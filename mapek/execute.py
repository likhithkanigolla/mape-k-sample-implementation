from app.logger import get_logger
import requests
import json

logger = get_logger()

# Example node IP mapping (replace with DB/config lookup in production)
NODE_IPS = {
    "motor_1": "192.168.1.10",
    "water_flow_1": "192.168.1.11",
    "water_level_1": "192.168.1.12",
    "water_quality_1": "192.168.1.13"
}

def execute(plans):
    """
    Executes each plan by sending a request to the node's IP.
    """
    from mapek.knowledge import update_knowledge
    logger.info(f"Executing plans: {plans}")
    for plan in plans:
        node_id = plan.get('node_id')
        command = plan.get('command')
        parameters = plan.get('parameters')
        ip = NODE_IPS.get(node_id)
        if not ip:
            logger.error(f"No IP found for node {node_id}, skipping execution.")
            continue
        # Placeholder for actual execution logic (e.g., HTTP POST, MQTT, etc.)
        # url = f"http://{ip}/execute"
        # payload = {"command": command, "parameters": parameters}
        # For now, just pass
        pass
