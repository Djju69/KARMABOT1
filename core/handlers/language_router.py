"""
Обработчики для смены языка
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core.utils.locales_v2 import get_text
from core.keyboards.reply_v2 import get_language_keyboard, get_main_menu_reply

logger = logging.getLogger(__name__)
router = Router(name="language_router")

@router.message(F.text.in_([
    "🌐 Выберите язык", "🌐 Choose language", "🌐 Chọn ngôn ngữ", "🌐 언어 선택"
]))
async def handle_language_selection(message: Message, state: FSMContext):
    """Показать клавиатуру выбора языка"""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        text = get_text('choose_language', lang)
        keyboard = get_language_keyboard(lang)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing language selection: {e}")
        await message.answer("❌ Ошибка при загрузке языков")

@router.message(F.text.in_([
    "🇷🇺 Русский", "🇺🇸 English", "🇻🇳 Tiếng Việt", "🇰🇷 한국어"
]))
async def handle_language_change(message: Message, state: FSMContext):
    """Обработать смену языка"""
    try:
        user_data = await state.get_data()
        current_lang = user_data.get('lang', 'ru')
        
        # Определяем новый язык по тексту кнопки
        language_map = {
            "🇷🇺 Русский": "ru",
            "🇺🇸 English": "en", 
            "🇻🇳 Tiếng Việt": "vi",
            "🇰🇷 한국어": "ko"
        }
        
        new_lang = language_map.get(message.text)
        if not new_lang:
            await message.answer("❌ Неизвестный язык")
            return
        
        # Обновляем язык в состоянии
        await state.update_data(lang=new_lang)
        
        # Показываем подтверждение
        language_names = {
            "ru": "Русский",
            "en": "English",
            "vi": "Tiếng Việt", 
            "ko": "한국어"
        }
        
        text = get_text('language_changed', new_lang).format(language=language_names[new_lang])
        keyboard = get_main_menu_reply(new_lang)
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        await message.answer("❌ Ошибка при смене языка")
