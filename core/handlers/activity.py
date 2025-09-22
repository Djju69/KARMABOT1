"""
Activity (Loyalty) UX for Telegram bot.
- Renders screen with available activities
- Handles callbacks actv:(checkin|profile|bindcard|geocheckin)
- Calls backend API /api/loyalty/activity/claim with Bearer JWT
- Applies simple local cooldown hints (optional) to reduce spam
"""
from __future__ import annotations

import os
import time
import logging
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from ..utils.locales_v2 import get_text, translations
from ..services.profile import profile_service
from ..services.cache import cache_service
from ..keyboards.inline_v2 import get_activity_inline
from ..services.webapp_auth import issue_jwt
from ..settings import settings
from ..keyboards.reply_v2 import get_location_request_keyboard
from .basic import ensure_policy_accepted

logger = logging.getLogger(__name__)
activity_router = Router(name="activity_router")


# --- Helpers ---
_DEF_COOLDOWN = {
    "checkin": int(os.getenv("ACTIVITY_CHECKIN_COOLDOWN_SEC", "86400") or 86400),
    "profile": int(os.getenv("ACTIVITY_PROFILE_COOLDOWN_SEC", "31536000") or 31536000),  # once a year
    "bindcard": int(os.getenv("ACTIVITY_BINDCARD_COOLDOWN_SEC", "31536000") or 31536000),
    "geocheckin": int(os.getenv("ACTIVITY_GEOCHECKIN_COOLDOWN_SEC", "21600") or 21600),
}

_ENABLED = os.getenv("ACTIVITY_ENABLED", "1").lower() in {"1", "true", "yes"}


async def _cooldown_key(user_id: int, rule: str) -> str:
    return f"actv:cd:{user_id}:{rule}"


async def _is_on_cooldown(user_id: int, rule: str) -> bool:
    return (await cache_service.get(await _cooldown_key(user_id, rule))) is not None


async def _set_cooldown(user_id: int, rule: str, ttl: int) -> None:
    await cache_service.set(await _cooldown_key(user_id, rule), "1", ex=ttl)


async def _await_geo_key(user_id: int) -> str:
    return f"actv:await_geo:{user_id}"


async def _set_await_geo(user_id: int, ttl: int = 180) -> None:
    await cache_service.set(await _await_geo_key(user_id), "1", ex=ttl)


async def _is_await_geo(user_id: int) -> bool:
    return (await cache_service.get(await _await_geo_key(user_id))) is not None


def _texts(key: str) -> list[str]:
    return [t.get(key, "") for t in translations.values()]


async def render_activity(message: Message):
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    title = get_text("actv_title", lang)
    # Simple list description; detailed progress can be added later
    lines = [
        f"• {get_text('actv_checkin', lang)}",
        f"• {get_text('actv_profile', lang)}",
        f"• {get_text('actv_bindcard', lang)}",
        f"• {get_text('actv_geocheckin', lang)}",
    ]
    kb = await _build_activity_keyboard(lang, user_id)
    await message.answer(f"{title}\n\n" + "\n".join(lines), reply_markup=kb)


