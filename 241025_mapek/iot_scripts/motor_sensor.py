"""
Motor Sensor Simulator
Continuously posts motor status data to the database via API
"""
import time
import random
import requests

SENSOR_ID = "motor_1"
API_URL = "http://localhost:3043/iot/motor"

print(f"Starting Motor Sensor: {SENSOR_ID}")
print(f"Posting to: {API_URL}")
print("Press Ctrl+C to stop\n")

cycle = 0
motor_state = False  # False = OFF, True = ON

while True:
    cycle += 1
    
    # Inject anomaly with 30% probability
    if random.random() < 0.3:
        # Anomalous values
        data = {
            "node_id": SENSOR_ID,
            "status": "ON" if motor_state else "OFF",
            "voltage": round(random.uniform(180, 210), 2),  # Anomalous voltage
            "current": round(random.uniform(15, 20), 2),    # Anomalous current
            "power": round(random.uniform(2100, 3000), 2),  # Anomalous power
            "energy": round(random.uniform(150, 200), 2),   # Anomalous energy
            "frequency": round(random.uniform(45, 48), 2),  # Anomalous frequency
            "power_factor": round(random.uniform(0.5, 0.7), 2) # Anomalous power factor
        }
        print(f"[Cycle {cycle}] ⚠️  ANOMALY: Motor={motor_state}, {data}")
    else:
        # Normal values
        data = {
            "node_id": SENSOR_ID,
            "status": "ON" if motor_state else "OFF",
            "voltage": round(random.uniform(220, 240), 2),
            "current": round(random.uniform(1, 10), 2),
            "power": round(random.uniform(100, 2000), 2),
            "energy": round(random.uniform(0, 100), 2),
            "frequency": round(random.uniform(49, 51), 2),
            "power_factor": round(random.uniform(0.8, 1.0), 2)
        }
        print(f"[Cycle {cycle}] ✓ Normal: Motor={motor_state}, {data}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        if response.status_code == 200:
            print(f"  → Data posted successfully\n")
        else:
            print(f"  → Error: HTTP {response.status_code}\n")
    except Exception as e:
        print(f"  → Error sending data: {e}\n")
    
    # Simulate motor control - randomly toggle state
    if random.random() > 0.8:
        motor_state = not motor_state
        print(f"  🔄 Motor state changed to: {'ON' if motor_state else 'OFF'}\n")
    
    time.sleep(60)
