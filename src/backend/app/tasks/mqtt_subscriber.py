import asyncio
import json
import os
import paho.mqtt.client as mqtt

from app.services.validation_service import process_message

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", 8883))
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "admin123"
CA_CERT_PATH = os.getenv("MQTT_CA_CERT_PATH", "./mosquitto/config/certs/ca.crt")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        asyncio.run(process_message(payload))
    except Exception as e:
        print(f"❌ Error processing message: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT subscriber connected")
        client.subscribe("scemas/sensors/#")
    else:
        print(f"❌ MQTT subscriber connection failed: {rc}")

async def run_mqtt_subscriber():
    try:
        print(f"🔌 Connecting to MQTT at {MQTT_HOST}:{MQTT_PORT}")
        print(f"🔌 Using CA cert: {CA_CERT_PATH}")
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(ca_certs=CA_CERT_PATH)
        client.tls_insecure_set(True)
        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_start()
    except Exception as e:
        print(f"❌ MQTT subscriber failed to start: {e}")
        return

    # Keep running forever
    while True:
        await asyncio.sleep(1)