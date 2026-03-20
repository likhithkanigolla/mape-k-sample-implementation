"""
Execute component - Parameter-based plan execution
Sends commands to IoT devices and records execution with parameter/escalation info
"""
import requests
from logger import logger
from knowledge import get_db_conn, KnowledgeBase

# IoT Gateway configuration
GATEWAY_URL = "http://localhost:3043"
EXECUTE_ENDPOINT = f"{GATEWAY_URL}/execute/command"

class Executor:
    """Executor service to execute action plans via IoT Gateway"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        logger.info("Executor service initialized (parameter-based)")
        logger.info(f"IoT Gateway URL: {GATEWAY_URL}")
    
    def execute(self, selected_plans):
        """Execute the selected plans by sending commands through IoT Gateway"""
        execution_results = []
        
        for plan_item in selected_plans:
            node_id = plan_item['node_id']
            plan = plan_item['plan']
            parameter = plan_item.get('parameter')  # NEW: Which parameter is being fixed
            scenario = plan_item.get('scenario')
            escalation_level = plan.get('escalation_level', 0)  # NEW: Escalation level
            
            # Skip NO_ACTION plans
            if plan['code'] == 'NO_ACTION':
                logger.info(f"Executor: Skipping NO_ACTION for {node_id}")
                continue
            
            try:
                # Send command through IoT Gateway
                result = self._send_command_via_gateway(node_id, plan, parameter, scenario)
                
                # Record execution in knowledge base with parameter and escalation level
                if parameter:
                    self.kb.record_plan_execution(
                        node_id=node_id,
                        parameter=parameter,
                        plan_code=plan['code'],
                        escalation_level=escalation_level
                    )
                    logger.info(
                        f"Recorded execution: {node_id}.{parameter} → {plan['code']} "
                        f"(Level {escalation_level})"
                    )
                else:
                    logger.warning(f"No parameter specified for plan execution: {plan['code']}")
                
                execution_results.append({
                    'node_id': node_id,
                    'parameter': parameter,
                    'scenario_code': plan.get('scenario_code'),
                    'plan_code': plan['code'],
                    'escalation_level': escalation_level,
                    'status': result['status'],
                    'message': result.get('message', '')
                })
                
                level_desc = f"Level {escalation_level}" if escalation_level > 0 else ""
                logger.info(
                    f"Executor: Executed '{plan['code']}' {level_desc} "
                    f"for {node_id}.{parameter} - Status: {result['status']}"
                )
            
            except Exception as e:
                logger.error(f"Executor error for {node_id}.{parameter}: {e}")
                execution_results.append({
                    'node_id': node_id,
                    'parameter': parameter,
                    'scenario_code': plan.get('scenario_code'),
                    'plan_code': plan['code'],
                    'escalation_level': escalation_level,
                    'status': 'error',
                    'message': str(e)
                })
        
        return execution_results
    
    def _send_command_via_gateway(self, node_id, plan, parameter=None, scenario=None):
        """Send command to IoT device through the Gateway"""
        try:
            payload = {
                'node_id': node_id,
                'plan_code': plan['code'],
                'description': plan['description'],
                'parameter': parameter,  # NEW: Include parameter for targeted commands
                'escalation_level': plan.get('escalation_level', 0),  # NEW: Include escalation level
                'scenario_code': plan.get('scenario_code'),
                'adaptation_goal': plan.get('adaptation_goal'),
                'scenario_details': scenario.get('details', {}) if scenario else None,
            }
            
            param_str = f".{parameter}" if parameter else ""
            logger.info(f"Sending command to Gateway for {node_id}{param_str}: {plan['code']}")
            
            # Send command to IoT Gateway
            response = requests.post(EXECUTE_ENDPOINT, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Command successfully executed on {node_id}{param_str}")
                return {
                    'status': result.get('status', 'success'),
                    'message': result.get('message', 'Command executed successfully')
                }
            else:
                error_msg = f"Gateway returned HTTP {response.status_code}"
                logger.error(f"Error executing command: {error_msg}")
                return {
                    'status': 'failed',
                    'message': error_msg
                }
        
        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to IoT Gateway at {GATEWAY_URL}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
        
        except requests.exceptions.Timeout:
            error_msg = f"Timeout connecting to Gateway for {node_id}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
        
        except Exception as e:
            error_msg = f"Error sending command: {str(e)}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
