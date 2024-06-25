from app.logger import get_logger

logger = get_logger()

def analyze(data):
    logger.info(f"Analyzing data: {data}")
    # Example: Simple anomaly detection logic
    if data.temperature > 50 or data.humidity > 80:
        return {"status": "anomaly", "data": data}
    return {"status": "normal", "data": data}
