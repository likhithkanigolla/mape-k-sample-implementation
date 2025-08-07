from mapek.infrastructure.database.repositories import PlanRepository
from typing import List, Dict

class Planner:
    def __init__(self, plan_repo: PlanRepository):
        self.plan_repo = plan_repo

    def select_plans(self, analysis_results: List[Dict]) -> List[Dict]:
        plans = []
        for result in analysis_results:
            state = result.get('state')
            plan_code = result.get('plan_code')
            plan = self.plan_repo.get_plan(state, plan_code)
            if plan:
                plans.append({"node_id": result['node_id'], "plan": plan})
        return plans
