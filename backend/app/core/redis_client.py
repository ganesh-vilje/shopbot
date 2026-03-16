import redis
from app.core.config import settings
from datetime import datetime, timedelta

_client: redis.Redis | None = None


class MockRedis:
    """Mock Redis client for development without Redis server"""
    def __init__(self):
        self._store = {}
    
    def setex(self, key: str, time: int, value: str) -> None:
        """Set key with expiration time (in seconds)"""
        self._store[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=time)
        }
    
    def get(self, key: str) -> str | None:
        """Get value by key"""
        if key in self._store:
            item = self._store[key]
            if item["expires_at"] > datetime.now():
                return item["value"]
            else:
                del self._store[key]
        return None
    
    def incr(self, key: str) -> int:
        """Increment counter"""
        current = self.get(key)
        value = int(current) if current else 0
        self._store[key] = {"value": str(value + 1), "expires_at": datetime.now() + timedelta(hours=24)}
        return value + 1
    
    def expire(self, key: str, time: int) -> None:
        """Set expiration for a key"""
        if key in self._store:
            self._store[key]["expires_at"] = datetime.now() + timedelta(seconds=time)


def get_redis() -> redis.Redis | MockRedis:
    global _client
    if _client is None:
        try:
            _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _client.ping()  # Test connection
        except Exception as e:
            print(f"Redis connection failed: {e}. Using MockRedis for development.")
            _client = MockRedis()
    return _client
