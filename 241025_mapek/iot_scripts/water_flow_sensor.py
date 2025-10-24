"""
Water Flow Sensor Simulator
Continuously posts water flow data to the database via API
"""
import time
import random
import requests

SENSOR_ID = "water_flow_1"
API_URL = "http://localhost:3043/iot/water_flow"

print(f"Starting Water Flow Sensor: {SENSOR_ID}")
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
            "flowrate": round(random.uniform(15, 25), 2),  # Anomalous flowrate
            "total_flow": round(random.uniform(2000, 3000), 2), # Anomalous total flow
            "pressure": round(random.uniform(6, 10), 2),   # Anomalous pressure
            "pressure_voltage": round(random.uniform(3, 5), 2) # Anomalous pressure voltage
        }
        print(f"[Cycle {cycle}] ⚠️  ANOMALY: {data}")
    else:
        # Normal values
        data = {
            "node_id": SENSOR_ID,
            "flowrate": round(random.uniform(1, 10), 2),
            "total_flow": round(random.uniform(100, 1000), 2),
            "pressure": round(random.uniform(1, 5), 2),
            "pressure_voltage": round(random.uniform(0.5, 2.5), 2)
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
