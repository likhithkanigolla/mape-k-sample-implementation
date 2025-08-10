from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError
import psycopg2
from psycopg2.extras import RealDictCursor
from app.ml_model import train_ml_model
import pickle
import os
import subprocess


app = FastAPI()
scheduler = BackgroundScheduler()

# PostgreSQL connection setup
DB_HOST = "localhost"
DB_NAME = "mapek_dt"
DB_USER = "postgres"
DB_PASS = "postgres"

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=5432,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

from models.iot_node import IoTNodeData, Thresholds, WaterQualityData, WaterFlowData, WaterLevelData, MotorData

@app.post("/iot/data")
async def receive_data(data: IoTNodeData):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO monitor (node_id, temperature, humidity) VALUES (%s, %s, %s)",
            (data.node_id, data.temperature, data.humidity)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/thresholds")
async def set_node_thresholds(thresholds: Thresholds):
    try:
        set_thresholds(thresholds.node_id, thresholds.temperature_threshold, thresholds.humidity_threshold)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/iot/train_model/{node_id}")
# async def train_node_model(node_id: str):
#     try:
#         historical_data = get_historical_data(node_id)
#         if not historical_data:
#             raise HTTPException(status_code=404, detail="No historical data found for the specified node_id")
#         model = train_ml_model(historical_data)
#         store_ml_model(node_id, model)  # Store the model using joblib
#         return {"status": "success"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_data/{node_id}")
async def get_data(node_id: str):
    try:
        historical_data = get_historical_data(node_id)
        return historical_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_latest_data/{node_id}")
async def get_latest_data(node_id: str):
    try:
        historical_data = get_historical_data(node_id)
        if historical_data:
            return historical_data[0]
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_all_node_ids")
async def get_all_node_ids():
    try:
        node_ids = get_node_ids()
        return node_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_thresholds/{node_id}")
async def get_thresholds_values(node_id: str):
    try:
        thresholds = get_thresholds(node_id)
        return thresholds
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/water_quality")
async def receive_water_quality(data: WaterQualityData):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO water_quality (node_id, temperature, tds_voltage, uncompensated_tds, compensated_tds) VALUES (%s, %s, %s, %s, %s)",
            (data.node_id, data.temperature, data.tds_voltage, data.uncompensated_tds, data.compensated_tds)
        )
        conn.commit()
        # print(f"[MAPE-K] Inserted water_quality: {data.dict()}")
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print(f"[MAPE-K] Error inserting water_quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/water_flow")
async def receive_water_flow(data: WaterFlowData):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO water_flow (node_id, flowrate, total_flow, pressure, pressure_voltage) VALUES (%s, %s, %s, %s, %s)",
            (data.node_id, data.flowrate, data.total_flow, data.pressure, data.pressure_voltage)
        )
        conn.commit()
        # print(f"[MAPE-K] Inserted water_flow: {data.dict()}")
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print(f"[MAPE-K] Error inserting water_flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/water_level")
async def receive_water_level(data: WaterLevelData):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO water_level (node_id, water_level, temperature) VALUES (%s, %s, %s)",
            (data.node_id, data.water_level, data.temperature)
        )
        conn.commit()
        # print(f"[MAPE-K] Inserted water_level: {data.dict()}")
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print(f"[MAPE-K] Error inserting water_level: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/motor")
async def receive_motor(data: MotorData):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO motor (node_id, status, voltage, current, power, energy, frequency, power_factor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data.node_id, data.status, data.voltage, data.current, data.power, data.energy, data.frequency, data.power_factor)
        )
        conn.commit()
        # print(f"[MAPE-K] Inserted motor: {data.dict()}")
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print(f"[MAPE-K] Error inserting motor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# def scheduled_retraining():
#     node_ids = get_node_ids()
#     for node_id_tuple in node_ids:
#         node_id = node_id_tuple[0] if isinstance(node_id_tuple, (tuple, list)) else node_id_tuple
#         try:
#             historical_data = get_historical_data(node_id)
#             if historical_data:
#                 model = train_ml_model(historical_data)
#                 store_ml_model(node_id, model)
#                 print(f"Model retrained for node {node_id}")
#         except Exception as e:
#             print(f"Error retraining model for node {node_id}: {str(e)}")

@app.on_event("shutdown")
def shutdown_event():
    try:
        scheduler.shutdown()
    except SchedulerNotRunningError:
        pass

@app.on_event("startup")
def startup_event():
    # print(f"[MAPE-K] Connecting to DB: host={DB_HOST}, port=5432, dbname={DB_NAME}, user={DB_USER}")
    # print("[MAPE-K] Running table creation on startup...")
    create_tables_if_not_exists()
    # print("[MAPE-K] Table creation completed.")
    # Print all tables in the database
    conn = get_db_conn()
    # print("[MAPE-K] Connected to DB successfully.", conn)
    cur = conn.cursor()
    # cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    # tables = cur.fetchall()
    # print("[MAPE-K] Tables in DB:")
    # for t in tables:
    #     print(f"  - {t[0]}")
    cur.close()
    conn.close()

def create_tables_if_not_exists():
    conn = get_db_conn()
    cur = conn.cursor()
    with open(os.path.join(os.path.dirname(__file__), "create_tables.sql"), "r") as f:
        sql_commands = f.read()
        try:
            # print("Executing full SQL file for table creation...")
            cur.execute(sql_commands)
            # print("[MAPE-K] Table creation SQL executed successfully.")
        except Exception as e:
            print(f"Error executing table creation SQL:\n{e}")
    conn.commit()
    cur.close()
    conn.close()
    print("[MAPE-K] Table creation completed.")

# Start sensor scripts in background
sensor_scripts = [
    "water_quality_sensor.py",
    "water_flow_sensor.py",
    "water_level_sensor.py",
    "motor_sensor.py"
]
for script in sensor_scripts:
    subprocess.Popen(["python3", os.path.join(os.path.dirname(__file__), "../scripts", script)])
