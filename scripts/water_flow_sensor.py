import time
import random
import requests

SENSOR_ID = "water_flow_1"
API_URL = "http://localhost:3043/iot/water_flow"

while True:
    data = {
        "node_id": SENSOR_ID,
        "flowrate": round(random.uniform(1, 10), 2),
        "total_flow": round(random.uniform(100, 1000), 2),
        "pressure": round(random.uniform(1, 5), 2),
        "pressure_voltage": round(random.uniform(0.5, 2.5), 2)
    }
    try:
        requests.post(API_URL, json=data)
    except Exception as e:
        print(f"Error sending data: {e}")
    time.sleep(60)
