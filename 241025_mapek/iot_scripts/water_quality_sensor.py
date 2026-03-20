"""
Water Quality Sensor Simulator with Command Receiver
- Continuously posts water quality data to IoT Gateway
- Receives execution commands from MAPE-K via Gateway
- Applies fixes when commanded
"""
import time
import random
import requests
import threading
import uvicorn
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

# Configuration
SENSOR_ID = "water_quality_1"
GATEWAY_URL = "http://localhost:3043/iot/water_quality"
COMMAND_PORT = 8001  # Port to receive commands

# Setup individual sensor logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "water_quality.log"),
        logging.StreamHandler()
    ]
)
sensor_logger = logging.getLogger(__name__)

# Sensor state
sensor_state = {
    "is_faulty": False,
    "fault_fixed": False,
    "last_command": None,
    "cycle": 0,
    "fix_attempts": {},  # Track fix attempts per plan
    "injected_scenario": None,
    "injected_cycles_left": 0,
    "scenario_step": 0,
    "fail_commands_left": 0,
}

# Plan effectiveness simulation
# Some plans work better than others - simulates real-world scenarios
PLAN_SUCCESS_RATES = {
    "EMERGENCY_SHUTDOWN": 0.5,      # 50% success rate
    "RECALIBRATE_SENSOR": 0.8,      # 80% success rate - works best!
    "RESTART_DEVICE": 0.6,          # 60% success rate
    "NO_ACTION": 1.0,               # Always "works"
    "CHECK_POWER_SUPPLY": 0.7,      # 70% success rate
    "ADJUST_PARAMETERS": 0.65       # 65% success rate
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
    """
    Receive execution command from MAPE-K via Gateway
    Simulates realistic plan effectiveness - sometimes plans fail!
    """
    sensor_logger.info("="*60)
    sensor_logger.info("COMMAND RECEIVED from MAPE-K Server")
    sensor_logger.info("="*60)
    sensor_logger.info(f"Plan Code: {command.plan_code}")
    sensor_logger.info(f"Description: {command.description}")

    if sensor_state["fail_commands_left"] > 0:
        sensor_state["fail_commands_left"] -= 1
        sensor_logger.warning("Injected S10 behavior: rejecting command execution")
        raise HTTPException(status_code=500, detail="Injected S10: command execution failed")
    
    # Get success rate for this plan (default 70% if not defined)
    success_rate = PLAN_SUCCESS_RATES.get(command.plan_code, 0.7)
    
    # Randomly determine if this plan will work based on its success rate
    plan_will_work = random.random() < success_rate
    
    if plan_will_work:
        # Plan worked! Fix the sensor
        sensor_state["is_faulty"] = False
        sensor_state["fault_fixed"] = True
        sensor_state["last_command"] = command.plan_code
        sensor_state["injected_scenario"] = None
        sensor_state["injected_cycles_left"] = 0
        sensor_state["scenario_step"] = 0
        sensor_state["fix_attempts"][command.plan_code] = sensor_state["fix_attempts"].get(command.plan_code, 0) + 1
        
        sensor_logger.info(f"✅ SUCCESS: Plan '{command.plan_code}' WORKED! Sensor fixed.")
        sensor_logger.info(f"   Success rate: {success_rate*100}%")
        sensor_logger.info("   Sensor calibrated/fixed - returning to normal operation")
        
        status = "success"
        message = f"Command '{command.plan_code}' executed successfully - Sensor fixed!"
    else:
        # Plan failed! Sensor still faulty
        sensor_state["is_faulty"] = True
        sensor_state["fault_fixed"] = False
        sensor_state["last_command"] = command.plan_code
        
        sensor_logger.warning(f"❌ FAILED: Plan '{command.plan_code}' DID NOT WORK!")
        sensor_logger.warning(f"   Success rate: {success_rate*100}%")
        sensor_logger.warning("   Sensor still faulty - need alternative plan")
        
        status = "failed"
        message = f"Command '{command.plan_code}' executed but did not resolve the issue"
    
    sensor_logger.info("="*60)
    
    return {
        "status": status,
        "node_id": SENSOR_ID,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "plan_worked": plan_will_work
    }


@app.post("/inject")
async def inject_scenario(req: ScenarioInjectRequest):
    """Inject scenario behavior into this sensor for N cycles."""
    code = req.scenario_code.upper().strip()
    if code not in {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11"}:
        raise HTTPException(status_code=400, detail=f"Unsupported scenario: {code}")

    sensor_state["injected_scenario"] = code
    sensor_state["injected_cycles_left"] = max(1, min(50, int(req.duration_cycles)))
    sensor_state["scenario_step"] = 0
    sensor_state["fault_fixed"] = False
    sensor_state["is_faulty"] = True
    if code == "S10":
        sensor_state["fail_commands_left"] = max(1, min(5, int(req.duration_cycles // 2) or 1))

    sensor_logger.warning(
        f"Injected {code} for {sensor_state['injected_cycles_left']} cycles (intensity={req.intensity})"
    )

    return {
        "status": "success",
        "node_id": SENSOR_ID,
        "scenario_code": code,
        "message": f"Scenario {code} injected",
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
    """Build injected data for a scenario code."""
    if code == "S1":
        return {
            "node_id": SENSOR_ID,
            "temperature": round(24 + step * 3.2, 2),
            "tds_voltage": round(1.2 + step * 0.42, 2),
            "uncompensated_tds": round(220 + step * 90, 2),
            "compensated_tds": round(210 + step * 95, 2),
        }
    if code == "S2":
        return {
            "node_id": SENSOR_ID,
            "temperature": 25.0,
            "tds_voltage": -3.0,
            "uncompensated_tds": -120.0,
            "compensated_tds": -100.0,
        }
    if code == "S3":
        return {
            "node_id": SENSOR_ID,
            "temperature": 0.0,
            "tds_voltage": 0.0,
            "uncompensated_tds": 0.0,
            "compensated_tds": 0.0,
        }
    if code == "S9":
        return {
            "node_id": SENSOR_ID,
            "temperature": round(65 + step * 1.5, 2),
            "tds_voltage": round(4.8, 2),
            "uncompensated_tds": round(980, 2),
            "compensated_tds": round(1020, 2),
        }

    # Default severe anomaly payload for remaining codes.
    return {
        "node_id": SENSOR_ID,
        "temperature": round(random.uniform(42, 60), 2),
        "tds_voltage": round(random.uniform(3.2, 5.2), 2),
        "uncompensated_tds": round(random.uniform(700, 1050), 2),
        "compensated_tds": round(random.uniform(700, 1050), 2),
    }

def run_fastapi_server():
    """Run FastAPI server in background thread"""
    uvicorn.run(app, host="0.0.0.0", port=COMMAND_PORT, log_level="warning")

def send_sensor_data():
    """Main sensor data sending loop"""
    sensor_logger.info(f"Starting Water Quality Sensor: {SENSOR_ID}")
    sensor_logger.info(f"Posting to: {GATEWAY_URL}")
    sensor_logger.info(f"Command receiver running on: http://localhost:{COMMAND_PORT}")
    sensor_logger.info("Press Ctrl+C to stop\n")
    
    while True:
        sensor_state["cycle"] += 1
        cycle = sensor_state["cycle"]

        injected_code = sensor_state.get("injected_scenario")
        if injected_code and sensor_state.get("injected_cycles_left", 0) > 0:
            sensor_state["scenario_step"] += 1
            sensor_state["injected_cycles_left"] -= 1

            # Connectivity/service scenarios: deliberately skip publish cycles.
            if injected_code in {"S4", "S11"}:
                sensor_logger.warning(
                    f"[Cycle {cycle}] {injected_code} injected: simulating no data from node "
                    f"({sensor_state['injected_cycles_left']} cycles left)"
                )
                time.sleep(60)
                if sensor_state["injected_cycles_left"] == 0:
                    sensor_state["injected_scenario"] = None
                continue

            # Unstable/reconnect scenarios: alternate between send and drop.
            if injected_code in {"S5", "S6"} and (sensor_state["scenario_step"] % 2 == 0):
                sensor_logger.warning(
                    f"[Cycle {cycle}] {injected_code} injected: transient disconnect/drop cycle"
                )
                time.sleep(60)
                if sensor_state["injected_cycles_left"] == 0:
                    sensor_state["injected_scenario"] = None
                continue

            data = _scenario_payload(injected_code, sensor_state["scenario_step"])
            sensor_state["is_faulty"] = True
            sensor_state["fault_fixed"] = False
            sensor_logger.warning(
                f"[Cycle {cycle}] Injected {injected_code}: forced anomaly {data} "
                f"({sensor_state['injected_cycles_left']} cycles left)"
            )

            if sensor_state["injected_cycles_left"] == 0:
                sensor_state["injected_scenario"] = None
        else:
            sensor_state["injected_scenario"] = None
        
            # If sensor is still faulty (plan didn't work), continue sending anomaly data
            if sensor_state["is_faulty"]:
                data = {
                    "node_id": SENSOR_ID,
                    "temperature": round(random.uniform(40, 60), 2),
                    "tds_voltage": round(random.uniform(3, 5), 2),
                    "uncompensated_tds": round(random.uniform(600, 1000), 2),
                    "compensated_tds": round(random.uniform(600, 1000), 2)
                }
                sensor_logger.warning(f"[Cycle {cycle}] STILL FAULTY - Last command '{sensor_state['last_command']}' did not fix issue: {data}")

            # If fault was recently fixed, send normal data for a few cycles
            elif sensor_state["fault_fixed"]:
                data = {
                    "node_id": SENSOR_ID,
                    "temperature": round(random.uniform(20, 30), 2),
                    "tds_voltage": round(random.uniform(0.5, 2.5), 2),
                    "uncompensated_tds": round(random.uniform(100, 500), 2),
                    "compensated_tds": round(random.uniform(100, 500), 2)
                }
                sensor_logger.info(f"[Cycle {cycle}] FIXED - Normal operation restored by '{sensor_state['last_command']}': {data}")

                # After 3 cycles, allow new anomalies
                if cycle % 3 == 0:
                    sensor_state["fault_fixed"] = False

            # Inject new anomaly with 30% probability (only if not faulty or recently fixed)
            elif random.random() < 0.4:
                sensor_state["is_faulty"] = True
                data = {
                    "node_id": SENSOR_ID,
                    "temperature": round(random.uniform(40, 60), 2),
                    "tds_voltage": round(random.uniform(3, 5), 2),
                    "uncompensated_tds": round(random.uniform(600, 1000), 2),
                    "compensated_tds": round(random.uniform(600, 1000), 2)
                }
                sensor_logger.warning(f"[Cycle {cycle}] NEW ANOMALY DETECTED: {data}")
            else:
                sensor_state["is_faulty"] = False
                data = {
                    "node_id": SENSOR_ID,
                    "temperature": round(random.uniform(20, 30), 2),
                    "tds_voltage": round(random.uniform(0.5, 2.5), 2),
                    "uncompensated_tds": round(random.uniform(100, 500), 2),
                    "compensated_tds": round(random.uniform(100, 500), 2)
                }
                sensor_logger.info(f"[Cycle {cycle}] Normal: {data}")
        
        try:
            response = requests.post(GATEWAY_URL, json=data, timeout=5)
            if response.status_code == 200:
                sensor_logger.info("  Data posted successfully to Gateway")
            else:
                sensor_logger.error(f"  Error: HTTP {response.status_code}")
        except Exception as e:
            sensor_logger.error(f"  Error sending data: {e}")
        
        time.sleep(60)

if __name__ == "__main__":
    # Start FastAPI server in background thread
    api_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    api_thread.start()
    
    # Give the server a moment to start
    time.sleep(2)
    
    # Run main sensor loop
    try:
        send_sensor_data()
    except KeyboardInterrupt:
        sensor_logger.info("\n\nShutting down sensor...")
