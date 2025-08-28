from __future__ import annotations

from asyncio import create_task, sleep, Lock
import logging
from typing import Optional

try:
    from redis.asyncio import Redis as AsyncRedis  # type: ignore
except Exception:  # optional dependency
    AsyncRedis = None  # type: ignore

from ..settings import settings
from ..utils.telemetry import log_event
try:
    from ..utils.metrics import AUTHME_ENTRIES, AUTHME_INVALIDATIONS
except Exception:
    AUTHME_ENTRIES = None
    AUTHME_INVALIDATIONS = None

logger = logging.getLogger(__name__)


class CacheService:
    """Thin async cache wrapper with optional Redis backend.
    Non-breaking: if REDIS_URL is empty or aioredis missing, becomes no-op/in-memory.
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url or ""
        self._redis: Optional[AsyncRedis] = None
        self._mem = {}  # fallback
        self._lock = Lock()

    async def connect(self):
        if self._redis_url and AsyncRedis:
            try:
                self._redis = AsyncRedis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
                await self._redis.ping()
                logger.info("✅ CacheService connected to Redis")
            except Exception as e:
                logger.warning(f"CacheService: Redis unavailable, fallback to memory: {e}")
        else:
            logger.info("⚠️ CacheService running in memory mode (no REDIS_URL or redis.asyncio)")

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
                    create_task(log_event("cache_get", backend="redis", key=key, hit=bool(val)))
                except Exception:
                    pass
                return val
            except Exception as e:
                logger.warning(f"CacheService.get redis error: {e}")
        async with self._lock:
            val = self._mem.get(key)
            try:
                create_task(log_event("cache_get", backend="memory", key=key, hit=bool(val)))
            except Exception:
                pass
            return val

    async def set(self, key: str, value: str, ttl_sec: int = 0, **kwargs):
        """Set cache value with TTL.
        Backward/compat helpers:
          - supports Redis-like kwargs: ex=seconds or ttl=seconds
        """
        # Resolve ttl from kwargs if provided as Redis-style
        if not ttl_sec:
            if "ex" in kwargs and kwargs["ex"] is not None:
                try:
                    ttl_sec = int(kwargs["ex"]) or 0
                except Exception:
                    ttl_sec = 0
            elif "ttl" in kwargs and kwargs["ttl"] is not None:
                try:
                    ttl_sec = int(kwargs["ttl"]) or 0
                except Exception:
                    ttl_sec = 0

        if self._redis:
            try:
                await self._redis.set(key, value, ex=(ttl_sec or None))
                try:
                    create_task(log_event("cache_set", backend="redis", key=key, ttl=ttl_sec))
                except Exception:
                    pass
                return
            except Exception as e:
                logger.warning(f"CacheService.set redis error: {e}")
        async with self._lock:
            self._mem[key] = value
            # naive TTL: schedule deletion only if positive
            if ttl_sec and ttl_sec > 0:
                create_task(self._expire_mem(key, ttl_sec))
            # gauge update for memory mode
            try:
                if AUTHME_ENTRIES is not None and key.startswith("authme:"):
                    AUTHME_ENTRIES.set(sum(1 for k in self._mem.keys() if k.startswith("authme:")))
            except Exception:
                pass
            try:
                create_task(log_event("cache_set", backend="memory", key=key, ttl=ttl_sec))
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
                    create_task(log_event("cache_delete_mask", backend="redis", mask=mask, deleted=deleted))
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
            # metrics: invalidations + gauge
            try:
                if AUTHME_INVALIDATIONS is not None and (mask.startswith("authme:") or "authme:" in mask):
                    AUTHME_INVALIDATIONS.labels("mask").inc(len(to_del))
                if AUTHME_ENTRIES is not None:
                    AUTHME_ENTRIES.set(sum(1 for k in self._mem.keys() if k.startswith("authme:")))
            except Exception:
                pass
            logger.info(f"🧹 CacheService(memory) deleted {len(to_del)} keys by mask: {mask}")
            try:
                create_task(log_event("cache_delete_mask", backend="memory", mask=mask, deleted=len(to_del)))
            except Exception:
                pass

    async def invalidate_authme(self, user_id: int, reason: str = "manual"):
        """Invalidate a specific /auth/me cache entry and record reasoned metrics.
        Non-breaking: works in both Redis and memory modes; logs best-effort.
        """
        key = f"authme:{user_id}"
        deleted = 0
        if self._redis:
            try:
                deleted = await self._redis.delete(key) or 0
                try:
                    if AUTHME_INVALIDATIONS is not None:
                        AUTHME_INVALIDATIONS.labels(reason).inc(max(1, deleted))
                except Exception:
                    pass
                try:
                    create_task(log_event("authme_invalidate", backend="redis", key=key, reason=reason, deleted=deleted))
                except Exception:
                    pass
                return
            except Exception as e:
                logger.warning(f"CacheService.invalidate_authme redis error: {e}")
        # memory fallback
        async with self._lock:
            if key in self._mem:
                self._mem.pop(key, None)
                deleted = 1
            # metrics: invalidations + gauge
            try:
                if AUTHME_INVALIDATIONS is not None:
                    AUTHME_INVALIDATIONS.labels(reason).inc(max(1, deleted))
                if AUTHME_ENTRIES is not None:
                    AUTHME_ENTRIES.set(sum(1 for k in self._mem.keys() if k.startswith("authme:")))
            except Exception:
                pass
            try:
                create_task(log_event("authme_invalidate", backend="memory", key=key, reason=reason, deleted=deleted))
            except Exception:
                pass

    async def _expire_mem(self, key: str, ttl: int):
        await sleep(max(0, ttl))
        async with self._lock:
            self._mem.pop(key, None)
            try:
                if AUTHME_ENTRIES is not None and key.startswith("authme:"):
                    AUTHME_ENTRIES.set(sum(1 for k in self._mem.keys() if k.startswith("authme:")))
            except Exception:
                pass


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


# --- cache bootstrap (lazy & safe) ---
import os

def _resolve_redis_url() -> str | None:
    # сначала пробуем settings.redis_url
    url = getattr(settings, "redis_url", None)
    # пробуем settings.database.redis_url (если вдруг есть)
    db = getattr(settings, "database", None)
    if not url and db and hasattr(db, "redis_url"):
        url = getattr(db, "redis_url")
    # окружение как последний приоритет
    if not url:
        url = os.getenv("REDIS_URL")
    return (url or "").strip() or None

_cache_singleton: "BaseCacheService | None" = None  # строковая аннотация → не ломает импорт

def get_cache_service() -> BaseCacheService:
    global _cache_singleton
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
