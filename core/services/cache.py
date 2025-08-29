from __future__ import annotations

import os
from typing import Optional, Union, Any

try:
    from redis.asyncio import Redis, from_url as redis_from_url
except Exception:  # на случай отсутствия пакета — бот хотя бы не упадёт
    Redis = None
    def redis_from_url(*args, **kwargs):
        return None


class BaseCacheService:
    async def connect(self) -> None:
        """Устанавливает подключение к Redis (не падает, если Redis недоступен)."""
        pass

    async def close(self) -> None:
        """Закрывает соединение с Redis."""
        pass

    async def get(self, key: str) -> Optional[str]:
        return None

    async def set(self, key: str, value: str, ttl: Union[int, None] = None) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None


class NullCacheService(BaseCacheService):
    """Заглушка без Redis — совместимая по интерфейсу."""
    async def connect(self) -> None:
        return

    async def close(self) -> None:
        return

    async def get(self, key: str) -> Optional[str]:
        return None

    async def set(self, key: str, value: str, ttl: Union[int, None] = None) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None


class CacheService(BaseCacheService):
    def __init__(self, url: str):
        self._redis_url = url
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Устанавливает подключение к Redis (не падает, если Redis недоступен)."""
        if not self._redis_url or redis_from_url is None:
            return
        self._client = redis_from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        try:
            await self._client.ping()
        except Exception:
            # если не получилось — работаем без Redis
            self._client = None

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            finally:
                self._client = None

    async def get(self, key: str) -> Optional[str]:
        if self._client:
            return await self._client.get(key)
        return None

    async def set(self, key: str, value: str, ttl: Union[int, None] = None) -> None:
        if self._client:
            await self._client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        if self._client:
            await self._client.delete(key)


def _resolve_redis_url() -> Optional[str]:
    """Resolve Redis URL from environment variables."""
    return (os.getenv("REDIS_URL") or os.getenv("CACHE_URL") or "").strip() or None


_cache_singleton: Optional[BaseCacheService] = None


async def get_cache_service() -> BaseCacheService:
    """Get or create the cache service instance and ensure it's connected."""
    global _cache_singleton
    if _cache_singleton is not None:
        return _cache_singleton

    redis_url = _resolve_redis_url()
    if redis_url and redis_from_url is not None:
        _cache_singleton = CacheService(redis_url)
    else:
        _cache_singleton = NullCacheService()
    
    # Ensure the service is connected
    await _cache_singleton.connect()
    return _cache_singleton


# For backward compatibility
# Note: This will create a new instance on import, which is not ideal
# but maintained for backward compatibility
import asyncio

cache_service = asyncio.get_event_loop().run_until_complete(get_cache_service())
