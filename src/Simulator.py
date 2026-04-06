""" File Overview
Simulates a network of IoT environmental sensors by publishing realistic
JSON payloads to the Mosquitto MQTT broker. Publishes readings for 4 zones
(zone-a through zone-d) and 4 metrics (AQI, temperature, humidity, noise)
every 2-3 seconds. Includes a --spike flag for triggering threshold-crossing
values during demos, a --zone flag to target a specific zone, and a --rate
flag to control publish frequency.

Using the --zone flag continuously publishes sensor data from that specific zone until you quit. 
For example, if you add --zone a, only zone a data will be published (with sensor_id, metricType,
value and timestap being randomly generated like usual).

The default rate is set to 2.5s. So every 2.5 seconds data is published. BUT that can be controlled
using the --rate flag. 

The --spike flag is used to input exactly which data you want to publish. For example, --spike zone-a aqi 400. 


"""


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

#FUNCTIONS

#takes a metric name (eg. aqi) and generates and random value within the range specified in RANGES dict
#called by generate_payload()
def generate_value(metric):
    low, high = RANGES[metric]
    return round(random.uniform(low, high), 2)

#generates a properly formatted dict with the 5 required fields. 
def generate_payload(zone, metric, sensor_id):
    return {
        "sensorId": sensor_id,
        "zone": zone,
        "metricType": metric,
        "value": generate_value(metric),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# takes a zone and metric to return a MQTT format string in correct format
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
    #note we dont care about which sensor the spike came from, we just want to test it


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

    parser.add_argument("--zone", type=str, help="Target a specific zone") #eg. "--zone a" 
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