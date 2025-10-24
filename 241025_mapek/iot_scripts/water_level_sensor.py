"""
Water Level Sensor Simulator
Continuously posts water level data to the database via API
"""
import time
import random
import requests

SENSOR_ID = "water_level_1"
API_URL = "http://localhost:3043/iot/water_level"

print(f"Starting Water Level Sensor: {SENSOR_ID}")
print(f"Posting to: {API_URL}")
print("Press Ctrl+C to stop\n")

cycle = 0

while True:
    cycle += 1
    
    # Inject anomaly with 30% probability
    if random.random() < 0.3:
        # Anomalous values
        data = {
            "node_id": SENSOR_ID,
            "water_level": round(random.uniform(-5, 0), 2),  # Anomalous water level
            "temperature": round(random.uniform(40, 60), 2)  # Anomalous temperature
        }
        print(f"[Cycle {cycle}] ⚠️  ANOMALY: {data}")
    else:
        # Normal values
        data = {
            "node_id": SENSOR_ID,
            "water_level": round(random.uniform(1, 10), 2),
            "temperature": round(random.uniform(20, 30), 2)
        }
        print(f"[Cycle {cycle}] ✓ Normal: {data}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        if response.status_code == 200:
            print(f"  → Data posted successfully\n")
        else:
            print(f"  → Error: HTTP {response.status_code}\n")
    except Exception as e:
        print(f"  → Error sending data: {e}\n")
    
    time.sleep(60)
