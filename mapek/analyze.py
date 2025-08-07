
from mapek.knowledge import get_db_conn
from app.logger import get_logger

logger = get_logger()

def analyze(sensor_data_list):
    """
    Accepts a list of sensor data dicts, returns a list of dicts per node,
    with each parameter marked 1 (good) or 0 (bad) based on thresholds.
    """
    conn = get_db_conn()
    cur = conn.cursor()
    results = []
    for sensor_data in sensor_data_list:
        node_id = sensor_data.get('node_id')
        node_result = {'node_id': node_id}
        bad_count = 0
        for key, value in sensor_data.items():
            if key == 'node_id':
                continue
            # Get threshold for this parameter
            cur.execute(
                "SELECT min_value, max_value FROM thresholds WHERE parameter = %s LIMIT 1", (key,)
            )
            threshold = cur.fetchone()
            if threshold:
                min_val, max_val = threshold
                status = 1 if (min_val <= value <= max_val) else 0
                node_result[key] = status
                if status == 0:
                    bad_count += 1
            else:
                node_result[key] = 1  # If no threshold, assume good
        # Set state based on bad_count
        if bad_count == 0:
            node_result['state'] = 'normal'
        elif bad_count == 1:
            node_result['state'] = 'alert'
        elif bad_count > 1:
            node_result['state'] = 'emergency'
        results.append(node_result)
        logger.info(f"Analyzed node {node_id}: {node_result}")
    cur.close()
    conn.close()
    return results

