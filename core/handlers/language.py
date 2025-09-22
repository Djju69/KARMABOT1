# core/handlers/language.py
from __future__ import annotations
from typing import Optional
import re
import logging

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

# In-memory кэш языка
user_language = {}

# i18n
from core.utils.locales_v2 import get_text

# reply клавиатуры
from core.keyboards.reply_v2 import get_reply_keyboard

# опционально: сервис профиля
try:
    from core.services.profile import ProfileService
except ImportError:
    ProfileService = None

logger = logging.getLogger(__name__)

language_router = Router(name="language")
SUPPORTED = ("ru", "en", "vi", "ko")
_CB_RE = re.compile(r"^lang:(?:set:)?(ru|en|vi|ko)$")

def build_language_inline_kb(active: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора языка без эмодзи.
    callback_data: lang:set:<code>
    """
    rows = []
    labels = {
        "ru": "Русский (RU)",
        "en": "English (EN)",
        "vi": "Tiếng Việt (VI)",
        "ko": "한국어 (KO)",
    }
    for code in SUPPORTED:
        title = labels[code]
        if active and active == code:
            title = f"✅ {title}"
        rows.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"lang:set:{code}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@language_router.callback_query(F.data.regexp(_CB_RE))
async def on_choose_language_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    logger.info("LANG_CB_RECEIVED user=%s data=%r", user_id, callback.data)
    
    # Парсим язык
    m = _CB_RE.match(callback.data or "")
    if not m:
        logger.warning("LANG_CB_INVALID user=%s data=%r", user_id, callback.data)
        await callback.answer("Invalid language code")
        return
        
    lang = m.group(1).lower()
    if lang not in SUPPORTED:
        logger.warning("LANG_CB_UNSUPPORTED user=%s lang=%s", user_id, lang)
        await callback.answer("Unsupported language")
        return
    
    # Сохраняем язык
    user_language[user_id] = lang
    
    # Пробуем сохранить в профиль, если сервис доступен
    if ProfileService is not None:
        try:
            svc = ProfileService()
            await svc.set_lang(user_id, lang)
        except Exception as e:
            logger.warning("LANG_SAVE_FAILED user=%s error=%s", user_id, str(e))
    
    # Отвечаем на колбэк
    try:
        await callback.answer(get_text('language_updated', lang))
    except Exception as e:
        logger.error("LANG_ANSWER_FAILED user=%s error=%s", user_id, str(e))
    
    # Обновляем клавиатуру
    try:
        await callback.message.edit_reply_markup(
            reply_markup=build_language_inline_kb(active=lang)
        )
    except Exception as e:
        logger.warning("LANG_UPDATE_KB_FAILED user=%s error=%s", user_id, str(e))
    
    # Отправляем главное меню
    try:
        await callback.message.answer(
            get_text('back_to_main_menu', lang),
            reply_markup=get_reply_keyboard(user=None, screen='main')
        )
    except Exception as e:
        logger.error("LANG_MAIN_MENU_FAILED user=%s error=%s", user_id, str(e))
    
    logger.info("LANG_CB_CHANGED user=%s lang=%s", user_id, lang)

# Легаси-обработчик для текстовых команд
@language_router.message(F.text.lower().in_({"русский (ru)","english (en)","tiếng việt (vi)","한국어 (ko)"}))
async def on_choose_language_msg(message: Message):
    user_id = message.from_user.id
    txt = (message.text or "").lower().strip()
    
    lang_map = {
        "русский (ru)": "ru",
        "english (en)": "en",
        "tiếng việt (vi)": "vi",
        "한국어 (ko)": "ko",
    }
    
    lang = lang_map.get(txt)
    if not lang or lang not in SUPPORTED:
        return
    
    # Сохраняем язык
    user_language[user_id] = lang
    
    # Пробуем сохранить в профиль
    if ProfileService is not None:
        try:
            svc = ProfileService()
            await svc.set_lang(user_id, lang)
        except Exception as e:
            logger.warning("LANG_LEGACY_SAVE_FAILED user=%s error=%s", user_id, str(e))
    
    # Отправляем подтверждение и главное меню
    try:
        await message.answer(
            get_text('language_updated', lang),
            reply_markup=get_reply_keyboard(user=None, screen='main')
        )
    except Exception as e:
        logger.error("LANG_LEGACY_MENU_FAILED user=%s error=%s", user_id, str(e))
    
    logger.info("LANG_LEGACY_CHANGED user=%s lang=%s", user_id, lang)

# redeploy marker 2025-08-30T11:56:29.3300283+07:00
