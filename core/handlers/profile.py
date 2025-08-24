"""
Inline personal cabinet: keyboard + callbacks per spec.
Minimal runnable stubs for complex flows (QR spend/report/lang/bind).
"""
import os
import re
import time
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from ..database.db_v2 import db_v2
from ..utils.locales_v2 import get_text
from ..services.profile import profile_service
from ..services.cache import cache_service
from ..services.loyalty import loyalty_service
from ..services.cards import card_service

profile_router = Router()


def _notify_key(user_id: int) -> str:
    return f"notify:{user_id}"


def _report_rl_key(user_id: int) -> str:
    return f"report_rl:{user_id}"


async def _is_notify_on(user_id: int) -> bool:
    v = await cache_service.get(_notify_key(user_id))
    return v != "off"


def build_profile_kb(lang: str, notify_on: bool) -> InlineKeyboardMarkup:
    btn_notify = get_text('btn_notify_on' if notify_on else 'btn_notify_off', lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text('btn.points', lang), callback_data="profile:points")],
        [InlineKeyboardButton(text=get_text('btn.spend', lang), callback_data="wallet:spend")],
        [InlineKeyboardButton(text=get_text('btn.history', lang), callback_data="profile:history:1")],
        [InlineKeyboardButton(text=get_text('btn.report', lang), callback_data="profile:report_menu")],
        [InlineKeyboardButton(text=get_text('btn.card.bind', lang), callback_data="card:bind")],
        [InlineKeyboardButton(text=btn_notify, callback_data="profile:notify:toggle")],
        [InlineKeyboardButton(text=get_text('btn.lang', lang), callback_data="profile:lang")],
        [InlineKeyboardButton(text=get_text('btn.partner.become', lang), callback_data="partner:become")],
    ])


async def render_profile(message_or_cb, *, as_edit: bool = False):
    user_id = message_or_cb.from_user.id
    lang = await profile_service.get_lang(user_id)
    notify_on = await _is_notify_on(user_id)
    kb = build_profile_kb(lang, notify_on)
    text = get_text('profile_main', lang)
    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(text, reply_markup=kb)
    else:
        await message_or_cb.message.edit_text(text, reply_markup=kb)


# Callbacks per spec
@profile_router.callback_query(F.data == "profile:points")
async def cb_points(c: CallbackQuery):
    await c.answer()
    # Placeholder points view
    await render_profile(c, as_edit=True)


@profile_router.callback_query(F.data == "wallet:spend")
async def cb_wallet_spend(c: CallbackQuery):
    await c.answer()
    lang = await profile_service.get_lang(c.from_user.id)
    try:
        min_pts = int(os.getenv('LOYALTY_MIN_SPEND_PTS', '100'))
    except Exception:
        min_pts = 100
    # Fetch balance from wallet
    balance = loyalty_service.get_balance(c.from_user.id)
    if balance < min_pts:
        await c.message.answer(get_text('wallet.spend.min_threshold', lang).replace('%{min}', str(min_pts)))
        return
    # Create spend intent
    intent = loyalty_service.create_spend_intent(c.from_user.id, min_pts)
    if not intent:
        await c.message.answer("⚠️ У вас уже есть активный запрос на списание. Пожалуйста, завершите его или дождитесь истечения срока.")
        return
    await c.message.answer(
        "✅ Запрос на списание создан. Пожалуйста, покажите этот код партнёру:\n\n" +
        f"<code>{intent.intent_token}</code>\n\nДействителен {loyalty_service.default_ttl} мин.",
        parse_mode='HTML'
    )


@profile_router.callback_query(F.data.regexp(r"^profile:history:\d+$"))
async def cb_history(c: CallbackQuery):
    await c.answer()
    lang = await profile_service.get_lang(c.from_user.id)
    m = re.match(r"^profile:history:(\d+)$", c.data)
    page = int(m.group(1)) if m else 1
    # Placeholder history list
    lines = [get_text('btn.history', lang) + f" — стр. {page}"]
    for i in range(1, 6):
        lines.append(f"• {time.strftime('%Y-%m-%d')} — +{i*5} pts @demo")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text('btn_goto_page', lang), callback_data=f"profile:history:{page+1}")]])
    await c.message.edit_text("\n".join(lines), reply_markup=kb)


@profile_router.callback_query(F.data == "profile:report_menu")
async def cb_report_menu(c: CallbackQuery):
    await c.answer()
    lang = await profile_service.get_lang(c.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней", callback_data="report:user:7")],
        [InlineKeyboardButton(text="30 дней", callback_data="report:user:30")],
        [InlineKeyboardButton(text="90 дней", callback_data="report:user:90")],
    ])
    await c.message.edit_text(get_text('report_building', lang), reply_markup=kb)


@profile_router.callback_query(F.data.regexp(r"^report:user:(7|30|90)$"))
async def cb_report_issue(c: CallbackQuery):
    await c.answer()
    lang = await profile_service.get_lang(c.from_user.id)
    key = _report_rl_key(c.from_user.id)
    cnt = int(await cache_service.get(key) or 0)
    if cnt >= 3:
        await c.message.answer(get_text('report_rate_limited', lang))
        return
    await cache_service.set(key, str(cnt + 1), ex=3600)
    await c.message.answer(get_text('report_building', lang))


@profile_router.callback_query(F.data == "card:bind")
async def cb_card_bind(c: CallbackQuery):
    await c.answer()
    lang = await profile_service.get_lang(c.from_user.id)
    await cache_service.set(f"card_bind_wait:{c.from_user.id}", "1", ex=300)
    await c.message.answer(get_text('card.bind.prompt', lang))


@profile_router.message(F.text.regexp(r"^\d{12}$"))
async def on_card_uid_entered(m: Message):
    # Proceed only if user is in bind-await state
    if not (await cache_service.get(f"card_bind_wait:{m.from_user.id}")):
        return
    lang = await profile_service.get_lang(m.from_user.id)
    uid = m.text
    res = card_service.bind_card(m.from_user.id, uid)
    await cache_service.delete(f"card_bind_wait:{m.from_user.id}")
    if not res.ok:
        reason = res.reason or "invalid"
        if reason == "blocked":
            await m.answer("❌ Эта карта заблокирована.")
        elif reason == "taken":
            await m.answer("❌ Эта карта уже привязана к другому пользователю.")
        else:
            await m.answer("❌ Неверный UID карты. Введите 12 цифр.")
        return
    await m.answer(f"✅ Карта с окончанием {res.last4} успешно привязана.")


@profile_router.callback_query(F.data == "profile:notify:toggle")
async def cb_notify_toggle(c: CallbackQuery):
    await c.answer()
    current = await _is_notify_on(c.from_user.id)
    await cache_service.set(_notify_key(c.from_user.id), "off" if current else "on", ex=7*24*3600)
    await render_profile(c, as_edit=True)


@profile_router.callback_query(F.data == "profile:lang")
async def cb_profile_lang(c: CallbackQuery):
    await c.answer()
    # Stub: delegate to existing reply-language flow
    await c.message.answer(get_text('choose_language', await profile_service.get_lang(c.from_user.id)))


def get_profile_router() -> Router:
    return profile_router
