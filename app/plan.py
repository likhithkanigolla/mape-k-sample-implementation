from app.logger import get_logger

logger = get_logger()

def plan(analysis_result):
    logger.info(f"Planning based on analysis: {analysis_result}")
    # Plan actions based on analysis result
    if analysis_result.get("status") == "anomaly":
        return {"action": "alert", "details": analysis_result}
    return {"action": "none", "details": analysis_result}
