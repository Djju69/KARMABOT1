import importlib
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext

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
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru")],
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en")],
        [InlineKeyboardButton(text="한국어 🇰🇷", callback_data="lang:ko")],
        [InlineKeyboardButton(text="Tiếng Việt 🇻🇳", callback_data="lang:vi")],
    ])

async def _apply_language(user_id: int, lang_code: str, state: FSMContext):
    """Apply language selection for user"""
    user_language[user_id] = lang_code
    await state.update_data(lang=lang_code)
    # Здесь можно добавить сохранение в БД, если нужно

@router.callback_query(F.data.startswith("lang:"))
async def on_choose_language_cb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handle language selection from inline keyboard"""
    lang_code = callback.data.split(":")[1]
    if lang_code not in {"ru", "en", "ko", "vi"}:
        await callback.answer("Unsupported language", show_alert=True)
        return
    
    await _apply_language(callback.from_user.id, lang_code, state)
    await callback.message.edit_text("✅ Язык обновлён / Language updated / 언어가 업데이트되었습니다 / Đã cập nhật ngôn ngữ")
    await callback.answer()

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
