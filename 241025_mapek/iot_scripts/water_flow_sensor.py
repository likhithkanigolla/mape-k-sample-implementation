"""
Water Flow Sensor Simulator with Command Receiver
- Continuously posts water flow data to IoT Gateway
- Receives execution commands from MAPE-K via Gateway
- Applies fixes when commanded
"""
import time
import random
import requests
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

# Configuration
SENSOR_ID = "water_flow_1"
GATEWAY_URL = "http://localhost:3043/iot/water_flow"
COMMAND_PORT = 8003

# Sensor state
sensor_state = {
    "is_faulty": False,
    "fault_fixed": False,
    "last_command": None,
    "cycle": 0,
    "injected_scenario": None,
    "injected_cycles_left": 0,
    "scenario_step": 0,
    "fail_commands_left": 0,
}

PLAN_SUCCESS_RATES = {
    "RESTART_NODE_ENFORCE_REPORTING": 0.84,
    "SERVICE_HEALTH_CHECK_AND_FIX": 0.79,
    "DISABLE_SENSOR_AND_RESTART": 0.76,
    "RESET_SENSING_MODULE": 0.8,
    "REASSIGN_GATEWAY": 0.81,
    "ADJUST_CONNECTION_INTERVAL": 0.83,
    "ENABLE_LOW_POWER_MODE": 0.72,
    "ISOLATE_SENSOR": 0.74,
    "VERIFY_AND_REISSUE_COMMAND": 0.7,
    "RECALIBRATE_SENSOR_PARAMS": 0.78,
}

# FastAPI app for receiving commands
app = FastAPI(title=f"{SENSOR_ID} Command Receiver")

class CommandRequest(BaseModel):
    plan_code: str
    description: str


class ScenarioInjectRequest(BaseModel):
    scenario_code: str
    duration_cycles: int = 6
    intensity: float = 1.0

