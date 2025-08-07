from pydantic import BaseModel

class IoTNodeData(BaseModel):
    node_id: str
    temperature: float
    humidity: float

class Thresholds(BaseModel):
    node_id: str
    temperature_threshold: float
    humidity_threshold: float

class WaterQualityData(BaseModel):
    node_id: str
    temperature: float
    tds_voltage: float
    uncompensated_tds: float
    compensated_tds: float

class WaterFlowData(BaseModel):
    node_id: str
    flowrate: float
    total_flow: float
    pressure: float
    pressure_voltage: float

class WaterLevelData(BaseModel):
    node_id: str
    water_level: float
    temperature: float

class MotorData(BaseModel):
    node_id: str
    status: str
    voltage: float
    current: float
    power: float
    energy: float
    frequency: float
    power_factor: float
