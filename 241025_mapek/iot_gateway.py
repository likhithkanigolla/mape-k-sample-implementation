"""
IoT Gateway - Central FastAPI Server
- Receives sensor data from all IoT devices
- Stores data in PostgreSQL database
- Provides endpoints for MAPE-K Monitor to fetch data
- Provides endpoints for MAPE-K Execute to send commands to devices
- Routes commands to appropriate IoT devices
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime
import requests
from contextlib import contextmanager
from pathlib import Path

app = FastAPI(title="IoT Gateway Server", version="1.0.0")
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
# Note: Must match the database name in plain_mapek/knowledge.py
DB_CONFIG = {
    "host": "localhost",
    "database": "mapek_dt",  # Using same database as MAPE-K
    "user": "postgres",
    "password": "postgres"
}

# Device registry - maps node_id to their command endpoint
DEVICE_REGISTRY = {
    "water_quality_1": "http://localhost:8001/command",
    "water_level_1": "http://localhost:8002/command",
    "water_flow_1": "http://localhost:8003/command",
    "motor_1": "http://localhost:8004/command"
}

SCENARIO_CATALOG = {
    "S1": {"title": "Sensor drift over time", "default_node": "water_quality_1"},
    "S2": {"title": "Invalid sensor values", "default_node": "water_quality_1"},
    "S3": {"title": "Constant zero sensor values", "default_node": "water_quality_1"},
    "S4": {"title": "No data from node", "default_node": "water_level_1"},
    "S5": {"title": "Unstable network connectivity", "default_node": "water_flow_1"},
    "S6": {"title": "Repeated reconnects", "default_node": "water_flow_1"},
    "S7": {"title": "Node resource/memory pressure", "default_node": "motor_1"},
    "S8": {"title": "Battery/energy pressure", "default_node": "motor_1"},
    "S9": {"title": "Sensor pattern deviation", "default_node": "water_quality_1"},
    "S10": {"title": "Actuation not executed correctly", "default_node": "motor_1"},
    "S11": {"title": "Service failure / heartbeat loss", "default_node": "water_level_1"},
}

# Pydantic models for data validation
class WaterQualityData(BaseModel):
    node_id: str
    temperature: float
    tds_voltage: float
    uncompensated_tds: float
    compensated_tds: float

class WaterLevelData(BaseModel):
    node_id: str
    water_level: float
    temperature: float

class WaterFlowData(BaseModel):
    node_id: str
    flowrate: float
    total_flow: float
    pressure: float
    pressure_voltage: float

class MotorData(BaseModel):
    node_id: str
    status: str
    voltage: float
    current: float
    power: float
    energy: float
    frequency: float
    power_factor: float

class ExecuteCommand(BaseModel):
    node_id: str
    plan_code: str
    description: str
    parameter: Optional[str] = None
    escalation_level: Optional[int] = None
    scenario_code: Optional[str] = None
    adaptation_goal: Optional[str] = None
    scenario_details: Optional[Dict] = None

class CommandResponse(BaseModel):
    status: str
    message: str
    node_id: str
    timestamp: str


class ScenarioInjectRequest(BaseModel):
    scenario_code: str
    node_id: Optional[str] = None
    duration_cycles: int = 6
    intensity: float = 1.0


class DatabaseResetRequest(BaseModel):
    confirm_text: str

# Database connection manager
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ============================================================================
# DATA INGESTION ENDPOINTS - IoT Devices POST data here
# ============================================================================

@app.post("/iot/water_quality")
async def receive_water_quality(data: WaterQualityData):
    """Receive and store water quality sensor data"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO water_quality 
                (node_id, temperature, tds_voltage, uncompensated_tds, compensated_tds, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (data.node_id, data.temperature, data.tds_voltage, 
                  data.uncompensated_tds, data.compensated_tds))
            cur.close()
        
        print(f"✓ Stored water_quality data from {data.node_id}")
        return {"status": "success", "message": "Data stored successfully"}
    
    except Exception as e:
        print(f"✗ Error storing water_quality data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/water_level")
