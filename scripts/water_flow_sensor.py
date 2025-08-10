import time
import random
import requests

SENSOR_ID = "water_flow_1"
API_URL = "http://localhost:3043/iot/water_flow"

while True:
    # Inject anomaly with 30% probability
    if random.random() < 0.3:
        data = {
            "node_id": SENSOR_ID,
            "flowrate": round(random.uniform(15, 25), 2),  # Anomalous flowrate
            "total_flow": round(random.uniform(2000, 3000), 2), # Anomalous total flow
            "pressure": round(random.uniform(6, 10), 2),   # Anomalous pressure
            "pressure_voltage": round(random.uniform(3, 5), 2) # Anomalous pressure voltage
        }
    else:
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
