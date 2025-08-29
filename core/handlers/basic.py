from aiogram.types import Message, CallbackQuery 
from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext

# Экспортируемый роутер, который подключает main_v2.py
router = Router(name="basic")

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


async def on_language_select(callback_query, bot: Bot, state: FSMContext):
    """Обработчик выбора языка"""
    lang = callback_query.data.split('_')[-1]  # Получаем выбранный язык из callback_data
    await state.update_data(lang=lang)
    
    # Отправляем сообщение о выборе языка
    await bot.answer_callback_query(
        callback_query.id,
        text=f"✅ Language set to {lang.upper()}"
    )
    
    # Показываем основное меню
    await main_menu(
        message=callback_query.message,
        bot=bot,
        state=state
    )


async def open_cabinet(message: Message, bot: Bot, state: FSMContext):
    """Открывает личный кабинет пользователя"""
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    
    # Базовая информация о пользователе
    user_info = (
        f"👤 <b>Личный кабинет</b>\n\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"🌐 Язык: {lang.upper()}\n"
    )
    
    # Здесь можно добавить дополнительную логику, например, баланс, статистику и т.д.
    
    await message.answer(
        text=user_info,
        parse_mode='HTML'
    )
    
    # Возвращаем пользователя в главное меню
    await main_menu(message, bot, state)


async def ensure_policy_accepted(message: Message, bot: Bot, state: FSMContext):
    """
    Проверяет, принял ли пользователь политику конфиденциальности.
    Если нет, показывает политику и просит принять её.
    """
    user_data = await state.get_data()
    
    # Проверяем, принял ли пользователь политику
    if not user_data.get('policy_accepted', False):
        # Показываем политику конфиденциальности
        policy_text = (
            "🔒 <b>Политика конфиденциальности</b>\n\n"
            "Перед продолжением работы с ботом, пожалуйста, ознакомьтесь с нашей политикой конфиденциальности.\n\n"
            "1. Мы собираем только необходимые данные для работы бота\n"
            "2. Ваши данные защищены и не передаются третьим лицам\n"
            "3. Вы можете запросить удаление ваших данных в любое время\n\n"
            "Нажимая кнопку 'Принять', вы соглашаетесь с нашей политикой конфиденциальности."
        )
        
        # Создаем клавиатуру с кнопкой принятия политики
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Принять политику")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            text=policy_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Устанавливаем состояние ожидания принятия политики
        await state.set_state("waiting_for_policy_acceptance")
        return False
    
    return True
