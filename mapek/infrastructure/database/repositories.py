from mapek.config.database import database_transaction
from typing import Optional, Tuple, List, Dict

class ThresholdRepository:
    def get_threshold(self, parameter: str) -> Optional[Tuple[float, float]]:
        with database_transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT min_value, max_value FROM thresholds WHERE parameter = %s", (parameter,))
            return cur.fetchone()

class PlanRepository:
    def get_plan(self, state: str = None, plan_code: str = None) -> Optional[Dict]:
        with database_transaction() as conn:
            cur = conn.cursor()
            if plan_code:
                cur.execute("SELECT * FROM plan WHERE plan_code = %s", (plan_code,))
            elif state:
                cur.execute("SELECT * FROM plan WHERE state = %s", (state,))
            else:
                cur.execute("SELECT * FROM plan LIMIT 1")
            return cur.fetchone()

class NodeRepository:
    def get_node_ips(self) -> Dict[str, str]:
        with database_transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id, ip_address FROM nodes")
            return {row[0]: row[1] for row in cur.fetchall()}

    def get_node_ids(self) -> List[str]:
        with database_transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT node_id FROM nodes")
            return [row[0] for row in cur.fetchall()]
