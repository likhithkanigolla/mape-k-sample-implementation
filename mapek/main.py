import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from mapek.monitor import monitor
from mapek.analyze import analyze
from mapek.plan import plan
from mapek.execute import execute
from mapek.knowledge import get_db_conn
from mapek.logger import get_logger

logger = get_logger()


# Create a single instance of the monitor generator (no monitor table used)
monitor_instance = monitor()

def mapek_background_loop():
    logger.info("[MAPE-K] Starting MAPE-K background loop...")
    try:
        sensor_data_list = next(monitor_instance)
        logger.info(f"[MAPE-K] Sensor data: {sensor_data_list}")
        # Pass the full sensor data list to analyze
        analyse_result = analyze(sensor_data_list)
        print(f"[MAPE-K] Analysis result: {analyse_result}")
        plan_result = plan(analyse_result)
        execute(plan_result)
        # Insert results into database for each node in sensor_data_list (no monitor table used)
        conn = get_db_conn()
        cur = conn.cursor()
        # if isinstance(plan_result, list) and len(plan_result) == len(sensor_data_list):
        #     # Each node has its own plan
        #     for sensor_data, node_plan in zip(sensor_data_list, plan_result):
        #         node_id = sensor_data['node_id']
        #         cur.execute(
        #             "INSERT INTO analyze (node_id, result, state) VALUES (%s, %s, %s)",
        #             (node_id, str(analyse_result), getattr(analyse_result, 'state', None) if hasattr(analyse_result, 'state') else None)
        #         )
        #         priority = node_plan['priority'] if isinstance(node_plan, dict) and 'priority' in node_plan else None
        #         cur.execute(
        #             "INSERT INTO plan (node_id, result, priority) VALUES (%s, %s, %s)",
        #             (node_id, str(node_plan), priority)
        #         )
        #         cur.execute(
        #             "INSERT INTO execute (node_id, result) VALUES (%s, %s)",
        #             (node_id, str(node_plan))
        #         )
        # else:
            # Single plan for all nodes
            # for sensor_data in sensor_data_list:
            #     node_id = sensor_data['node_id']
            #     cur.execute(
            #         "INSERT INTO analyze (node_id, result, state) VALUES (%s, %s, %s)",
            #         (node_id, str(analyse_result), getattr(analyse_result, 'state', None) if hasattr(analyse_result, 'state') else None)
            #     )
            #     if isinstance(plan_result, dict):
            #         priority = plan_result.get('priority') if 'priority' in plan_result else None
            #         cur.execute(
            #             "INSERT INTO plan (node_id, result, priority) VALUES (%s, %s, %s)",
            #             (node_id, str(plan_result), priority)
            #         )
            #         cur.execute(
            #             "INSERT INTO execute (node_id, result) VALUES (%s, %s)",
            #             (node_id, str(plan_result))
            #         )
            #     else:
            #         cur.execute(
            #             "INSERT INTO plan (node_id, result, priority) VALUES (%s, %s, %s)",
            #             (node_id, str(plan_result), None)
            #         )
            #         cur.execute(
            #             "INSERT INTO execute (node_id, result) VALUES (%s, %s)",
            #             (node_id, str(plan_result))
            #         )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"[MAPE-K] Error in background loop: {e}")

if __name__ == "__main__":
    while True:
        print("[MAPE-K] Running MAPE-K background loop...")
        mapek_background_loop()
        time.sleep(60)
