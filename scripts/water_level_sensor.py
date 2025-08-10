import time
import random
import requests

SENSOR_ID = "water_level_1"
API_URL = "http://localhost:3043/iot/water_level"

while True:
    # Inject anomaly with 30% probability
    if random.random() < 0.3:
        data = {
            "node_id": SENSOR_ID,
            "water_level": round(random.uniform(-5, 0), 2),  # Anomalous water level
            "temperature": round(random.uniform(40, 60), 2)  # Anomalous temperature
        }
    else:
        data = {
            "node_id": SENSOR_ID,
            "water_level": round(random.uniform(1, 10), 2),
            "temperature": round(random.uniform(20, 30), 2)
        }
    try:
        requests.post(API_URL, json=data)
    except Exception as e:
        print(f"Error sending data: {e}")
    time.sleep(60)
