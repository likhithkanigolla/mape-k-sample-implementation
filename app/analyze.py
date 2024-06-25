from app.knowledge import get_historical_data, get_thresholds, get_ml_model
from app.ml_model import predict_anomalies
from app.logger import get_logger

logger = get_logger()

def analyze(data):
    logger.info(f"Analyzing data: {data}")

    # Retrieve historical data for the node
    historical_data = get_historical_data(data.node_id)
    logger.info(f"Historical data for node {data.node_id}: {historical_data}")

    # Retrieve thresholds for the node
    thresholds = get_thresholds(data.node_id)
    if thresholds:
        temp_threshold, humidity_threshold = thresholds
        if data.temperature > temp_threshold or data.humidity > humidity_threshold:
            return {"status": "anomaly", "reason": "threshold", "data": data, "historical_data": historical_data}

    # Retrieve and use ML model for anomaly detection
    model_blob = get_ml_model(data.node_id)
    if model_blob and predict_anomalies(model_blob, data):
        return {"status": "anomaly", "reason": "ml_model", "data": data, "historical_data": historical_data}

    return {"status": "normal", "data": data, "historical_data": historical_data}
