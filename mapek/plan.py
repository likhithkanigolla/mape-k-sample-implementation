
from app.logger import get_logger
from mapek.knowledge import get_db_conn, update_knowledge
import json

logger = get_logger()


def plan(analysis_results):
    """
    Accepts a list of analysis results (one per node).
    Selects and returns plans for each node based on analysis data.
    """
    conn = get_db_conn()
    cur = conn.cursor()
    plans = []
    logger.info(f"Planning based on analysis: {analysis_results}")

    for analysis_result in analysis_results:
        node_id = analysis_result.get('node_id') or analysis_result.get('sensor_data', {}).get('node_id')
        state = analysis_result.get('state')
        sensor_data = analysis_result.get('sensor_data', analysis_result)

        # Example logic: select plan based on state and node
        if state == "alert":
            # If water level is low, turn on motor
            if node_id == "water_level_1" and sensor_data.get('water_level', 1) == 0:
                cur.execute("SELECT * FROM plan WHERE plan_id = 'WL001' AND node_id = %s", ("motor_1",))
            # If water level is high, turn off motor
            elif node_id == "water_level_1" and sensor_data.get('water_level', 1) == 1:
                cur.execute("SELECT * FROM plan WHERE plan_id = 'WL002' AND node_id = %s", ("motor_1",))
            # If abnormality, restart node
            else:
                cur.execute("SELECT * FROM plan WHERE plan_id = 'SH002' AND node_id = %s", (node_id,))
        elif state == "emergency":
            cur.execute("SELECT * FROM plan WHERE plan_id = 'WL003' AND node_id = %s", ("motor_1",))
        elif state == "data_not_posting":
            cur.execute("SELECT * FROM plan WHERE plan_id = 'SH001' AND node_id = %s", (node_id,))
        elif state == "service_restart":
            cur.execute("SELECT * FROM plan WHERE plan_id = 'SH003' AND node_id = %s", (node_id,))
        elif state == "calibration":
            cur.execute("SELECT * FROM plan WHERE plan_id = 'CM001' AND node_id = %s", (node_id,))
        else:
            # Default: no action
            plans.append({"plan_id": "NONE", "node_id": node_id, "command": "no_action", "parameters": "{}", "priority": 99, "description": "No action required"})

        # Fetch and format plan(s) from DB
        if cur.description:
            rows = cur.fetchall()
            for row in rows:
                plan_dict = {
                    "plan_id": row[0],
                    "node_id": row[1],
                    "command": row[2],
                    "parameters": json.loads(row[3]) if row[3] else {},
                    "priority": row[4],
                    "description": row[5]
                }
                plans.append(plan_dict)
                update_knowledge(f"Plan selected: {plan_dict['plan_id']} for node {plan_dict['node_id']}", plan_dict['node_id'])

    cur.close()
    conn.close()
    return plans
