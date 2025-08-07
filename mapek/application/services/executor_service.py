import aiohttp
import asyncio
import tenacity
from pybreaker import CircuitBreaker
from mapek.infrastructure.database.repositories import NodeRepository
from mapek.logger import logger
from typing import List, Dict

class Executor:
    def __init__(self, node_repo: NodeRepository):
        self.node_repo = node_repo

    @tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_exponential(multiplier=1, min=4, max=10))
    @CircuitBreaker(fail_max=5, reset_timeout=60)
    async def execute_command(self, node_ip: str, command: dict):
        async with aiohttp.ClientSession() as session:
            try:
                url = f"http://{node_ip}/execute"
                async with session.post(url, json=command, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error(f"Execution failed for {node_ip}: {e}")
                raise

    async def execute(self, plans: List[Dict]):
        node_ips = self.node_repo.get_node_ips()
        tasks = []
        for plan in plans:
            node_id = plan['node_id']
            node_ip = node_ips.get(node_id)
            if node_ip:
                tasks.append(self.execute_command(node_ip, plan['plan']))
        return await asyncio.gather(*tasks, return_exceptions=True)