async def receive_water_level(data: WaterLevelData):
    """Receive and store water level sensor data"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO water_level 
                (node_id, water_level, temperature, timestamp)
                VALUES (%s, %s, %s, NOW())
            """, (data.node_id, data.water_level, data.temperature))
            cur.close()
        
        print(f"✓ Stored water_level data from {data.node_id}")
        return {"status": "success", "message": "Data stored successfully"}
    
    except Exception as e:
        print(f"✗ Error storing water_level data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/water_flow")
async def receive_water_flow(data: WaterFlowData):
    """Receive and store water flow sensor data"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO water_flow 
                (node_id, flowrate, total_flow, pressure, pressure_voltage, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (data.node_id, data.flowrate, data.total_flow, 
                  data.pressure, data.pressure_voltage))
            cur.close()
        
        print(f"✓ Stored water_flow data from {data.node_id}")
        return {"status": "success", "message": "Data stored successfully"}
    
    except Exception as e:
        print(f"✗ Error storing water_flow data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/motor")
async def receive_motor(data: MotorData):
    """Receive and store motor sensor data"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO motor 
                (node_id, status, voltage, current, power, energy, frequency, power_factor, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (data.node_id, data.status, data.voltage, data.current, 
                  data.power, data.energy, data.frequency, data.power_factor))
            cur.close()
        
        print(f"✓ Stored motor data from {data.node_id}")
        return {"status": "success", "message": "Data stored successfully"}
    
    except Exception as e:
        print(f"✗ Error storing motor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DATA RETRIEVAL ENDPOINTS - MAPE-K Monitor fetches data from here
# ============================================================================

@app.get("/monitor/water_quality/latest")
async def get_latest_water_quality(limit: int = 10):
    """Get latest water quality readings for MAPE-K Monitor"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM water_quality 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
        
        return {"data": rows, "count": len(rows)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/water_level/latest")
async def get_latest_water_level(limit: int = 10):
    """Get latest water level readings for MAPE-K Monitor"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM water_level 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
        
        return {"data": rows, "count": len(rows)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/water_flow/latest")
async def get_latest_water_flow(limit: int = 10):
    """Get latest water flow readings for MAPE-K Monitor"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM water_flow 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
        
        return {"data": rows, "count": len(rows)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/motor/latest")
async def get_latest_motor(limit: int = 10):
    """Get latest motor readings for MAPE-K Monitor"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM motor 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
        
        return {"data": rows, "count": len(rows)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _load_latest_rows(cur, query, params=()):
    """Small helper to execute a query and return row dicts."""
    cur.execute(query, params)
    return cur.fetchall()


@app.get("/dashboard", response_class=HTMLResponse)
async def mapek_dashboard_page():
    """Serve a single-page dashboard for live MAPE-K visibility."""
    dashboard_file = BASE_DIR / "dashboard" / "index.html"
    if not dashboard_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard page not found")
    return dashboard_file.read_text(encoding="utf-8")


@app.get("/dashboard/data")
async def mapek_dashboard_data(limit: int = 20):
    """Return aggregated data for Monitor/Analyze/Plan/Execute dashboard panels."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            monitor_rows = _load_latest_rows(
                cur,
                """
                SELECT * FROM (
                    SELECT node_id, timestamp, 'water_quality' AS sensor_type,
                           temperature, tds_voltage, compensated_tds,
                           NULL::FLOAT AS water_level, NULL::FLOAT AS flowrate,
                           NULL::FLOAT AS pressure, NULL::FLOAT AS voltage,
                           NULL::FLOAT AS current, NULL::FLOAT AS energy,
                           NULL::VARCHAR AS status
                    FROM water_quality
                    ORDER BY timestamp DESC
                    LIMIT 50
                ) wq
                UNION ALL
                SELECT * FROM (
                    SELECT node_id, timestamp, 'water_level' AS sensor_type,
                           temperature, NULL::FLOAT AS tds_voltage, NULL::FLOAT AS compensated_tds,
                           water_level, NULL::FLOAT AS flowrate,
                           NULL::FLOAT AS pressure, NULL::FLOAT AS voltage,
                           NULL::FLOAT AS current, NULL::FLOAT AS energy,
                           NULL::VARCHAR AS status
                    FROM water_level
                    ORDER BY timestamp DESC
                    LIMIT 50
                ) wl
                UNION ALL
                SELECT * FROM (
                    SELECT node_id, timestamp, 'water_flow' AS sensor_type,
                           NULL::FLOAT AS temperature, NULL::FLOAT AS tds_voltage, NULL::FLOAT AS compensated_tds,
                           NULL::FLOAT AS water_level, flowrate,
                           pressure, NULL::FLOAT AS voltage,
                           NULL::FLOAT AS current, NULL::FLOAT AS energy,
                           NULL::VARCHAR AS status
                    FROM water_flow
                    ORDER BY timestamp DESC
                    LIMIT 50
                ) wf
                UNION ALL
                SELECT * FROM (
                    SELECT node_id, timestamp, 'motor' AS sensor_type,
                           NULL::FLOAT AS temperature, NULL::FLOAT AS tds_voltage, NULL::FLOAT AS compensated_tds,
                           NULL::FLOAT AS water_level, NULL::FLOAT AS flowrate,
                           NULL::FLOAT AS pressure, voltage,
                           current, energy,
                           status
                    FROM motor
                    ORDER BY timestamp DESC
                    LIMIT 50
                ) m
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            analyze_rows = _load_latest_rows(
                cur,
                """
                SELECT id, node_id, state, result, timestamp
                FROM "analyze"
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            plan_rows = _load_latest_rows(
                cur,
                """
                SELECT ps.id, ps.node_id, ps.plan_code, ps.timestamp, p.description
                FROM plan_selection ps
                LEFT JOIN plans p ON p.plan_code = ps.plan_code
                ORDER BY ps.timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            execute_rows = _load_latest_rows(
                cur,
                """
                SELECT id, node_id, plan_code, status, message, timestamp
                FROM execution
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            gateway_rows = _load_latest_rows(
                cur,
                """
                SELECT id, node_id, plan_code, description, status, error_message, timestamp
                FROM execution_log
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )

            counts = _load_latest_rows(
                cur,
                """
                SELECT
                    (SELECT COUNT(*) FROM water_quality) AS water_quality_count,
                    (SELECT COUNT(*) FROM water_level) AS water_level_count,
                    (SELECT COUNT(*) FROM water_flow) AS water_flow_count,
                    (SELECT COUNT(*) FROM motor) AS motor_count,
                    (SELECT COUNT(*) FROM "analyze") AS analyze_count,
                    (SELECT COUNT(*) FROM plan_selection) AS plan_count,
                    (SELECT COUNT(*) FROM execution) AS execute_count,
                    (SELECT COUNT(*) FROM execution_log) AS gateway_execute_count
                """,
            )

            cur.close()

        return {
            "generated_at": datetime.now().isoformat(),
            "summary": counts[0] if counts else {},
            "monitor": monitor_rows,
            "analyze": analyze_rows,
            "plan": plan_rows,
            "execute": execute_rows,
            "gateway_execute": gateway_rows,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data error: {e}")


@app.post("/admin/database/reset")
async def reset_database(payload: DatabaseResetRequest):
    """Dangerous operation: clear and re-seed the full database."""
    if payload.confirm_text != "RESET_DATABASE":
        raise HTTPException(status_code=400, detail="Invalid confirmation token")

    setup_files = [
        BASE_DIR / "setup_complete_database.sql",
        BASE_DIR / "setup_knowledge_base.sql",
        BASE_DIR / "setup_iot_gateway_views.sql",
    ]
    missing = [str(f.name) for f in setup_files if not f.exists()]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing setup files: {', '.join(missing)}",
        )

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                """
            )
            table_names = [row[0] for row in cur.fetchall()]

            if table_names:
                table_identifiers = [sql.Identifier("public", name) for name in table_names]
                truncate_stmt = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                    sql.SQL(", ").join(table_identifiers)
                )
                cur.execute(truncate_stmt)

            for setup_file in setup_files:
                cur.execute(setup_file.read_text(encoding="utf-8"))

            cur.close()

        return {
            "status": "success",
            "message": "Database reset complete and defaults restored",
            "tables_cleared": len(table_names),
            "seed_files": [f.name for f in setup_files],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database reset failed: {e}")


@app.get("/scenario/catalog")
async def get_scenario_catalog():
    """Return supported scenario metadata for dashboard controls."""
    return {
        "scenarios": [
            {
                "code": code,
                "title": data["title"],
                "default_node": data["default_node"],
            }
            for code, data in SCENARIO_CATALOG.items()
        ]
    }


@app.post("/scenario/inject")
async def inject_scenario(payload: ScenarioInjectRequest):
    """Inject scenario S1-S11 into a target device simulator."""
    scenario_code = payload.scenario_code.upper().strip()
    if scenario_code not in SCENARIO_CATALOG:
        raise HTTPException(status_code=400, detail=f"Unsupported scenario code: {scenario_code}")

    target_node = payload.node_id or SCENARIO_CATALOG[scenario_code]["default_node"]
    if target_node not in DEVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown node_id: {target_node}")

    inject_url = DEVICE_REGISTRY[target_node].replace("/command", "/inject")
    request_body = {
        "scenario_code": scenario_code,
        "duration_cycles": max(1, min(50, payload.duration_cycles)),
        "intensity": max(0.2, min(3.0, payload.intensity)),
    }

    try:
        response = requests.post(inject_url, json=request_body, timeout=10)
        if response.status_code != 200:
            # Improve troubleshooting signal for the common case where a stale sensor
            # process is running without the newer /inject endpoint.
            if response.status_code == 404:
                status_url = DEVICE_REGISTRY[target_node].replace("/command", "/status")
                status_probe = "unreachable"
                try:
                    probe_resp = requests.get(status_url, timeout=5)
                    status_probe = f"HTTP {probe_resp.status_code}"
                except Exception:
                    status_probe = "unreachable"

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Device {target_node} is reachable ({status_probe}) but does not expose {inject_url}. "
                        "Restart sensor scripts so they load the latest /inject endpoint."
                    ),
                )

            raise HTTPException(
                status_code=response.status_code,
                detail=(
                    f"Device injection endpoint failed for {target_node} with HTTP {response.status_code} "
                    f"at {inject_url}"
                ),
            )

        device_result = response.json()

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO execution_log
                (node_id, plan_code, description, status, timestamp)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (
                    target_node,
                    f"INJECT_{scenario_code}",
                    f"Injected {scenario_code}: {SCENARIO_CATALOG[scenario_code]['title']}",
                    "success",
                ),
            )
            cur.close()

        return {
            "status": "success",
            "node_id": target_node,
            "scenario_code": scenario_code,
            "message": device_result.get("message", "Scenario injected"),
            "request": request_body,
            "timestamp": datetime.now().isoformat(),
        }

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to device injector at {inject_url}")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail=f"Timed out connecting to {inject_url}")

# ============================================================================
# COMMAND EXECUTION ENDPOINT - MAPE-K Execute sends commands here
# ============================================================================

@app.post("/execute/command", response_model=CommandResponse)
async def execute_command(command: ExecuteCommand):
    """
    Receive command from MAPE-K Execute and forward to appropriate IoT device
    The gateway routes the command to the correct device based on node_id
    """
    node_id = command.node_id
    
    print(f"\n{'='*70}")
    print(f"📤 EXECUTE COMMAND REQUEST from MAPE-K")
    print(f"{'='*70}")
    print(f"Target Device: {node_id}")
    print(f"Plan Code: {command.plan_code}")
    print(f"Description: {command.description}")
    if command.scenario_code:
        print(f"Scenario: {command.scenario_code}")
    if command.parameter:
        print(f"Parameter: {command.parameter}")
    if command.escalation_level is not None:
        print(f"Escalation Level: {command.escalation_level}")
    if command.adaptation_goal:
        print(f"Adaptation Goal: {command.adaptation_goal}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if device is registered
    if node_id not in DEVICE_REGISTRY:
        error_msg = f"Device {node_id} not found in registry"
        print(f"✗ {error_msg}")
        print(f"{'='*70}\n")
        raise HTTPException(status_code=404, detail=error_msg)
    
    device_url = DEVICE_REGISTRY[node_id]
    
    try:
        # Forward command to the IoT device
        print(f"→ Forwarding command to device at {device_url}")
        
        response = requests.post(
            device_url,
            json={
                "plan_code": command.plan_code,
                "description": command.description
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            node_message = result.get('message', 'Success')
            plan_worked = bool(result.get('plan_worked', True))
            node_status = str(result.get('status', 'success')).lower()
            execution_status = 'success' if plan_worked and node_status == 'success' else 'failed'

            print(f"✓ Command delivered to {node_id}")
            print(f"✓ Device response: {node_message}")
            print(f"✓ Plan resolved issue: {plan_worked}")
            print(f"{'='*70}\n")
            
            # Log the execution in database
            with get_db_connection() as conn:
                cur = conn.cursor()
                if execution_status == 'success':
                    cur.execute("""
                        INSERT INTO execution_log 
                        (node_id, plan_code, description, status, timestamp)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (node_id, command.plan_code, command.description, 'success'))
                else:
                    cur.execute("""
                        INSERT INTO execution_log 
                        (node_id, plan_code, description, status, error_message, timestamp)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (node_id, command.plan_code, command.description, 'failed', node_message))
                cur.close()
            
            return CommandResponse(
                status=execution_status,
                message=node_message,
                node_id=node_id,
                timestamp=datetime.now().isoformat()
            )
        else:
            error_msg = f"Device returned HTTP {response.status_code}"
            print(f"✗ {error_msg}")
            print(f"{'='*70}\n")
            raise HTTPException(status_code=response.status_code, detail=error_msg)
    
    except requests.exceptions.ConnectionError:
        error_msg = f"Cannot connect to device {node_id} at {device_url}"
        print(f"✗ {error_msg}")
        print(f"{'='*70}\n")
        raise HTTPException(status_code=503, detail=error_msg)
    
    except requests.exceptions.Timeout:
        error_msg = f"Timeout connecting to device {node_id}"
        print(f"✗ {error_msg}")
        print(f"{'='*70}\n")
        raise HTTPException(status_code=504, detail=error_msg)
    
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        print(f"✗ {error_msg}")
        print(f"{'='*70}\n")
        
        # Log the failed execution
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO execution_log 
                    (node_id, plan_code, description, status, error_message, timestamp)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (node_id, command.plan_code, command.description, 'failed', str(e)))
                cur.close()
        except:
            pass
        
        raise HTTPException(status_code=500, detail=error_msg)

# ============================================================================
# HEALTH CHECK AND STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "IoT Gateway",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/devices")
async def list_devices():
    """List all registered devices"""
    return {
        "devices": list(DEVICE_REGISTRY.keys()),
        "count": len(DEVICE_REGISTRY)
    }

@app.get("/device/{node_id}/status")
async def get_device_status(node_id: str):
    """Get status of a specific device"""
    if node_id not in DEVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Device {node_id} not found")
    
    device_url = DEVICE_REGISTRY[node_id].replace("/command", "/status")
    
    try:
        response = requests.get(device_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="Device unavailable")
    except:
        raise HTTPException(status_code=503, detail=f"Cannot connect to device {node_id}")

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("Starting IoT Gateway Server")
    print("=" * 70)
    print("Data Ingestion Endpoints:")
    print("  POST /iot/water_quality")
    print("  POST /iot/water_level")
    print("  POST /iot/water_flow")
    print("  POST /iot/motor")
    print("\nMonitor Endpoints:")
    print("  GET /monitor/water_quality/latest")
    print("  GET /monitor/water_level/latest")
    print("  GET /monitor/water_flow/latest")
    print("  GET /monitor/motor/latest")
    print("\nExecution Endpoint:")
    print("  POST /execute/command")
    print("\nDashboard Endpoints:")
    print("  GET /dashboard")
    print("  GET /dashboard/data")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=3043, log_level="info")
