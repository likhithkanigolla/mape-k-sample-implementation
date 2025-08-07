try:
    import redis
except ImportError:
    redis = None
import json

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        if redis:
            self.client = redis.Redis(host=host, port=port, db=db)
        else:
            self.client = None

    def get(self, key):
        if not self.client:
            return None
        val = self.client.get(key)
        return json.loads(val) if val else None

    def setex(self, key, ttl, value):
        if not self.client:
            return None
        self.client.setex(key, ttl, json.dumps(value))
