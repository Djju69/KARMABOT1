"""
Admins service: dynamic admin list with super admin, optional Redis backend, in-memory fallback.
"""
from __future__ import annotations
from typing import Optional, Set, List, Any
import time
import os
import logging

try:
    from redis.asyncio import Redis as AsyncRedis  # type: ignore
except Exception:  # pragma: no cover
    AsyncRedis = None  # type: ignore

from ..settings import settings


class AdminsService:
    KEY_SET = "admins:set"
    RATE_WINDOW_SEC = 10
    MAX_ADMINS = 5  # excluding super admin

    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or ""
        self._redis: Optional[AsyncRedis] = None
        self._mem: Set[int] = set()
        self._rate: dict[int, float] = {}

    async def connect(self):
        if AsyncRedis and self._redis_url:
            try:
                self._redis = AsyncRedis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        # Seed initial admins from ENV (optional, non-breaking)
        try:
            raw = os.getenv("ADMIN_TG_IDS", "").strip()
            if raw:
                # Support comma or whitespace separated list
                parts = [p for chunk in raw.split(",") for p in chunk.strip().split()] if "," in raw else raw.split()
                ids: List[int] = []
                for p in parts:
                    try:
                        ids.append(int(p))
                    except Exception:
                        continue
                su = int(settings.bots.admin_id)
                seed = [i for i in ids if i and i != su]
                if seed:
                    if self._redis:
                        try:
                            if seed:
                                await self._redis.sadd(self.KEY_SET, *seed)
                        except Exception:
                            # Fallback to memory if Redis write fails
                            self._mem.update(seed)
                    else:
                        self._mem.update(seed)
        except Exception as e:
            logging.getLogger(__name__).warning(f"AdminsService seed from ENV failed: {e}")
        return self

    async def disconnect(self) -> None:
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
            finally:
                self._redis = None

    def _ensure_super(self, lst: List[int]) -> List[int]:
        su = int(settings.bots.admin_id)
        if su not in lst:
            return [su] + lst
        return lst

    async def is_admin(self, user_id: int) -> bool:
        user_id = int(user_id)
        if user_id == int(settings.bots.admin_id):
            return True
        if self._redis:
            try:
                return bool(await self._redis.sismember(self.KEY_SET, user_id))
            except Exception:
                pass
        return user_id in self._mem

    async def list_admins(self) -> List[int]:
        lst: List[int] = []
        if self._redis:
            try:
                members = await self._redis.smembers(self.KEY_SET)
                lst = [int(x) for x in members]
            except Exception:
                lst = list(self._mem)
        else:
            lst = list(self._mem)
        lst.sort()
        return self._ensure_super(lst)

    def _check_rate(self, actor_id: int) -> bool:
        now = time.time()
        last = self._rate.get(actor_id, 0.0)
        if now - last < self.RATE_WINDOW_SEC:
            return False
        self._rate[actor_id] = now
        return True

    async def add_admin(self, actor_id: int, new_admin_id: int) -> tuple[bool, str]:
        actor_id = int(actor_id)
        new_admin_id = int(new_admin_id)
        if actor_id != int(settings.bots.admin_id):
            return False, "❌ Только главный админ может управлять списком админов."
        if not self._check_rate(actor_id):
            return False, "⏳ Слишком часто. Попробуйте позже."
        if new_admin_id == int(settings.bots.admin_id):
            return False, "ℹ️ Главный админ уже имеет все права."
        # Check count limit
        current = await self.list_admins()
        # exclude super
        others = [x for x in current if x != int(settings.bots.admin_id)]
        if new_admin_id in others:
            return True, "✅ Пользователь уже является админом."
        if len(others) >= self.MAX_ADMINS:
            return False, f"🚦 Достигнут лимит админов: {self.MAX_ADMINS}."
        try:
            if self._redis:
                await self._redis.sadd(self.KEY_SET, new_admin_id)
            else:
                self._mem.add(new_admin_id)
            return True, "✅ Админ добавлен."
        except Exception:
            return False, "❌ Ошибка при добавлении админа."

    async def remove_admin(self, actor_id: int, admin_id: int) -> tuple[bool, str]:
        actor_id = int(actor_id)
        admin_id = int(admin_id)
        if actor_id != int(settings.bots.admin_id):
            return False, "❌ Только главный админ может управлять списком админов."
        if not self._check_rate(actor_id):
            return False, "⏳ Слишком часто. Попробуйте позже."
        if admin_id == int(settings.bots.admin_id):
            return False, "🛡 Нельзя удалить главного админа."
        try:
            if self._redis:
                await self._redis.srem(self.KEY_SET, admin_id)
            else:
                self._mem.discard(admin_id)
            return True, "✅ Админ удалён."
        except Exception:
            return False, "❌ Ошибка при удалении админа."


def _get_redis_url() -> Optional[str]:
    """Safely get Redis URL from various sources with fallbacks."""
    return (
        os.getenv("REDIS_URL")
        or getattr(settings, "redis_url", None)
        or getattr(getattr(settings, "cache", None), "redis_url", None)
        or getattr(getattr(settings, "database", None), "redis_url", None)
    )

# Initialize with safe fallback
try:
    admins_service = AdminsService(redis_url=_get_redis_url())
except Exception as e:
    logging.warning(f"[admins] fallback to in-memory; reason: {e}")
    admins_service = AdminsService(redis_url=None)
