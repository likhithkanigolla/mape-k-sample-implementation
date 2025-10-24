"""
Plan component - Selects appropriate plans based on analysis
Simple implementation without design patterns
"""
from logger import logger
from knowledge import get_db_conn

class Planner:
    """Planner service to select appropriate action plans"""
    
    def __init__(self):
        self.plans = self._load_plans()
        logger.info("Planner service initialized")
    
    def _load_plans(self):
        """Load plans from database"""
        plans = {}
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT state, plan_code, description, priority 
                FROM plans 
                ORDER BY priority DESC
            """)
            rows = cur.fetchall()
            
            for row in rows:
                state = row[0]
                plan_code = row[1]
                description = row[2]
                priority = row[3]
                
                if state not in plans:
                    plans[state] = []
                
                plans[state].append({
                    'code': plan_code,
                    'description': description,
                    'priority': priority
                })
            
            cur.close()
            conn.close()
            
            logger.info(f"Loaded plans for {len(plans)} states")
            
        except Exception as e:
            logger.error(f"Error loading plans: {e}")
        
        return plans
    
    def select_plans(self, analysis_results):
        """Select appropriate plans based on analysis results"""
        selected_plans = []
        
        for result in analysis_results:
            node_id = result.get('node_id')
            state = result.get('state')
            
            if state in self.plans:
                # Get the highest priority plan for this state
                plan_list = self.plans[state]
                if plan_list:
                    plan = plan_list[0]  # Highest priority (already sorted)
                    
                    selected_plans.append({
                        'node_id': node_id,
                        'state': state,
                        'plan': plan
                    })
                    
                    logger.info(f"Planner: Selected plan '{plan['code']}' for {node_id} (state: {state})")
            else:
                logger.warning(f"Planner: No plan found for state '{state}' of {node_id}")
        
        return selected_plans
