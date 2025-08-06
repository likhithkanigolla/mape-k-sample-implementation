from app.logger import get_logger

logger = get_logger()

def execute(plan_result):
    logger.info(f"Executing plan: {plan_result}")
    if plan_result.get("action") == "alert":
        # Example: Execute an alert action
        logger.warning(f"Alert! Anomaly detected: {plan_result['details']}")
    else:
        logger.info("No action needed.")
