import asyncio
import logging
from typing import Optional

try:
    import aioredis  # type: ignore
except Exception:  # optional dependency
    aioredis = None

from ..settings import settings
from ..utils.telemetry import log_event

logger = logging.getLogger(__name__)


class CacheService:
    """Thin async cache wrapper with optional Redis backend.
    Non-breaking: if REDIS_URL is empty or aioredis missing, becomes no-op/in-memory.
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url or ""
        self._redis = None
        self._mem = {}  # fallback
        self._lock = asyncio.Lock()

    async def connect(self):
        if self._redis_url and aioredis:
            try:
                self._redis = await aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
                logger.info("✅ CacheService connected to Redis")
            except Exception as e:
                logger.warning(f"CacheService: Redis unavailable, fallback to memory: {e}")
        else:
            logger.info("⚠️ CacheService running in memory mode (no REDIS_URL or aioredis)")

    async def close(self):
        try:
            if self._redis:
                await self._redis.close()
        except Exception:
            pass

    async def get(self, key: str) -> Optional[str]:
        if self._redis:
            try:
                val = await self._redis.get(key)
                try:
                    import asyncio; asyncio.create_task(log_event("cache_get", backend="redis", key=key, hit=bool(val)))
                except Exception:
                    pass
                return val
            except Exception as e:
                logger.warning(f"CacheService.get redis error: {e}")
        async with self._lock:
            val = self._mem.get(key)
            try:
                import asyncio; asyncio.create_task(log_event("cache_get", backend="memory", key=key, hit=bool(val)))
            except Exception:
                pass
            return val

    async def set(self, key: str, value: str, ttl_sec: int):
        if self._redis:
            try:
                await self._redis.set(key, value, ex=ttl_sec)
                try:
                    import asyncio; asyncio.create_task(log_event("cache_set", backend="redis", key=key, ttl=ttl_sec))
                except Exception:
                    pass
                return
            except Exception as e:
                logger.warning(f"CacheService.set redis error: {e}")
        async with self._lock:
            self._mem[key] = value
            # naive TTL: schedule deletion
            asyncio.create_task(self._expire_mem(key, ttl_sec))
            try:
                import asyncio; asyncio.create_task(log_event("cache_set", backend="memory", key=key, ttl=ttl_sec))
            except Exception:
                pass

    async def delete_by_mask(self, mask: str):
        """Delete keys by glob-style mask. In memory mode - linear scan.
        Example mask: 'catalog:1:restaurants:*'
        """
        if self._redis:
            try:
                # Use async scan to avoid blocking
                deleted = 0
                async for key in self._redis.scan_iter(match=mask):
                    await self._redis.delete(key)
                    deleted += 1
                logger.info(f"🧹 CacheService deleted keys by mask: {mask} (count={deleted})")
                try:
                    import asyncio; asyncio.create_task(log_event("cache_delete_mask", backend="redis", mask=mask, deleted=deleted))
                except Exception:
                    pass
                return
            except Exception as e:
                logger.warning(f"CacheService.delete_by_mask redis error: {e}")
        # memory fallback
        async with self._lock:
            to_del = [k for k in self._mem.keys() if _match_glob(k, mask)]
            for k in to_del:
                self._mem.pop(k, None)
            logger.info(f"🧹 CacheService(memory) deleted {len(to_del)} keys by mask: {mask}")
            try:
                import asyncio; asyncio.create_task(log_event("cache_delete_mask", backend="memory", mask=mask, deleted=len(to_del)))
            except Exception:
                pass

    async def _expire_mem(self, key: str, ttl: int):
        await asyncio.sleep(max(0, ttl))
        async with self._lock:
            self._mem.pop(key, None)


def _match_glob(text: str, pattern: str) -> bool:
    # very small glob: '*' only
    if pattern == '*':
        return True
    parts = pattern.split('*')
    if len(parts) == 1:
        return text == pattern
    # must contain all parts in order
    pos = 0
    for i, p in enumerate(parts):
        if not p:
            continue
        idx = text.find(p, pos)
        if idx < 0:
            return False
        pos = idx + len(p)
    # if pattern does not end with '*', ensure last part aligns to end
    if not pattern.endswith('*') and not text.endswith(parts[-1]):
        return False
    return True


cache_service = CacheService(settings.database.redis_url)
