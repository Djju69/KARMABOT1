from __future__ import annotations
import os
from typing import Optional

try:
    # redis>=4.2
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

class BaseCacheService:
    async def get(self, key: str): 
        ...
    async def set(self, key: str, value, ex: int | None = None): 
        ...
    async def close(self): 
        ...

class NullCacheService(BaseCacheService):
    def __init__(self) -> None:
        self._mem: dict[str, str] = {}
    async def get(self, key: str):
        return self._mem.get(key)
    async def set(self, key: str, value, ex: int | None = None):
        self._mem[key] = value
    async def close(self): 
        ...

class RedisCacheService(BaseCacheService):
    def __init__(self, url: str) -> None:
        self._url = url
        self._r = None
    async def connect(self):
        if aioredis is None:
            raise RuntimeError("redis library not installed")
        self._r = aioredis.from_url(self._url, decode_responses=True)
        await self._r.ping()
    async def get(self, key: str):
        if not self._r: 
            return None
        return await self._r.get(key)
    async def set(self, key: str, value, ex: int | None = None):
        if self._r:
            await self._r.set(key, value, ex=ex)
    async def close(self):
        if self._r:
            await self._r.close()

# -------- lazy singleton --------
_cache_singleton: Optional[BaseCacheService] = None

async def init_cache_service(redis_url: str | None = None) -> BaseCacheService:
    """Call once at app/bot startup."""
    global _cache_singleton
    if _cache_singleton:
        return _cache_singleton

    url = redis_url or os.getenv("REDIS_URL") or os.getenv("REDIS_TLS_URL")
    if url:
        try:
            svc = RedisCacheService(url)
            await svc.connect()
            print(f"[cache] Using Redis cache at {url}", flush=True)
            _cache_singleton = svc
            return svc
        except Exception as e:
            print(f"[cache] Redis unavailable ({e}); falling back to NullCacheService", flush=True)

    _cache_singleton = NullCacheService()
    print("[cache] Using NullCacheService", flush=True)
    return _cache_singleton

def get_cache_service() -> BaseCacheService:
    """Non-async accessor; returns current singleton or NullCacheService."""
    return _cache_singleton or NullCacheService()
