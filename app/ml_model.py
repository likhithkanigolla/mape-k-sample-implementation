import pickle
from typing import List, Dict
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from pydantic import BaseModel
from app.knowledge import store_ml_model


class IoTNodeData(BaseModel):
    id: int
    node_id: str
    temperature: float
    humidity: float
    anomaly_label: int

def train_ml_model(data):
    # Train a RandomForestClassifier model for anomaly detection
    print(data)
    # df = pd.DataFrame(data, columns=['temperature', 'humidity'])
    # X = df[['temperature', 'humidity']]
    # y = df['anomaly_label']  # Assuming you have a label indicating anomalies or normal data
    
    # model = RandomForestClassifier(n_estimators=100, random_state=42)
    # model.fit(X, y)
    
    # return model

def predict_anomalies(model, data):
    X = [[data.temperature, data.humidity]]
    return model.predict(X)[0] == 1  # 1 indicates an anomaly with RandomForestClassifier
