"""
Personal cabinet uses REPLY keyboards only (no inline menu).
Handlers here render profile and process Settings/Stats/Add card/My cards/
Become partner, Language, and Notifications toggle as reply actions.
"""
import os
import re
import time
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..database.db_v2 import db_v2
from ..utils.locales_v2 import get_text, translations
from ..services.profile import profile_service
from ..services.cache import cache_service
from ..services.loyalty import loyalty_service
from ..services.cards import card_service
from ..keyboards.reply_v2 import (
    get_profile_keyboard,
    get_profile_settings_keyboard,
    get_partner_keyboard,
    get_admin_keyboard,
    get_superadmin_keyboard,
)
from ..keyboards.inline_v2 import get_add_card_choice_inline
from ..settings import settings

profile_router = Router()
logger = logging.getLogger(__name__)


def _notify_key(user_id: int) -> str:
    return f"notify:{user_id}"


def _report_rl_key(user_id: int) -> str:
    return f"report_rl:{user_id}"


async def _is_notify_on(user_id: int) -> bool:
    v = await cache_service.get(_notify_key(user_id))
    return v != "off"


def _texts(key: str) -> list[str]:
    return [t.get(key, '') for t in translations.values()]


async def render_profile(message: Message):
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    notify_on = await _is_notify_on(user_id)
    text = get_text('profile_main', lang)
    try:
        logger.info("profile.render user_id=%s lang=%s notify_on=%s", user_id, lang, notify_on)
    except Exception:
        pass
    # Личный кабинет пользователя — БЕЗ QR WebApp кнопки
    kb = get_profile_keyboard(lang)
    await message.answer(text, reply_markup=kb)


@profile_router.message(F.text.in_(_texts('profile_settings')))
async def on_profile_settings(message: Message):
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(get_text('profile_settings', lang), reply_markup=get_profile_settings_keyboard(lang))


@profile_router.message(F.text.in_(_texts('profile_stats')))
async def on_profile_stats(message: Message):
    lang = await profile_service.get_lang(message.from_user.id)
    # Placeholder: combined Stats + Report
    await message.answer(get_text('profile_stats', lang) + "\n\n" + get_text('report_building', lang), reply_markup=get_profile_keyboard(lang))


@profile_router.message(F.text.in_(_texts('add_card')))
async def on_add_card(message: Message):
    """Показать выбор: партнёрская карточка или привязка пластиковой."""
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(
        "Выберите действие:",
        reply_markup=get_add_card_choice_inline(lang)
    )

@profile_router.callback_query(F.data == "act:bind_plastic")
async def on_bind_plastic_cb(callback: CallbackQuery):
    """Старт потока привязки пластиковой карты по каллбэку из меню выбора."""
    try:
        await callback.answer()
    except Exception:
        pass
    lang = await profile_service.get_lang(callback.from_user.id)
    await cache_service.set(f"card_bind_wait:{callback.from_user.id}", "1", ex=300)
    try:
        await callback.message.edit_text(
            get_text('card.bind.options', lang) + "\n\n" + get_text('card.bind.prompt', lang),
            reply_markup=None
        )
    except Exception:
        await callback.message.answer(
            get_text('card.bind.options', lang) + "\n\n" + get_text('card.bind.prompt', lang)
        )


@profile_router.message(F.text.in_(_texts('my_cards')))
async def on_my_cards(message: Message):
    # Placeholder: list user's cards
    await message.answer("📋 Ваши карточки будут показаны здесь.")


@profile_router.message(F.text.in_(_texts('btn.partner.become')))
async def on_become_partner(message: Message, state: FSMContext):
    """Open partner cabinet instead of sending external link.
    Keeps UX consistent with partner.open_partner_cabinet_button.
    """
    try:
        # Ensure partner exists
        partner = db_v2.get_or_create_partner(message.from_user.id, message.from_user.full_name)

        # If Partner FSM enabled — сразу запускаем мастер добавления карточки
        if settings.features.partner_fsm:
            try:
                # Lazy import to avoid potential circular deps
                from .partner import start_add_card
            except Exception as e:
                logger.error(f"Failed to import start_add_card: {e}")
            else:
                # Сохраняем partner_id в состояние и запускаем мастер
                await state.update_data(partner_id=partner.id)
                await start_add_card(message, state)
                try:
                    logger.info("profile.become_partner: started add_card flow user_id=%s", message.from_user.id)
                except Exception:
                    pass
                return

        # Fallback: просто открыть кабинет партнёра (без FSM)
        lang = await profile_service.get_lang(message.from_user.id)
        kb = get_partner_keyboard(lang)
        await message.answer("🏪 Вы в личном кабинете партнёра", reply_markup=kb)
        try:
            logger.info("profile.become_partner: opened cabinet user_id=%s", message.from_user.id)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Failed to handle become partner: {e}")
        await message.answer("❌ Не удалось открыть кабинет партнёра. Попробуйте позже.")


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


# Temporary: accept photo during bind flow and ask for manual input until QR decoding is implemented
@profile_router.message(F.photo)
async def on_card_photo(message: Message):
    # Proceed only if user is in bind-await state
    if not (await cache_service.get(f"card_bind_wait:{message.from_user.id}")):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(
        "📷 Обработка QR с фото будет доступна скоро. Пожалуйста, отправьте номер карты (12 цифр) сообщением.")


# Note: language selection via reply button is handled centrally in
# core/handlers/main_menu_router.py to avoid double responses.
@profile_router.message(F.text.in_(_texts('choose_language')))
async def on_choose_language(message: Message):
    return


@profile_router.message(F.text.in_(_texts('btn.notify.on')))
async def on_notify_on(message: Message):
    await cache_service.set(_notify_key(message.from_user.id), "on", ex=7*24*3600)
    await message.answer("🔔 Уведомления включены", reply_markup=get_profile_settings_keyboard(await profile_service.get_lang(message.from_user.id)))


@profile_router.message(F.text.in_(_texts('btn.notify.off')))
async def on_notify_off(message: Message):
    await cache_service.set(_notify_key(message.from_user.id), "off", ex=7*24*3600)
    await message.answer("🔕 Уведомления выключены", reply_markup=get_profile_settings_keyboard(await profile_service.get_lang(message.from_user.id)))


def get_profile_router() -> Router:
    return profile_router


# Admin cabinet entry from main menu button "👑 Админ кабинет"
@profile_router.message(F.text == "👑 Админ кабинет")
async def on_admin_cabinet(message: Message):
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    # Simple role detection: superadmin is OWNER (ADMIN_ID), others are admins
    if user_id == settings.bots.admin_id:
        kb = get_superadmin_keyboard(lang)
        title = get_text('admin_cabinet_title', lang)
    else:
        kb = get_admin_keyboard(lang)
        title = get_text('admin_cabinet_title', lang)
    await message.answer(title, reply_markup=kb)
