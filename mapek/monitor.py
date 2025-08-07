from mapek.knowledge import update_knowledge, get_node_ids, get_historical_data
from app.logger import get_logger

logger = get_logger()

import time

def monitor():
    while True:
        sensor_data_list = []
        node_ids = get_node_ids()
        for node_id_tuple in node_ids:
            node_id = node_id_tuple[0] if isinstance(node_id_tuple, (tuple, list)) else node_id_tuple
            historical_data = get_historical_data(node_id)
            if historical_data:
                latest_data = historical_data[0]
                # Determine node type by node_id naming convention
                if "water_quality" in node_id:
                    sensor_data = {
                        "node_id": node_id,
                        "temperature": latest_data[1],
                        "tds_voltage": latest_data[2],
                        "uncompensated_tds": latest_data[3],
                        "compensated_tds": latest_data[4]
                    }
                elif "water_flow" in node_id:
                    sensor_data = {
                        "node_id": node_id,
                        "flowrate": latest_data[1],
                        "total_flow": latest_data[2],
                        "pressure": latest_data[3],
                        "pressure_voltage": latest_data[4]
                    }
                elif "water_level" in node_id:
                    sensor_data = {
                        "node_id": node_id,
                        "water_level": latest_data[1],
                        "temperature": latest_data[2]
                    }
                elif "motor" in node_id:
                    sensor_data = {
                        "node_id": node_id,
                        "status": latest_data[1],
                        "voltage": latest_data[2],
                        "current": latest_data[3],
                        "power": latest_data[4],
                        "energy": latest_data[5],
                        "frequency": latest_data[6],
                        "power_factor": latest_data[7]
                    }
                else:
                    # Default: just log all columns
                    sensor_data = {"node_id": node_id}
                    for i, val in enumerate(latest_data[1:], start=1):
                        sensor_data[f"param_{i}"] = val
                sensor_data_list.append(sensor_data)
        logger.info(f"Monitor step: Latest sensor data: {sensor_data_list}")
        yield sensor_data_list
        time.sleep(60)
