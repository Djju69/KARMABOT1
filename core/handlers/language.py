# core/handlers/language.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.client.bot import Bot
import logging

logger = logging.getLogger(__name__)
language_router = Router(name="language")

SUPPORTED = ("ru", "en", "vi", "ko")

def build_language_inline_kb(active: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    for code, label in [
        ("ru", "Русский (RU)"),
        ("en", "English (EN)"),
        ("vi", "Tiếng Việt (VI)"),
        ("ko", "한국어 (KO)"),
    ]:
        if active and code.lower() == active.lower():
            continue
        rows.append([InlineKeyboardButton(text=label, callback_data=f"lang:set:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _parse_lang(data: str) -> str | None:
    if not data or not data.lower().startswith("lang:"):
        return None
    code = data.split(":")[-1].lower()
    return code if code in SUPPORTED else None

@language_router.callback_query(F.data.startswith("lang:"))
async def on_choose_language_cb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    raw = callback.data or ""
    code = _parse_lang(raw)
    if not code:
        logger.warning("Lang callback ignored (bad data): %r", raw)
        await callback.answer("Unsupported language", show_alert=True)
        return

    uid = callback.from_user.id
    try:
        from core.services.profile import ProfileService
        svc = ProfileService()
        await svc.set_lang(uid, code)
        logger.info("Language set to %s for user %s", code, uid)
    except Exception as e:
        logger.exception("Failed to save language for user %s: %s", uid, e)

    await callback.answer("✅ Язык обновлён")

    try:
        from core.keyboards.reply import get_reply_keyboard
        kb = get_reply_keyboard(screen="main")
        await callback.message.answer("Главное меню", reply_markup=kb)
    except Exception as e:
        logger.exception("Failed to redraw main menu: %s", e)

# Временный логгер для отладки
@language_router.callback_query()
async def _lang_debug_catchall(callback: CallbackQuery):
    if callback.data and callback.data.startswith("lang:"):
        logger.warning("LANG DEBUG raw callback_data=%r", callback.data)
    await callback.answer()  # чтобы не висела «часовая» на кнопке
