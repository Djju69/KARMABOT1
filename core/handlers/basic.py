from aiogram.types import Message, CallbackQuery 
from aiogram import Bot
from aiogram.fsm.context import FSMContext

# Локализация
from core.utils.locales import translations, get_text

# Клавиатуры
from core.keyboards.inline import select_restoran, regional_restoran, language_keyboard
from core.keyboards.reply_dynamic import get_return_to_main_menu, get_test_restoran, get_main_menu_reply  # добавлен импорт

# Тексты
from core.windows.feedback import feedback_text
from core.windows.hiw import hiw_text
from core.windows.regional_rest import regional_restoran_text
from core.windows.Wrongtype import (
    get_hello_text,
    get_photo_text,
    get_photo_text_el,
    get_inline_text,
    get_location_text
)


async def main_menu(message: Message, bot: Bot, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    text = get_text(lang, "main_menu")
    
    # Новый код (reply клавиатура с кнопками внизу)
    keyboard = get_main_menu_reply(lang)
    
    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)


async def get_start(message: Message, bot: Bot, state: FSMContext):
    await state.set_data({})  # Сброс данных
    await state.update_data(started=True)
    # Отправляем выбор языка локализованно, но тут можно оставить простой текст
    await bot.send_message(
        chat_id=message.chat.id,
        text="🌐 Choose your language / Выберите язык / 언어를 선택하세요:",
        reply_markup=language_keyboard
    )


async def language_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
    lang = call.data.split("_")[1]  # lang_ru, lang_en, lang_ko
    await state.update_data(lang=lang)

    start_text = get_text(lang, "start")
    main_text = get_text(lang, "main_menu")
    keyboard = select_restoran  # inline клавиатура для меню

    full_text = f"{start_text}\n\n{main_text}"

    try:
        await call.message.edit_text(full_text, reply_markup=keyboard)
    except Exception:
        await bot.send_message(chat_id=call.message.chat.id, text=full_text, reply_markup=keyboard)
    await call.answer()


# Новый обработчик callback для кнопок главного меню
async def main_menu_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
    data = call.data

    if data == "show_categories":
        # Показываем категории (можно подключить реальный обработчик категорий)
        await call.message.edit_text("Выберите категорию:", reply_markup=None)  # заглушка
        # TODO: реализовать вызов show_categories
    elif data == "rests_by_district":
        lang = (await state.get_data()).get("lang", "ru")
        text = get_text(lang, "choose_district") or "Выберите район:"
        await call.message.edit_text(text, reply_markup=regional_restoran)
    elif data == "rest_near_me":
        # Обработка ближайших — заглушка, потом реализовать реальный вызов
        await call.message.edit_text("Показываю рестораны рядом с вами...")
    elif data == "change_language":
        await call.message.edit_text(
            "🌐 Choose your language / Выберите язык / 언어를 선택하세요:",
            reply_markup=language_keyboard
        )
    elif data == "back_to_main":
        # Возврат в главное меню по callback
        message = call.message
        await main_menu(message, bot, state)
    else:
        await call.answer("Неизвестная команда", show_alert=True)

    await call.answer()


async def hiw_user(message: Message, bot: Bot, state: FSMContext):
    lang = (await state.get_data()).get("lang", "ru")
    keyboard = get_return_to_main_menu(lang)
    await bot.send_message(chat_id=message.chat.id, text=hiw_text, reply_markup=keyboard)


async def feedback_user(message: Message, bot: Bot, state: FSMContext):
    lang = (await state.get_data()).get("lang", "ru")
    keyboard = get_return_to_main_menu(lang)
    await bot.send_message(chat_id=message.chat.id, text=feedback_text, reply_markup=keyboard)


async def get_inline(message: Message, bot: Bot, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text=get_inline_text, reply_markup=select_restoran)


async def user_regional_rest(message: Message, bot: Bot, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text=regional_restoran_text, reply_markup=regional_restoran)


async def get_hello(message: Message, bot: Bot, state: FSMContext):
    await message.answer(text=get_hello_text)
    await main_menu(message, bot, state)


async def get_photo(message: Message, bot: Bot, state: FSMContext):
    text = get_photo_text if message.photo else get_photo_text_el
    await message.answer(text=text)
    await main_menu(message, bot, state)


async def get_video(message: Message, bot: Bot, state: FSMContext):
    if message.video:
        await message.answer(text=get_photo_text)
    await main_menu(message, bot, state)


async def get_file(message: Message, bot: Bot, state: FSMContext):
    if message.animation:
        await message.answer(text=get_photo_text)
    await main_menu(message, bot, state)


async def get_location(message: Message, bot: Bot, state: FSMContext):
    await message.answer(text=get_location_text)
    await main_menu(message, bot, state)


async def on_language_select(callback_query):
    """Обработчик выбора языка"""
    from aiogram.types import CallbackQuery
    
    if isinstance(callback_query, CallbackQuery):
        # Обработка выбора языка
        selected_lang = callback_query.data.replace('lang_', '')
        
        # Здесь должна быть логика смены языка
        await callback_query.message.edit_text(
            f"Язык изменен на: {selected_lang}",
            reply_markup=None
        )
        await callback_query.answer()
    else:
        # Показ меню выбора языка
        from core.keyboards.language import get_language_keyboard
        await callback_query.answer("Выберите язык:", reply_markup=get_language_keyboard())
