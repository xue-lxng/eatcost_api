from typing import Any

from config import REDIS_URL
from core.caching.in_redis import AsyncRedisCache

redis = AsyncRedisCache(REDIS_URL)


def get_redis() -> Any:
    return redis
