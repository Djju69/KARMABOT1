# core/handlers/language.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.client.bot import Bot
import logging

logger = logging.getLogger(__name__)

# ВАЖНО: этот объект должен существовать, чтобы main_menu_router мог его импортировать
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
        # можно скрыть текущий язык — тогда показываться будет 3 кнопки
        if active and code.lower() == active.lower():
            continue
        rows.append([InlineKeyboardButton(text=label, callback_data=f"lang:set:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _parse_lang(data: str) -> str | None:
    if not data.startswith("lang:"):
        return None
    parts = data.split(":")
    code = parts[-1].lower()
    return code if code in SUPPORTED else None

@language_router.callback_query(F.data.regexp(r"^lang:(?:set:)?(ru|en|vi|ko)$"))
async def on_choose_language_cb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    code = _parse_lang(callback.data or "")
    if not code:
        await callback.answer("Unsupported language", show_alert=True)
        return

    uid = callback.from_user.id
    try:
        # используй существующий сервис профиля (он уже есть в проекте)
        from core.services.profile import ProfileService
        svc = ProfileService()
        await svc.set_lang(uid, code)
        logger.info("Language set to %s for user %s", code, uid)
    except Exception as e:
        logger.exception("Failed to save language for user %s: %s", uid, e)

    await callback.answer("✅ Язык обновлён")

    # перерисовать главное меню: используем текущий билдер Reply
    try:
        from core.keyboards.reply import get_reply_keyboard
        kb = get_reply_keyboard(screen="main")
        # не все клиенты позволяют edit_text здесь — просто пришлём новое сообщение
        await callback.message.answer("Главное меню", reply_markup=kb)
    except Exception as e:
        logger.exception("Failed to redraw main menu: %s", e)
