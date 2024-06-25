from pydantic import BaseModel

class IoTNodeData(BaseModel):
    node_id: str
    temperature: float
    humidity: float
