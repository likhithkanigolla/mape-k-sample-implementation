import joblib
from app.knowledge import get_historical_data, get_thresholds, get_ml_model
from app.ml_model import predict_anomalies
from app.logger import get_logger

logger = get_logger()

def analyze(data):
    node_id = data.node_id
    thresholds = get_thresholds(node_id)
    model = get_ml_model(node_id)
    logger.info(f"Analyzing data: {data}")

    # Retrieve historical data for the node
    historical_data = get_historical_data(data.node_id)
    logger.info(f"Historical data for node {data.node_id}: {historical_data}")


    if thresholds:
        temp_threshold, humidity_threshold = thresholds
        if data.temperature > temp_threshold or data.humidity > humidity_threshold:
            return {"status": "anomaly", "reason": "threshold", "data": data, "historical_data": historical_data}
    
    if model:
        # Prepare the data for prediction (assuming the model expects temperature and humidity as input features)
        input_features = [[data.temperature, data.humidity]]
        prediction = model.predict(input_features)
        if prediction == 1:  # Assuming 1 indicates an anomaly
            return {"node_id": node_id, "status": "anomaly", "details": data}

    return {"status": "normal", "data": data, "historical_data": historical_data}