"""
Execute component - Executes selected plans
Simple implementation without design patterns
"""
import requests
from logger import logger
from knowledge import get_db_conn

class Executor:
    """Executor service to execute action plans"""
    
    def __init__(self):
        logger.info("Executor service initialized")
    
    def execute(self, selected_plans):
        """Execute the selected plans"""
        execution_results = []
        
        for plan_item in selected_plans:
            node_id = plan_item['node_id']
            plan = plan_item['plan']
            
            try:
                # Get node IP address from database
                node_ip = self._get_node_ip(node_id)
                
                if node_ip:
                    # Send command to the node
                    result = self._send_command(node_ip, plan)
                    
                    execution_results.append({
                        'node_id': node_id,
                        'plan_code': plan['code'],
                        'status': result['status'],
                        'message': result.get('message', '')
                    })
                    
                    logger.info(f"Executor: Executed plan '{plan['code']}' for {node_id} - Status: {result['status']}")
                else:
                    logger.warning(f"Executor: No IP address found for {node_id}")
                    execution_results.append({
                        'node_id': node_id,
                        'plan_code': plan['code'],
                        'status': 'failed',
                        'message': 'No IP address'
                    })
            
            except Exception as e:
                logger.error(f"Executor error for {node_id}: {e}")
                execution_results.append({
                    'node_id': node_id,
                    'plan_code': plan['code'],
                    'status': 'error',
                    'message': str(e)
                })
        
        return execution_results
    
    def _get_node_ip(self, node_id):
        """Get IP address for a node from database"""
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            cur.execute("SELECT ip_address FROM nodes WHERE node_id = %s", (node_id,))
            row = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if row:
                return row[0]
        
        except Exception as e:
            logger.error(f"Error getting node IP for {node_id}: {e}")
        
        return None
    
    def _send_command(self, node_ip, plan):
        """Send command to IoT node"""
        try:
            # In a real system, this would send actual commands to IoT devices
            # For now, we'll simulate the execution
            
            url = f"http://{node_ip}/command"
            payload = {
                'plan_code': plan['code'],
                'description': plan['description']
            }
            
            # Simulate command execution (comment out if real API exists)
            # response = requests.post(url, json=payload, timeout=5)
            # if response.status_code == 200:
            #     return {'status': 'success'}
            # else:
            #     return {'status': 'failed', 'message': f'HTTP {response.status_code}'}
            
            # Simulated success
            logger.info(f"Simulated command sent to {node_ip}: {plan['code']}")
            return {'status': 'simulated_success'}
        
        except Exception as e:
            logger.error(f"Error sending command to {node_ip}: {e}")
            return {'status': 'error', 'message': str(e)}
