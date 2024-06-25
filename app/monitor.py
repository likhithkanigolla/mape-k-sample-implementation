from app.knowledge import update_knowledge
from app.logger import get_logger

logger = get_logger()

def monitor(data):
    # Store the incoming data into the Knowledge component
    update_knowledge(data)
    print(f"Data monitored and stored: {data}")
