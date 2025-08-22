"""
Profile service with Redis (async) and in-memory fallback.
Stores per-user preferences: language, city_id, policy_accepted.
"""
from __future__ import annotations

from typing import Optional, Any
import json

try:
    # redis>=4.2 provides asyncio API
    from redis.asyncio import Redis as AsyncRedis  # type: ignore
except Exception:  # pragma: no cover
    AsyncRedis = None  # type: ignore


class ProfileService:
    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or ""
        self._redis: Optional[AsyncRedis] = None
        # In-memory fallback
        self._mem: dict[int, dict[str, Any]] = {}

    async def clear_cache(self) -> None:
        """Clear cached profiles in memory and Redis (only profile:* keys)."""
        # Clear in-memory cache
        self._mem.clear()
        # Clear Redis keys if available
        if self._redis:
            try:
                async for key in self._redis.scan_iter("profile:*"):
                    await self._redis.delete(key)
            except Exception:
                # Fail silently to avoid breaking admin command in absence of permissions
                pass

    async def connect(self):
        if AsyncRedis and self._redis_url:
            try:
                self._redis = AsyncRedis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
                # ping to validate
                await self._redis.ping()
            except Exception:
                # fallback to memory
                self._redis = None
        return self

    def _key(self, user_id: int) -> str:
        return f"profile:{user_id}"

    async def _get(self, user_id: int) -> dict:
        if self._redis:
            raw = await self._redis.get(self._key(user_id))
            return json.loads(raw) if raw else {}
        return self._mem.get(user_id, {})

    async def _set(self, user_id: int, data: dict) -> None:
        if self._redis:
            await self._redis.set(self._key(user_id), json.dumps(data))
        else:
            self._mem[user_id] = data

    async def get_lang(self, user_id: int, default: str = "ru") -> str:
        data = await self._get(user_id)
        return str(data.get("lang", default))

    async def set_lang(self, user_id: int, lang: str) -> None:
        data = await self._get(user_id)
        data["lang"] = lang
        await self._set(user_id, data)

    async def has_lang(self, user_id: int) -> bool:
        """Return True if user has explicitly selected language."""
        data = await self._get(user_id)
        return "lang" in data

    async def get_city_id(self, user_id: int) -> Optional[int]:
        data = await self._get(user_id)
        v = data.get("city_id")
        return int(v) if v is not None else None

    async def set_city_id(self, user_id: int, city_id: int) -> None:
        data = await self._get(user_id)
        data["city_id"] = int(city_id)
        await self._set(user_id, data)

    async def is_policy_accepted(self, user_id: int) -> bool:
        data = await self._get(user_id)
        return bool(data.get("policy_accepted", False))

    async def set_policy_accepted(self, user_id: int, accepted: bool = True) -> None:
        data = await self._get(user_id)
        data["policy_accepted"] = bool(accepted)
        await self._set(user_id, data)


# Singleton provider
profile_service = ProfileService()
