from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.monitor import monitor
from app.analyze import analyze
from app.plan import plan
from app.execute import execute
from app.knowledge import set_thresholds, store_ml_model, update_knowledge
from app.ml_model import train_ml_model

app = FastAPI()

class IoTNodeData(BaseModel):
    node_id: str
    temperature: float
    humidity: float

class Thresholds(BaseModel):
    node_id: str
    temperature_threshold: float
    humidity_threshold: float

class MLModelData(BaseModel):
    node_id: str
    historical_data: list

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

@app.post("/iot/train_model")
async def train_node_model(model_data: MLModelData):
    try:
        model_blob = train_ml_model(model_data.historical_data)
        store_ml_model(model_data.node_id, model_blob)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
