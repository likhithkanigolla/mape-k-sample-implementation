from mapek.config.settings import config
from mapek.config.database import db_pool
from mapek.infrastructure.database.repositories import ThresholdRepository, PlanRepository, NodeRepository

class MAPEKContainer:
    def __init__(self):
        self.db_pool = db_pool
        self.threshold_repo = ThresholdRepository()
        self.plan_repo = PlanRepository()
        self.node_repo = NodeRepository()
        # Analyzer, Planner, Executor, Monitor will be injected below
