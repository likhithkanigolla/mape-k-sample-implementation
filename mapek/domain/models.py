from pydantic import BaseModel, validator, ValidationError
from typing import Optional
from datetime import datetime

class SensorReading(BaseModel):
    node_id: str
    timestamp: datetime
    water_level: Optional[float] = None
    temperature: Optional[float] = None
    tds_voltage: Optional[float] = None
    flow_rate: Optional[float] = None

    @validator('node_id')
    def validate_node_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Node ID must be a non-empty string')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v > datetime.now():
            raise ValueError('Sensor timestamp cannot be in future')
        return v

    @validator('water_level')
    def validate_water_level(cls, v):
        if v is not None and (v < 0 or v > 500):
            raise ValueError('Water level must be between 0-500 cm')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < -10 or v > 60):
            raise ValueError('Temperature must be between -10 and 60°C')
        return v

    @validator('tds_voltage')
    def validate_tds_voltage(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('TDS voltage must be between 0-5V')
        return v

    @validator('flow_rate')
    def validate_flow_rate(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Flow rate must be between 0-100 L/min')
        return v
