from __future__ import annotations
import logging

from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from ..services.profile import profile_service
from ..settings import settings

logger = logging.getLogger(__name__)


class LocaleMiddleware(BaseMiddleware):
    """Injects user's language into handler data as 'lang'.
    Relies on profile_service; falls back to settings.default_lang.
    """

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery | Update,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
        # Fallback: keep existing
        default_lang = getattr(settings, 'default_lang', 'ru')
        lang = default_lang
        if user_id:
            try:
                lang = await profile_service.get_lang(user_id, default=default_lang)
            except Exception:
                lang = default_lang
        logger.info(f"LocaleMiddleware: Set lang='{lang}' for user_id={user_id}")
        data["lang"] = lang
        # Also provide selected city_id if any
        try:
            city_id = await profile_service.get_city_id(user_id) if user_id else None
        except Exception:
            city_id = None
        data["city_id"] = city_id
        return await handler(event, data)
