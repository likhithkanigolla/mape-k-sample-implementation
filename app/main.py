from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from app.monitor import monitor
from app.analyze import analyze
from app.plan import plan
from app.execute import execute
from app.knowledge import set_thresholds, store_ml_model, get_historical_data, update_knowledge
from app.ml_model import train_ml_model

app = FastAPI()
scheduler = BackgroundScheduler()

class IoTNodeData(BaseModel):
    node_id: str
    temperature: float
    humidity: float

class Thresholds(BaseModel):
    node_id: str
    temperature_threshold: float
    humidity_threshold: float

@app.post("/iot/data")
async def receive_data(data: IoTNodeData):
    try:
        monitor(data)
        analysis_result = analyze(data)
        plan_result = plan(analysis_result)
        execute(plan_result)
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

@app.post("/iot/train_model/{node_id}")
async def train_node_model(node_id: str):
    try:
        historical_data = get_historical_data(node_id)
        if not historical_data:
            raise HTTPException(status_code=404, detail="No historical data found for the specified node_id")
        model_blob = train_ml_model(historical_data)
        store_ml_model(node_id, model_blob)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def scheduled_retraining():
    node_ids = get_all_node_ids()  # Function to get all node IDs
    for node_id in node_ids:
        try:
            historical_data = get_historical_data(node_id)
            if historical_data:
                model_blob = train_ml_model(historical_data)
                store_ml_model(node_id, model_blob)
                print(f"Model retrained for node {node_id}")
        except Exception as e:
            print(f"Error retraining model for node {node_id}: {str(e)}")

# Schedule the retraining every day at midnight
scheduler.add_job(scheduled_retraining, 'cron', hour=0, minute=0)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