@app.post("/command")
async def receive_command(command: CommandRequest):
    """Receive execution command from MAPE-K via Gateway"""
    print(f"\n{'='*60}")
    print("COMMAND RECEIVED from MAPE-K Server")
    print(f"{'='*60}")
    print(f"Plan Code: {command.plan_code}")
    print(f"Description: {command.description}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if sensor_state["fail_commands_left"] > 0:
        sensor_state["fail_commands_left"] -= 1
        raise HTTPException(status_code=500, detail="Injected S10: command execution failed")

    success_rate = PLAN_SUCCESS_RATES.get(command.plan_code, 0.78)
    plan_worked = random.random() < success_rate

    sensor_state["last_command"] = command.plan_code
    if plan_worked:
        sensor_state["is_faulty"] = False
        sensor_state["fault_fixed"] = True
        sensor_state["injected_scenario"] = None
        sensor_state["injected_cycles_left"] = 0
        sensor_state["scenario_step"] = 0
        print(f"Fix worked (p={success_rate:.2f}) - returning to normal operation")
    else:
        sensor_state["is_faulty"] = True
        sensor_state["fault_fixed"] = False
        print(f"Fix command accepted but issue persists (p={success_rate:.2f})")

    print(f"{'='*60}\n")

    return {
        "status": "success" if plan_worked else "failed",
        "node_id": SENSOR_ID,
        "message": (
            f"Command '{command.plan_code}' executed and issue resolved"
            if plan_worked
            else f"Command '{command.plan_code}' executed but issue not resolved"
        ),
        "timestamp": datetime.now().isoformat(),
        "plan_worked": plan_worked,
    }


@app.post("/inject")
async def inject_scenario(req: ScenarioInjectRequest):
    code = req.scenario_code.upper().strip()
    if code not in {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11"}:
        raise HTTPException(status_code=400, detail=f"Unsupported scenario: {code}")

    sensor_state["injected_scenario"] = code
    sensor_state["injected_cycles_left"] = max(1, min(50, int(req.duration_cycles)))
    sensor_state["scenario_step"] = 0
    sensor_state["is_faulty"] = True
    sensor_state["fault_fixed"] = False
    if code == "S10":
        sensor_state["fail_commands_left"] = max(1, min(5, int(req.duration_cycles // 2) or 1))

    return {
        "status": "success",
        "node_id": SENSOR_ID,
        "scenario_code": code,
        "message": f"Scenario {code} injected"
    }

@app.get("/status")
async def get_status():
    """Get current sensor status"""
    return {
        "node_id": SENSOR_ID,
        "is_faulty": sensor_state["is_faulty"],
        "fault_fixed": sensor_state["fault_fixed"],
        "last_command": sensor_state["last_command"],
        "cycle": sensor_state["cycle"],
        "injected_scenario": sensor_state["injected_scenario"],
        "injected_cycles_left": sensor_state["injected_cycles_left"],
    }


def _scenario_payload(code, step):
    if code == "S1":
        return {
            "node_id": SENSOR_ID,
            "flowrate": round(4 + step * 2.1, 2),
            "total_flow": round(200 + step * 180, 2),
            "pressure": round(1.1 + step * 0.75, 2),
            "pressure_voltage": round(0.8 + step * 0.38, 2)
        }
    if code == "S2":
        return {
            "node_id": SENSOR_ID,
            "flowrate": -5.0,
            "total_flow": -100.0,
            "pressure": -2.0,
            "pressure_voltage": -1.0
        }
    if code == "S3":
        return {
            "node_id": SENSOR_ID,
            "flowrate": 0.0,
            "total_flow": 0.0,
            "pressure": 0.0,
            "pressure_voltage": 0.0
        }
    if code == "S9":
        return {
            "node_id": SENSOR_ID,
            "flowrate": 24.0,
            "total_flow": 3200.0,
            "pressure": 9.5,
            "pressure_voltage": 4.8
        }
    return {
        "node_id": SENSOR_ID,
        "flowrate": round(random.uniform(15, 25), 2),
        "total_flow": round(random.uniform(2000, 3000), 2),
        "pressure": round(random.uniform(6, 10), 2),
        "pressure_voltage": round(random.uniform(3, 5), 2)
    }

def run_fastapi_server():
    """Run FastAPI server in background thread"""
    uvicorn.run(app, host="0.0.0.0", port=COMMAND_PORT, log_level="warning")

def send_sensor_data():
    """Main sensor data sending loop"""
    print(f"Starting Water Flow Sensor: {SENSOR_ID}")
    print(f"Posting to: {GATEWAY_URL}")
    print(f"Command receiver running on: http://localhost:{COMMAND_PORT}")
    print("Press Ctrl+C to stop\n")
    
    while True:
        sensor_state["cycle"] += 1
        cycle = sensor_state["cycle"]

        injected_code = sensor_state.get("injected_scenario")
        if injected_code and sensor_state.get("injected_cycles_left", 0) > 0:
            sensor_state["scenario_step"] += 1
            sensor_state["injected_cycles_left"] -= 1

            if injected_code in {"S4", "S11"}:
                print(f"[Cycle {cycle}] {injected_code} injected: no data sent")
                time.sleep(60)
                if sensor_state["injected_cycles_left"] == 0:
                    sensor_state["injected_scenario"] = None
                continue

            if injected_code in {"S5", "S6"} and sensor_state["scenario_step"] % 2 == 0:
                print(f"[Cycle {cycle}] {injected_code} injected: transient disconnect")
                time.sleep(60)
                if sensor_state["injected_cycles_left"] == 0:
                    sensor_state["injected_scenario"] = None
                continue

            data = _scenario_payload(injected_code, sensor_state["scenario_step"])
            sensor_state["is_faulty"] = True
            sensor_state["fault_fixed"] = False
            print(f"[Cycle {cycle}] Injected {injected_code}: {data}")

            if sensor_state["injected_cycles_left"] == 0:
                sensor_state["injected_scenario"] = None
        else:
            sensor_state["injected_scenario"] = None
        
            # If fault was recently fixed, send normal data
            if sensor_state["fault_fixed"]:
                data = {
                    "node_id": SENSOR_ID,
                    "flowrate": round(random.uniform(1, 10), 2),
                    "total_flow": round(random.uniform(100, 1000), 2),
                    "pressure": round(random.uniform(1, 5), 2),
                    "pressure_voltage": round(random.uniform(0.5, 2.5), 2)
                }
                print(f"[Cycle {cycle}] FIXED - Normal operation restored: {data}")

                if cycle % 3 == 0:
                    sensor_state["fault_fixed"] = False

            # Inject anomaly with 30% probability
            elif random.random() < 0.4:
                sensor_state["is_faulty"] = True
                data = {
                    "node_id": SENSOR_ID,
                    "flowrate": round(random.uniform(15, 25), 2),
                    "total_flow": round(random.uniform(2000, 3000), 2),
                    "pressure": round(random.uniform(6, 10), 2),
                    "pressure_voltage": round(random.uniform(3, 5), 2)
                }
                print(f"[Cycle {cycle}] ANOMALY: {data}")
            else:
                sensor_state["is_faulty"] = False
                data = {
                    "node_id": SENSOR_ID,
                    "flowrate": round(random.uniform(1, 10), 2),
                    "total_flow": round(random.uniform(100, 1000), 2),
                    "pressure": round(random.uniform(1, 5), 2),
                    "pressure_voltage": round(random.uniform(0.5, 2.5), 2)
                }
                print(f"[Cycle {cycle}] Normal: {data}")
        
        try:
            response = requests.post(GATEWAY_URL, json=data, timeout=5)
            if response.status_code == 200:
                print("  Data posted successfully to Gateway\n")
            else:
                print(f"  Error: HTTP {response.status_code}\n")
        except Exception as e:
            print(f"  Error sending data: {e}\n")
        
        time.sleep(60)

if __name__ == "__main__":
    api_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    api_thread.start()
    time.sleep(2)
    
    try:
        send_sensor_data()
    except KeyboardInterrupt:
        print("\n\nShutting down sensor...")
