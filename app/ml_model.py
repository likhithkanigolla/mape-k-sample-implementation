import pickle
from sklearn.ensemble import IsolationForest

def train_ml_model(data):
    # Train an Isolation Forest model for anomaly detection
    model = IsolationForest(contamination=0.1)
    X = [[d[0], d[1]] for d in data]
    model.fit(X)
    return pickle.dumps(model)

def predict_anomalies(model_blob, data):
    model = pickle.loads(model_blob)
    X = [[data.temperature, data.humidity]]
    return model.predict(X)[0] == -1  # -1 indicates an anomaly
