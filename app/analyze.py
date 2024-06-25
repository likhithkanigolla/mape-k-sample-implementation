import joblib
from app.knowledge import get_historical_data, get_thresholds, get_ml_model
from app.ml_model import predict_anomalies
from app.logger import get_logger
from app.knowledge import update_anomaly_label

logger = get_logger()

def analyze(data):
    print("Analyzing data:",data)
    node_id = data.node_id
    thresholds = get_thresholds(node_id)
    logger.info(f"Analyzing data: {data}")

    # Retrieve historical data for the node
    historical_data = get_historical_data(node_id)
    logger.info(f"Historical data for node {node_id}: {historical_data}")

    try:
        model = get_ml_model(node_id)
        if model:
            # Prepare the data for prediction
            input_features = [[data.temperature, data.humidity]]
            prediction = model.predict(input_features)
            if prediction == 1:  # Assuming 1 indicates an anomaly
                logger.info(f"Anomaly detected for node {node_id}")
                return {
                    "node_id": node_id,
                    "status": "anomaly",
                    "details": data
                }
        else:
            logger.warning(f"No model found for node_id: {node_id}")

    except Exception as e:
        logger.error(f"Error loading or using model for node {node_id}: {e}")


    latest_data = historical_data[0] if historical_data else None
    
    # Check against thresholds if model-based detection didn't find an anomaly
    if thresholds:
        temp_threshold, humidity_threshold = thresholds
        if data.temperature > temp_threshold or data.humidity > humidity_threshold:
            update_anomaly_label(node_id, latest_data[0], 1)
            return {"node_id": node_id, "status": "anomaly", "reason": "threshold", "data": data, "historical_data": historical_data}

    # If neither thresholds nor model-based detection found anomalies, return normal status
    return {"status": "normal","data": data,"historical_data": historical_data}

