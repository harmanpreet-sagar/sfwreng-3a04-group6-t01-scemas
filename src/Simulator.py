import time
import random
import argparse
import json
import paho.mqtt.client as mqtt
import os
from datetime import datetime, timezone

# MQTT client setup
MQTT_HOST = "localhost"
MQTT_PORT = 8883
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "admin123"
CA_CERT_PATH = "./mosquitto/config/certs/ca.crt"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to Mosquitto successfully")
    else:
        print(f"❌ Connection failed with code {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(ca_certs=CA_CERT_PATH)
client.tls_insecure_set(True)  # needed for self-signed certs
client.connect(MQTT_HOST, MQTT_PORT)
client.loop_start()

ZONES = ["zone-a", "zone-b", "zone-c", "zone-d"]
METRICS = ["aqi", "temperature", "humidity", "noise"]
SENSORS = ["sensor-001", "sensor-002", "sensor-003"]

RANGES = {
    "aqi": (0, 500),
    "temperature": (-30, 50),
    "humidity": (0, 100),
    "noise": (0, 140),
}

#functions:
def generate_value(metric):
    low, high = RANGES[metric]
    return round(random.uniform(low, high), 2)


def generate_payload(zone, metric, sensor_id):
    return {
        "sensorId": sensor_id,
        "zone": zone,
        "metricType": metric,
        "value": generate_value(metric),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def build_topic(zone, metric):
    return f"scemas/sensors/{zone}/{metric}"


#spikes. literally just command line arguments. Outputs data only once. 
def generate_spike(zone, metric, value):
    payload = {
        "sensorId": "sensor-spike",
        "zone": zone,
        "metricType": metric,
        "value": value,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("\n🚨 SPIKE EVENT 🚨")
    topic = f"scemas/sensors/{zone}/{metric}"
    client.publish(topic, json.dumps(payload))
    print(json.dumps(payload, indent=2))
    #note for now i think we dont care about which sensor the spike came from, we just want to test it


# -----------------------------
# Main loop
# -----------------------------
def run_simulator(selected_zone=None, rate=2.5):
    while True:
        zone = selected_zone if selected_zone else random.choice(ZONES)
        metric = random.choice(METRICS)
        sensor = random.choice(SENSORS)

        payload = generate_payload(zone, metric, sensor)

        if random.random() < 0.1:
            payload["value"] = 600

        topic = f"scemas/sensors/{zone}/{metric}"
        client.publish(topic, json.dumps(payload))

        print(f"\n📡 Publishing")
        print(json.dumps(payload, indent=2))

        time.sleep(rate)


# -----------------------------
# CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="SCEMAS Sensor Simulator")

    parser.add_argument("--zone", type=str, help="Target a specific zone")
    parser.add_argument("--rate", type=float, default=2.5, help="Publish rate in seconds")

    parser.add_argument(
        "--spike",
        nargs=3,
        metavar=("ZONE", "METRIC", "VALUE"),
        help="Trigger a spike event (e.g. --spike zone-a aqi 400)"
    )

    args = parser.parse_args()

    # Handle spike mode
    if args.spike:
        zone, metric, value = args.spike
        generate_spike(zone, metric, float(value))
        return

    # Run normal simulator
    run_simulator(selected_zone=args.zone, rate=args.rate)


if __name__ == "__main__":
    main()