async def _build_activity_keyboard(lang: str, user_id: int) -> InlineKeyboardMarkup:
    async def label(key: str, rule: str, emoji: str) -> str:
        on_cd = await _is_on_cooldown(user_id, rule)
        badge = " ⏳" if on_cd else ""
        return f"{emoji} {get_text(key, lang)}{badge}"

    rows = [
        [InlineKeyboardButton(text=await label('actv_checkin', 'checkin', '🎯'), callback_data="actv:checkin")],
        [InlineKeyboardButton(text=await label('actv_profile', 'profile', '🧩'), callback_data="actv:profile")],
        [InlineKeyboardButton(text=await label('actv_bindcard', 'bindcard', '🪪'), callback_data="actv:bindcard")],
        [InlineKeyboardButton(text=await label('actv_geocheckin', 'geocheckin', '📍'), callback_data="actv:geocheckin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Entry point: open Activity screen ---
@activity_router.message(F.text.in_(_texts('actv_title')))
async def on_activity_open(message: Message):
    if not await ensure_policy_accepted(message):
        return
    if not _ENABLED:
        lang = await profile_service.get_lang(message.from_user.id)
        await message.answer(get_text('actv_rule_disabled', lang))
        return
    await render_activity(message)


# --- Callbacks ---
@activity_router.callback_query(F.data.regexp(r"^actv:(checkin|profile|bindcard|geocheckin)$"))
async def on_activity_claim(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        await callback.answer()
    except Exception:
        pass

    lang = await profile_service.get_lang(user_id)

    # Policy gate
    if not await ensure_policy_accepted(callback.message):
        return

    if not _ENABLED:
        await callback.message.answer(get_text('actv_rule_disabled', lang))
        return

    rule = callback.data.split(":", 1)[1]
    # Cooldown check (local hint; server enforces real cooldown)
    if await _is_on_cooldown(user_id, rule):
        try:
            await callback.answer(get_text('actv_cooldown', lang), show_alert=False)
        except Exception:
            await callback.message.answer(get_text('actv_cooldown', lang))
        return

    # Special flow for geocheckin: request location first
    if rule == "geocheckin":
        await _set_await_geo(user_id, ttl=180)
        await callback.message.answer(get_text('actv_send_location_prompt', lang), reply_markup=get_location_request_keyboard(lang))
        return

    # Call backend API
    base_url = (settings.webapp_qr_url or "http://localhost:8000").rstrip("/")
    url = f"{base_url}/api/loyalty/activity/claim"
    token = issue_jwt(user_id, ttl_sec=120)
    payload = {"rule_code": rule}
    # Note: geocheckin may require lat/lng — TG doesn't provide; leave empty for now
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if data.get("ok"):
                        await _set_cooldown(user_id, rule, int(_DEF_COOLDOWN.get(rule, 0)))
                        try:
                            await callback.answer(get_text('actv_claim_ok', lang), show_alert=False)
                        except Exception:
                            pass
                    else:
                        code = data.get("code") or ""
                        if code == "cooldown_active":
                            try:
                                await callback.answer(get_text('actv_cooldown', lang), show_alert=False)
                            except Exception:
                                await callback.message.answer(get_text('actv_cooldown', lang))
                            return
                        if code == "rule_disabled":
                            await callback.message.answer(get_text('actv_rule_disabled', lang))
                            return
                        # Unknown code (geo_required, out_of_coverage, etc.)
                        await callback.message.answer("ℹ️ Действие временно недоступно.")
                        return
                elif resp.status == 401:
                    await callback.message.answer("🔒 Требуется авторизация. Попробуйте /start")
                    return
                else:
                    txt = await resp.text()
                    logger.warning("activity.claim http error %s: %s", resp.status, txt)
                    await callback.message.answer("❌ Ошибка сервера. Попробуйте позже.")
                    return
    except Exception as e:
        logger.error("activity.claim request failed user=%s rule=%s err=%s", user_id, rule, e)
        await callback.message.answer("❌ Сеть недоступна. Попробуйте позже.")
        return

    # Refresh UI best-effort
    try:
        kb = await _build_activity_keyboard(lang, user_id)
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@activity_router.message(F.location)
async def on_location_for_geocheckin(message: Message):
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    if not await ensure_policy_accepted(message):
        return
    if not _ENABLED:
        return
    if not await _is_await_geo(user_id):
        return

    lat = message.location.latitude
    lng = message.location.longitude

    base_url = (settings.webapp_qr_url or "http://localhost:8000").rstrip("/")
    url = f"{base_url}/api/loyalty/activity/claim"
    token = issue_jwt(user_id, ttl_sec=120)
    payload = {"rule_code": "geocheckin", "lat": lat, "lng": lng}

    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if data.get("ok"):
                        await _set_cooldown(user_id, "geocheckin", int(_DEF_COOLDOWN.get("geocheckin", 0)))
                        await message.answer(get_text('actv_claim_ok', lang), reply_markup=None)
                    else:
                        code = data.get("code") or ""
                        if code == "cooldown_active":
                            await message.answer(get_text('actv_cooldown', lang), reply_markup=None)
                        elif code == "rule_disabled":
                            await message.answer(get_text('actv_rule_disabled', lang), reply_markup=None)
                        elif code == "geo_required":
                            await message.answer(get_text('actv_geo_required', lang), reply_markup=get_location_request_keyboard(lang))
                        elif code == "out_of_coverage":
                            await message.answer(get_text('actv_out_of_coverage', lang), reply_markup=None)
                        else:
                            await message.answer("ℹ️ Действие временно недоступно.")
                elif resp.status == 401:
                    await message.answer("🔒 Требуется авторизация. Попробуйте /start")
                else:
                    txt = await resp.text()
                    logger.warning("activity.geocheckin http error %s: %s", resp.status, txt)
                    await message.answer("❌ Ошибка сервера. Попробуйте позже.")
    except Exception as e:
        logger.error("geocheckin request failed user=%s err=%s", user_id, e)
        await message.answer("❌ Сеть недоступна. Попробуйте позже.")


def get_activity_router() -> Router:
    return activity_router
