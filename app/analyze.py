from app.knowledge import get_historical_data
from app.logger import get_logger

logger = get_logger()

def analyze(data):
    logger.info(f"Analyzing data: {data}")
    # Retrieve historical data for the node
    historical_data = get_historical_data(data.node_id)
    logger.info(f"Historical data for node {data.node_id}: {historical_data}")
    
    # Example: Simple anomaly detection logic
    if data.temperature > 50 or data.humidity > 80:
        return {"status": "anomaly", "data": data, "historical_data": historical_data}
    return {"status": "normal", "data": data, "historical_data": historical_data}
