from __future__ import annotations

import os
from typing import Optional

try:
    import redis.asyncio as redis
except Exception:
    redis = None


class BaseCacheService:
    async def get(self, key: str) -> Optional[str]:
        return None

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        return None


class NullCacheService(BaseCacheService):
    pass


class CacheService(BaseCacheService):
    def __init__(self, url: str):
        if not redis:
            raise RuntimeError("redis library is not available")
        self._r = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._r.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if ttl:
            await self._r.set(key, value, ex=ttl)
        else:
            await self._r.set(key, value)


_cache_singleton: BaseCacheService | None = None


def get_cache_service() -> BaseCacheService:
    global _cache_singleton
    if _cache_singleton is not None:
        return _cache_singleton

    redis_url = os.getenv("REDIS_URL") or os.getenv("CACHE_URL")
    if redis_url and redis:
        try:
            _cache_singleton = CacheService(redis_url)
            return _cache_singleton
        except Exception:
            pass

    _cache_singleton = NullCacheService()
    return _cache_singleton


# For backward compatibility
cache_service = get_cache_service()    global _cache_singleton
    if _cache_singleton is not None:
        return _cache_singleton

    redis_url = _resolve_redis_url()
    if not redis_url:
        print("[cache] redis_url not configured; using NullCacheService")
        _cache_singleton = NullCacheService()
        return _cache_singleton

    try:
        _cache_singleton = CacheService(redis_url)
        print(f"[cache] Redis enabled: {redis_url}")
    except Exception as e:
        print(f"[cache] Redis init failed ({e}); falling back to NullCacheService")
        _cache_singleton = NullCacheService()
    return _cache_singleton

# совместимость со старым импортом
cache_service = get_cache_service()
