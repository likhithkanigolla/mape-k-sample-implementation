from mapek.infrastructure.cache.redis_client import RedisClient
from mapek.infrastructure.database.repositories import ThresholdRepository
import json

class CachedThresholdRepository:
    def __init__(self, redis_client=None, db_repo=None):
        self.redis = redis_client or RedisClient()
        self.db_repo = db_repo or ThresholdRepository()

    def get_threshold(self, parameter: str):
        cache_key = f"threshold:{parameter}"
        cached = self.redis.get(cache_key)
        if cached:
            return cached
        threshold = self.db_repo.get_threshold(parameter)
        self.redis.setex(cache_key, 300, threshold)  # 5min TTL
        return threshold
