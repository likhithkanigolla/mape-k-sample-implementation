import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from mapek.application.services.monitor_service import Monitor
from mapek.application.services.analyzer_service import Analyzer
from mapek.application.services.planner_service import Planner
from mapek.application.services.executor_service import Executor
from mapek.application.services.container import MAPEKContainer
from mapek.logger import logger
from mapek.knowledge import get_db_conn

# Initialize MAPE-K components using the service container
container = MAPEKContainer()
monitor_service = Monitor(container.node_repo)
analyzer_service = Analyzer(container.threshold_repo)
planner_service = Planner(container.plan_repo)
executor_service = Executor(container.node_repo)

def mapek_background_loop():
    logger.info("[MAPE-K] Starting MAPE-K background loop...")
    try:
        # Monitor: Read sensor data
        sensor_data_list = monitor_service.read_sensors()
        logger.info(f"[MAPE-K] Sensor data: {sensor_data_list}")
        
        # Analyze: Process sensor data
        analysis_result = analyzer_service.analyze(sensor_data_list)
        logger.info(f"[MAPE-K] Analysis result: {analysis_result}")
        
        # Plan: Select appropriate plans based on analysis
        plan_result = planner_service.select_plans(analysis_result)
        logger.info(f"[MAPE-K] Plans selected: {plan_result}")
        
        # Execute: Execute the selected plans (this is async, so we'll handle it)
        if plan_result:
            import asyncio
            asyncio.run(executor_service.execute(plan_result))
            logger.info("[MAPE-K] Execution complete.")
        else:
            logger.info("[MAPE-K] No plans to execute.")
            
        # Store results in database for each node
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Store analysis and plan results for each node
        for sensor_data in sensor_data_list:
            node_id = sensor_data['node_id']
            # Find corresponding analysis result for this node
            node_analysis = next((result for result in analysis_result if result.get('node_id') == node_id), None)
            if node_analysis:
                state = node_analysis.get('state', 'unknown')
                cur.execute(
                    "INSERT INTO analyze (node_id, result, state) VALUES (%s, %s, %s)",
                    (node_id, str(node_analysis), state)
                )
            
            # Find corresponding plan for this node
            node_plan = next((plan for plan in plan_result if plan.get('node_id') == node_id), None)
            if node_plan:
                plan_data = node_plan.get('plan', {})
                priority = plan_data.get('priority') if isinstance(plan_data, dict) else None
                cur.execute(
                    "INSERT INTO plan (node_id, result, priority) VALUES (%s, %s, %s)",
                    (node_id, str(plan_data), priority)
                )
                cur.execute(
                    "INSERT INTO execute (node_id, result) VALUES (%s, %s)",
                    (node_id, str(plan_data))
                )
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"[MAPE-K] Error in background loop: {e}")
        # Ensure database connection is closed even on error
        try:
            if 'conn' in locals():
                conn.rollback()
                cur.close()
                conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    while True:
        print("[MAPE-K] Running MAPE-K background loop...")
        mapek_background_loop()
        time.sleep(60)
