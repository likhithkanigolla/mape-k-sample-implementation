import time
import random
import requests

SENSOR_ID = "water_quality_1"
API_URL = "http://localhost:3043/iot/water_quality"

while True:
    data = {
        "node_id": SENSOR_ID,
        "temperature": round(random.uniform(20, 30), 2),
        "tds_voltage": round(random.uniform(0.5, 2.5), 2),
        "uncompensated_tds": round(random.uniform(100, 500), 2),
        "compensated_tds": round(random.uniform(100, 500), 2)
    }
    try:
        requests.post(API_URL, json=data)
    except Exception as e:
        print(f"Error sending data: {e}")
    time.sleep(60)  # Send data every 10 seconds
