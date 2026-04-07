"""
MQTT Subscriber — FastAPI Background Task

Connects to the Mosquitto MQTT broker over TLS on startup and subscribes
to the wildcard topic scemas/sensors/#. For every incoming message, parses
the JSON payload and passes it to the validation pipeline in validation_service.py.
Runs continuously as a background asyncio task alongside the FastAPI HTTP server.

This file imports the function "process_message" from validation_service.py (which calls the functions
that contain all the validation logic)

Print statements have also been included for debugging purposes to ensure the MQTT subscriber has 
been successfully connected. 
"""


import asyncio
import json
import os
import ssl

import paho.mqtt.client as mqtt

from app.services.validation_service import process_message

# Read broker config from environment so Docker and local runs use the same code.
_HOST     = os.getenv("MQTT_BROKER_HOST",  "localhost")
_PORT     = int(os.getenv("MQTT_BROKER_PORT", "8883"))
_USERNAME = os.getenv("MQTT_USERNAME",     "admin")
_PASSWORD = os.getenv("MQTT_PASSWORD",     "admin123")
_CA_CERT  = os.getenv("MQTT_CA_CERT_PATH", "./mosquitto/config/certs/ca.crt")
# Cloud brokers (HiveMQ Cloud, etc.) use a public CA — set MQTT_CA_CERT_PATH=SYSTEM on Render.
# Local Docker Mosquitto: keep default file path; code uses tls_insecure_set for self-signed CN.
_USE_TLS = os.getenv("MQTT_USE_TLS", "true").strip().lower() in ("1", "true", "yes")

_TOPIC = "scemas/sensors/#"


def on_connect(client, userdata, flags, rc) -> None:
    """Called by paho once the TCP+TLS handshake and MQTT CONNACK are complete."""
    if rc == 0:
        print(f"✅ MQTT subscriber connected to {_HOST}:{_PORT}")
        # Subscribe after a confirmed connection so we never miss messages
        # that arrive before the subscribe ACK in edge-case reconnect scenarios.
        client.subscribe(_TOPIC)
        print(f"📡 Subscribed to topic: {_TOPIC}")
    else:
        # paho rc codes: 1=wrong protocol, 2=bad client id, 3=server unavailable,
        # 4=bad credentials, 5=not authorised.
        print(f"❌ MQTT connection failed (rc={rc}) — check broker credentials and TLS config")


def on_disconnect(client, userdata, rc) -> None:
    """Called whenever the connection drops, whether cleanly or unexpectedly."""
    if rc == 0:
        print("🔌 MQTT subscriber disconnected cleanly")
    else:
        # paho will attempt automatic reconnect when loop_start() is active.
        print(f"⚠️  MQTT subscriber lost connection (rc={rc}) — paho will retry")


def on_message(client, userdata, msg) -> None:
    """
    Called by paho's network thread for every incoming publish.

    Decodes the JSON payload and hands it to the validation pipeline.
    Errors are caught here so a single bad message never kills the subscriber.
    """
    try:
        payload = json.loads(msg.payload.decode())
        zone   = payload.get("zone", "unknown")
        metric = payload.get("metricType", "unknown")
        value  = payload.get("value", "?")
        print(f"📨 Message received — topic: {msg.topic} | zone: {zone} | {metric}: {value}")

        # process_message is synchronous (psycopg) — no asyncio.run() needed
        process_message(payload)
        print(f"✅ Validation complete — zone: {zone} | {metric}: {value}")

    except json.JSONDecodeError as exc:
        print(f"❌ Non-JSON message on {msg.topic}: {exc}")
    except Exception as exc:
        print(f"❌ Error processing message on {msg.topic}: {exc}")


async def run_mqtt_subscriber() -> None:
    """
    Async wrapper that keeps the paho client alive for the duration of the
    FastAPI lifespan.

    paho runs its own network thread via loop_start(), so this coroutine just
    sleeps in 1-second intervals.  When the lifespan cancels this task, the
    finally block shuts down the paho thread cleanly before the process exits.
    """
    client = mqtt.Client()
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    client.username_pw_set(_USERNAME, _PASSWORD)

    print(f"🔌 Connecting to MQTT broker at {_HOST}:{_PORT}")
    if _USE_TLS:
        print(
            "🔒 TLS on — CA: system trust store"
            if _CA_CERT.strip().upper() == "SYSTEM"
            else f"🔒 TLS on — CA file: {_CA_CERT}"
        )
    else:
        print("🔓 TLS off (plain MQTT)")

    try:
        if _USE_TLS:
            if _CA_CERT.strip().upper() == "SYSTEM":
                client.tls_set_context(ssl.create_default_context())
            else:
                client.tls_set(ca_certs=_CA_CERT)
                # Self-signed local Mosquitto: CN often does not match hostname.
                client.tls_insecure_set(True)
        client.connect(_HOST, _PORT)
        # loop_start() spins up paho's network thread so connect/subscribe/receive
        # all happen in the background without blocking the asyncio event loop.
        client.loop_start()
    except Exception as exc:
        print(f"❌ MQTT subscriber failed to start: {exc}")
        print("   Sensor readings will not be validated until the broker is reachable.")
        return

    try:
        # Keep this coroutine alive so the paho thread stays running.
        while True:
            await asyncio.sleep(1)
    finally:
        # Graceful shutdown: flush any in-flight messages and close the TCP socket.
        client.loop_stop()
        client.disconnect()
        print("🔌 MQTT subscriber shut down")
