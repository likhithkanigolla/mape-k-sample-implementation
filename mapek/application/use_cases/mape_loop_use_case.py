import asyncio
from mapek.application.services.monitor_service import Monitor
from mapek.application.services.analyzer_service import Analyzer
from mapek.application.services.planner_service import Planner
from mapek.application.services.executor_service import Executor
from mapek.application.services.container import MAPEKContainer
from mapek.logger import logger
from mapek.config.settings import config


class AsyncMAPEK:
    def __init__(self):
        self.container = MAPEKContainer()
        self.monitor = Monitor(self.container.node_repo)
        self.analyzer = Analyzer(self.container.threshold_repo)
        self.planner = Planner(self.container.plan_repo)
        self.executor = Executor(self.container.node_repo)

    async def run_loop(self):
        while True:
            try:
                logger.info("[MAPE-K] Monitoring sensors...")
                sensor_data = self.monitor.read_sensors()
                logger.info(f"[MAPE-K] Sensor data: {sensor_data}")

                logger.info("[MAPE-K] Analyzing data...")
                analysis = self.analyzer.analyze(sensor_data)
                logger.info(f"[MAPE-K] Analysis result: {analysis}")

                logger.info("[MAPE-K] Planning actions...")
                plans = self.planner.select_plans(analysis)
                logger.info(f"[MAPE-K] Plans selected: {plans}")

                logger.info("[MAPE-K] Executing plans...")
                await self.executor.execute(plans)
                logger.info("[MAPE-K] Execution complete.")

                await asyncio.sleep(config.loop_interval)
            except Exception as e:
                logger.error(f"MAPE-K loop error: {e}")
                await asyncio.sleep(30)


if __name__ == "__main__":
    loop = AsyncMAPEK()
    import asyncio
    asyncio.run(loop.run_loop())
