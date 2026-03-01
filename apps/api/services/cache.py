import json
from typing import Any

import redis.asyncio as redis


class CacheService:
    def __init__(self, redis: redis.Redis) -> None:
        self._redis = redis

    @staticmethod
    def build_key(*parts: str | None) -> str:
        """Normaliza partes em uma cache key."""
        clean = [str(p).lower().strip() if p else "all" for p in parts]
        return ":".join(clean)

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        await self._redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete_pattern(self, pattern: str) -> int:
        keys = await self._redis.keys(pattern)
        if not keys:
            return 0
        return await self._redis.delete(*keys)
