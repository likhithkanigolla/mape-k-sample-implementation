import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from pydantic import BaseModel


class IoTNodeData(BaseModel):
    id: int
    node_id: str
    temperature: float
    humidity: float
    anomaly_label: int

def train_ml_model(historical_data):
    # Convert the historical data into a DataFrame for easier manipulation
    columns = ['id', 'temperature', 'humidity', 'timestamp', 'anomaly_label']
    df = pd.DataFrame(historical_data, columns=columns)
    
    # Prepare the feature matrix (X) and the target vector (y)
    X = df[['temperature', 'humidity']]
    y = df['anomaly_label']
    
    # Train a RandomForestClassifier model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model  # Return the trained model object

def predict_anomalies(model, data):
    X = [[data.temperature, data.humidity]]
    return model.predict(X)[0] == 1  # 1 indicates an anomaly with RandomForestClassifier
