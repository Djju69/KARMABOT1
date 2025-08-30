import contextlib
import importlib
import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

from core.utils.locales import translations
from core.utils.storage import user_language
from core.keyboards.reply import test_restoran

def _resolve_get_main_menu():
    try:
        m = importlib.import_module("core.windows.main_menu")
        candidates = [
            "get_main_menu",
            "build_main_menu",
            "get_main_menu_kb",
            "get_main_menu_keyboard",
            "main_menu",
            "build_menu",
            "get_menu",
        ]
        for name in candidates:
            fn = getattr(m, name, None)
            if callable(fn):
                return fn
    except ImportError:
        pass
    # Fallback to a no-op keyboard remover
    def _noop(*args, **kwargs):
        return ReplyKeyboardRemove()
    return _noop

get_main_menu = _resolve_get_main_menu()

router = Router()

# Сопоставление текста с языковым кодом (для обратной совместимости с текстовыми кнопками)
LANG_TEXT_TO_CODE = {
    # Русский
    "Русский": "ru",
    "Русский 🇷🇺": "ru",
    # English
    "English": "en",
    "English 🇬🇧": "en",
    # Korean
    "한국어": "ko",
    "한국어 🇰🇷": "ko",
    # Vietnamese
    "Tiếng Việt": "vi",
    "Tiếng Việt 🇻🇳": "vi",
}

def build_language_inline_kb() -> InlineKeyboardMarkup:
    """Build inline keyboard for language selection"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский (RU)", callback_data="lang:set:ru")],
        [InlineKeyboardButton(text="English (EN)", callback_data="lang:set:en")],
        [InlineKeyboardButton(text="Tiếng Việt (VI)", callback_data="lang:set:vi")],
        [InlineKeyboardButton(text="한국어 (KO)", callback_data="lang:set:ko")],
    ])

async def _apply_language(user_id: int, lang_code: str, state: FSMContext):
    """Apply language selection for user"""
    user_language[user_id] = lang_code
    await state.update_data(lang=lang_code)
    # Здесь можно добавить сохранение в БД, если нужно

@router.callback_query(F.data.regexp(r"^lang:(set:)?(ru|en|vi|ko)$"))
async def on_choose_language_cb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle language selection from inline keyboard"""
    try:
        # Extract language code from both lang:ru and lang:set:ru formats
        lang_code = callback.data.split(":")[-1]
        if lang_code not in {"ru", "en", "ko", "vi"}:
            await callback.answer("Unsupported language", show_alert=True)
            return
        
        await _apply_language(callback.from_user.id, lang_code, state)
        
        # Remove inline keyboard
        with contextlib.suppress(Exception):
            await callback.message.edit_reply_markup()
        
        # Send confirmation
        await callback.answer("✅ Язык обновлён")
        
        # Redraw main menu
        from core.windows.main_menu import get_main_menu
        await callback.message.answer(
            "Главное меню",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Language selection error: {e}")
        await callback.answer("❌ Ошибка при смене языка", show_alert=True)

@router.message(F.text.in_(LANG_TEXT_TO_CODE.keys()))
async def on_choose_language_msg(message: Message, state: FSMContext, bot: Bot):
    """Handle language selection from text buttons (legacy support)"""
    lang_code = LANG_TEXT_TO_CODE.get(message.text)
    if lang_code:
        await _apply_language(message.from_user.id, lang_code, state)
        await message.answer("✅ Язык обновлён / Language updated / 언어가 업데이트되었습니다 / Đã cập nhật ngôn ngữ")

# Legacy function for backward compatibility
def language_keyboard():
    return build_language_inline_kb()

# Legacy function for backward compatibility
async def language_chosen(message: Message, bot: Bot, state: FSMContext):
    await on_choose_language_msg(message, state, bot)
