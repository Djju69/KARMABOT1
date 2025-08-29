from __future__ import annotations
import os
import asyncio
from typing import Optional, Any

try:
    # redis>=4.2
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

class BaseCacheService:
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None: ...
    async def delete(self, key: str) -> int: ...
    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, ttl: int) -> bool: ...
    async def ping(self) -> bool: ...

class _MemoryCache(BaseCacheService):
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        self._store[key] = value
        if ex:
            loop = asyncio.get_running_loop()
            loop.call_later(ex, lambda: self._store.pop(key, None))

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    async def incr(self, key: str) -> int:
        v = int(self._store.get(key, 0)) + 1
        self._store[key] = v
        return v

    async def expire(self, key: str, ttl: int) -> bool:
        if key not in self._store:
            return False
        loop = asyncio.get_running_loop()
        loop.call_later(ttl, lambda: self._store.pop(key, None))
        return True

    async def ping(self) -> bool:
        return True

class _RedisCache(BaseCacheService):
    def __init__(self, client: "aioredis.Redis") -> None:
        self.client = client

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> int:
        return await self.client.delete(key)

    async def incr(self, key: str) -> int:
        return await self.client.incr(key)

    async def expire(self, key: str, ttl: int) -> bool:
        return await self.client.expire(key, ttl)

    async def ping(self) -> bool:
        return await self.client.ping()

_instance: Optional[BaseCacheService] = None
_lock = asyncio.Lock()

async def get_cache_service() -> BaseCacheService:
    """Ленивая инициализация: без синхронного await при импорте."""
    global _instance
    if _instance is None:
        async with _lock:
            if _instance is None:
                url = (
                    os.getenv("REDIS_URL")
                    or os.getenv("UPSTASH_REDIS_URL")
                    or os.getenv("KV_URL")
                )
                if aioredis and url:
                    client = aioredis.from_url(url, decode_responses=True)
                    _instance = _RedisCache(client)
                else:
                    _instance = _MemoryCache()
    return _instance

class _CacheFacade(BaseCacheService):
    """Фасад для обратной совместимости: тот же интерфейс, что и раньше.
    Внутри каждый вызов лениво берёт реальный сервис.
    """
    async def _svc(self) -> BaseCacheService:
        return await get_cache_service()

    async def get(self, key: str) -> Optional[str]:
        return await (await self._svc()).get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        return await (await self._svc()).set(key, value, ex=ex)

    async def delete(self, key: str) -> int:
        return await (await self._svc()).delete(key)

    async def incr(self, key: str) -> int:
        return await (await self._svc()).incr(key)

    async def expire(self, key: str, ttl: int) -> bool:
        return await (await self._svc()).expire(key, ttl)

    async def ping(self) -> bool:
        return await (await self._svc()).ping()

# Экспорт как раньше: теперь импорт `cache_service` снова работает
cache_service: BaseCacheService = _CacheFacade()

__all__ = ["get_cache_service", "cache_service", "BaseCacheService"]
