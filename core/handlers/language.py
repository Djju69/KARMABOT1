# core/handlers/language.py
from __future__ import annotations
from typing import Optional
import re
import logging

from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

# быстрый in-memory кэш языка (на случай отсутствия БД или медленного сервиса)
try:
    from core.utils.storage import user_language  # dict: user_id -> 'ru'|'en'|'vi'|'ko'
except Exception:
    user_language = {}

# i18n utils
from core.utils.locales_v2 import get_text

# reply клавиатуры
from core.keyboards.reply import get_reply_keyboard

# опционально: сервис профиля (если присутствует)
try:
    from core.services.profile import ProfileService
except Exception:
    ProfileService = None  # заглушка

logger = logging.getLogger(__name__)

language_router = Router(name="language")

SUPPORTED = ("ru", "en", "vi", "ko")
_CB_RE = re.compile(r"^lang:(?:set:)?(ru|en|vi|ko)$")

def build_language_inline_kb(active: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора языка БЕЗ эмодзи, чтобы исключить проблемы UTF-8.
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
        # можно подсветить активный язык галочкой
        if active and active == code:
            title = f"✅ {title}"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"lang:set:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _parse_lang_from_data(data: str) -> Optional[str]:
    m = _CB_RE.match(data or "")
    return m.group(1) if m else None

async def _persist_lang(user_id: int, lang: str) -> None:
    # обновляем быстрый кэш
    user_language[user_id] = lang
    # обновляем профиль, если сервис доступен
    if ProfileService is not None:
        try:
            svc = ProfileService()
            await svc.set_lang(user_id, lang)
        except Exception as e:
            logger.warning("ProfileService.set_lang failed: %s", e)

@language_router.callback_query(F.data.regexp(_CB_RE))
async def on_choose_language_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    raw = callback.data or ""
    lang = _parse_lang_from_data(raw)

    if lang not in SUPPORTED:
        try:
            await callback.answer("Unsupported language", show_alert=True)
        except Exception:
            pass
        logger.error("lang callback parse failed: data=%r user=%s", raw, user_id)
        return

    # сохраняем язык
    await _persist_lang(user_id, lang)

    # ответ боту, чтобы убрать "часики"
    try:
        await callback.answer(get_text('language_updated', lang))
    except TelegramBadRequest:
        pass

    # обновляем сообщение с клавиатурой языка (если можно)
    try:
        await callback.message.edit_reply_markup(reply_markup=build_language_inline_kb(active=lang))
    except Exception:
        # если редактирование не получилось (старое сообщение и т.п.) — игнор
        pass

    # шлём новое главное меню на выбранном языке
    try:
        await callback.message.answer(
            get_text('back_to_main_menu', lang),
            reply_markup=get_reply_keyboard(user=None, screen='main')
        )
    except Exception as e:
        logger.error("Failed to send main menu after language set: %s", e)

    logger.info("Language changed to %s for user_id=%s", lang, user_id)

# Легаси обработчик текстом, если где-то остался
@language_router.message(F.text.lower().in_({"русский (ru)","english (en)","tiếng việt (vi)","한국어 (ko)"}))
async def on_choose_language_msg(message: Message):
    txt = (message.text or "").lower().strip()
    map_txt = {
        "русский (ru)": "ru",
        "english (en)": "en",
        "tiếng việt (vi)": "vi",
        "한국어 (ko)": "ko",
    }
    lang = map_txt.get(txt)
    if lang not in SUPPORTED:
        return
    await _persist_lang(message.from_user.id, lang)
    await message.answer(
        get_text('language_updated', lang),
        reply_markup=get_reply_keyboard(user=None, screen='main')
    )
    logger.info("Language changed (text) to %s for user_id=%s", lang, message.from_user.id)
