import time
import random
import requests

SENSOR_ID = "water_quality_1"
API_URL = "http://localhost:3043/iot/water_quality"

while True:
    # Inject anomaly with 30% probability
    if random.random() < 0.3:
        data = {
            "node_id": SENSOR_ID,
            "temperature": round(random.uniform(40, 60), 2),  # Anomalous temperature
            "tds_voltage": round(random.uniform(3, 5), 2),    # Anomalous tds voltage
            "uncompensated_tds": round(random.uniform(600, 1000), 2), # Anomalous uncompensated tds
            "compensated_tds": round(random.uniform(600, 1000), 2)    # Anomalous compensated tds
        }
    else:
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
    time.sleep(60)
