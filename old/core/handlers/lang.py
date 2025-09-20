from aiogram.types import CallbackQuery
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from core.utils.locales import translations
from core.keyboards.reply_v2 import get_test_restoran

async def language_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    lang_code = callback.data.split("_")[-1]  # 'ru', 'en', 'ko'
    await state.update_data(lang=lang_code)

    text = translations[lang_code]["start"]
    keyboard = get_test_restoran(lang_code)
    await callback.message.edit_text(text)
    await bot.send_message(chat_id=callback.from_user.id, text=translations[lang_code]["main_menu"], reply_markup=keyboard)
