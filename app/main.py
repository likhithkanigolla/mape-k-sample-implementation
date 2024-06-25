from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.monitor import monitor
from app.analyze import analyze
from app.plan import plan
from app.execute import execute
from app.knowledge import get_all_data

app = FastAPI()

class IoTNodeData(BaseModel):
    node_id: str
    temperature: float
    humidity: float

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

@app.get("/iot/data")
async def get_data():
    try:
        data = get_all_data()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
