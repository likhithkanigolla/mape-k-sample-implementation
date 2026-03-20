"""
Scenario catalog and helper utilities for uncertainty-driven adaptation.
Implements scenarios S1-S11 as provided by the user.
"""

SCENARIO_CATALOG = {
    "S1": {
        "uncertainty": "Sensor readings drift over time",
        "adaptation": "Recalibrate the sensor and adjust sensing parameters at the device level",
        "goal": "Restore correct sensing behaviour",
        "default_plan_code": "RECALIBRATE_SENSOR_PARAMS",
    },
    "S2": {
        "uncertainty": "Sensor produces invalid values",
        "adaptation": "Disable the faulty sensor and send restart command; stop readings and notify authorities if unresolved",
        "goal": "Prevent faulty sensing from affecting system operation",
        "default_plan_code": "DISABLE_SENSOR_AND_RESTART",
    },
    "S3": {
        "uncertainty": "Sensor produces constant zero values",
        "adaptation": "Reset sensing module and reinitialize device",
        "goal": "Restore normal sensing functionality",
        "default_plan_code": "RESET_SENSING_MODULE",
    },
    "S4": {
        "uncertainty": "Data is not received from a node",
        "adaptation": "Restart node and enforce periodic data reporting",
        "goal": "Restore data flow from the node",
        "default_plan_code": "RESTART_NODE_ENFORCE_REPORTING",
    },
    "S5": {
        "uncertainty": "Network connection is very unstable",
        "adaptation": "Reassign node to available gateway and reconnect; node reports updated IP back",
        "goal": "Re-establish connectivity",
        "default_plan_code": "REASSIGN_GATEWAY",
    },
    "S6": {
        "uncertainty": "Node repeatedly reconnects",
        "adaptation": "Stabilize communication by adjusting connection intervals",
        "goal": "Ensure stable communication behaviour",
        "default_plan_code": "ADJUST_CONNECTION_INTERVAL",
    },
    "S7": {
        "uncertainty": "Node memory usage exceeds limits",
        "adaptation": "Reduce local processing and clear internal buffers",
        "goal": "Prevent node crash",
        "default_plan_code": "REDUCE_PROCESSING_CLEAR_BUFFERS",
    },
    "S8": {
        "uncertainty": "Node battery drops rapidly or energy utilization is high",
        "adaptation": "Switch node to low-power mode by reducing sensing and communication frequency",
        "goal": "Extend node lifetime",
        "default_plan_code": "ENABLE_LOW_POWER_MODE",
    },
    "S9": {
        "uncertainty": "Sensor behaviour deviates from expected pattern",
        "adaptation": "Isolate sensor and remove it from control decisions",
        "goal": "Prevent incorrect system behaviour",
        "default_plan_code": "ISOLATE_SENSOR",
    },
    "S10": {
        "uncertainty": "System action is not executed correctly",
        "adaptation": "Verify outcomes and reissue control commands",
        "goal": "Ensure correct actuation",
        "default_plan_code": "VERIFY_AND_REISSUE_COMMAND",
    },
    "S11": {
        "uncertainty": "System services are failing",
        "adaptation": "Check service health using heartbeat and apply service recovery",
        "goal": "Maintain system consistency",
        "default_plan_code": "SERVICE_HEALTH_CHECK_AND_FIX",
    },
}


def make_scenario_event(code, node_id, parameter=None, details=None, severity="warning"):
    """Create a normalized scenario event payload."""
    base = SCENARIO_CATALOG.get(code, {})
    return {
        "code": code,
        "node_id": node_id,
        "parameter": parameter,
        "severity": severity,
        "uncertainty": base.get("uncertainty", "Unknown uncertainty"),
        "adaptation": base.get("adaptation", "No adaptation defined"),
        "goal": base.get("goal", "No goal defined"),
        "default_plan_code": base.get("default_plan_code", "HANDLE_SCENARIO"),
        "details": details or {},
    }
