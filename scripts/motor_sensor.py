import time
import random
import requests

SENSOR_ID = "motor_1"
API_URL = "http://localhost:3043/iot/motor"

motor_state = False  # False = OFF, True = ON

while True:
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
    try:
        requests.post(API_URL, json=data)
    except Exception as e:
        print(f"Error sending data: {e}")
    # Simulate motor control
    if random.random() > 0.8:
        motor_state = not motor_state
    time.sleep(60)
