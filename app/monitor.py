from app.knowledge import update_knowledge
from app.logger import get_logger

logger = get_logger()

def monitor(data):
    logger.info(f"Monitoring data: {data}")
    update_knowledge(data)
