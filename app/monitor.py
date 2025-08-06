from app.knowledge import update_knowledge
from app.logger import get_logger

logger = get_logger()

def monitor(data):
    # Store the incoming data into the Knowledge component
    update_knowledge(data)
    logger.info(f"Data monitored and stored: {data}")
    # In a scalable system, you could trigger analysis here via event/queue
    # For now, monitoring is decoupled and only stores data
    #dshould tge read and analyse 
