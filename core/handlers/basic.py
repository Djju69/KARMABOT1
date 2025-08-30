from __future__ import annotations

import logging
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.settings import settings

# Экспортируемый роутер, который подключает main_v2.py
router = Router(name="basic")

# Локализация
from core.utils.locales import translations, get_text

# Клавиатуры
from core.keyboards.inline import select_restoran, regional_restoran, language_keyboard
from core.keyboards.reply import get_main_menu_reply
from core.keyboards.reply_dynamic import get_return_to_main_menu, get_test_restoran

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
    logger = logging.getLogger(__name__)
    logger.info(f"[MENU_DEBUG] Starting get_start for user {message.from_user.id}")
    
    try:
        # Сброс данных
        await state.set_data({})
        await state.update_data({
            'started': True,
            'lang': 'ru'  # Устанавливаем русский по умолчанию
        })
        
        # Получаем клавиатуру главного меню
        keyboard = get_main_menu_reply('ru')
        logger.info(f"[MENU_DEBUG] Generated menu keyboard: {keyboard}")
        
        # Отправляем приветственное сообщение с главным меню
        await bot.send_message(
            chat_id=message.chat.id,
            text="👋 Добро пожаловать! Выберите действие:",
            reply_markup=keyboard
        )
        logger.info("[MENU_DEBUG] Welcome message with main menu sent successfully")
        
    except Exception as e:
        logger.error(f"[MENU_ERROR] Error in get_start: {str(e)}", exc_info=True)
        # Пытаемся отправить сообщение об ошибке
        try:
            await bot.send_message(
                chat_id=message.chat.id,
                text="❌ Произошла ошибка при загрузке меню. Пожалуйста, попробуйте снова."
            )
        except Exception as send_error:
            logger.error(f"[MENU_CRITICAL] Failed to send error message: {str(send_error)}")


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
@router.message(Command("test_menu"))
async def test_menu_command(message: Message, bot: Bot, state: FSMContext):
    """
    Test command to debug menu display.
    
    This command helps verify that the menu system is working correctly.
    It shows the current menu state and feature flags.
    """
    logger = logging.getLogger(__name__)
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        logger.info(f"[MENU_DEBUG] test_menu_command started for user {user_id}")
        
        # Get current state data
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        logger.info(f"[MENU_DEBUG] User {user_id} language: {lang}")
        logger.info(f"[MENU_DEBUG] Feature flags: {settings.features.dict()}")
        
        # Get the menu with error handling
        try:
            keyboard = get_main_menu_reply(lang)
            logger.info(f"[MENU_DEBUG] Menu generated successfully")
        except Exception as e:
            logger.error(f"[MENU_ERROR] Failed to generate menu: {str(e)}", exc_info=True)
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Ошибка при создании меню. Пожалуйста, проверьте логи."
            )
            return
            
        # Send the menu with error handling
        try:
            await bot.send_message(
                chat_id=chat_id,
                text="🔧 Тестовое меню:",
                reply_markup=keyboard
            )
            logger.info(f"[MENU_DEBUG] Menu sent to user {user_id}")
            
            # Send debug info
            debug_info = (
                "✅ Меню успешно загружено\n"
                f"🌐 Язык: {lang}\n"
                f"🚩 Флаги: new_menu={settings.features.new_menu}"
            )
            await bot.send_message(chat_id, debug_info)
            
        except Exception as e:
            logger.error(f"[MENU_ERROR] Failed to send menu to {user_id}: {str(e)}", exc_info=True)
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Ошибка при отправке меню: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"[MENU_CRITICAL] Unhandled error in test_menu_command: {str(e)}", exc_info=True)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text="❌ Критическая ошибка при обработке команды. Администратор уведомлен."
            )
        except:
            logger.error("[MENU_CRITICAL] Could not send error message to user")


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
    """Показывает информацию о том, как работает бот."""
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    text = hiw_text(lang)
    await bot.send_message(chat_id=message.chat.id, text=text, parse_mode="HTML", reply_markup=get_return_to_main_menu(lang))


async def feedback_user(message: Message, bot: Bot, state: FSMContext):
    """Показывает форму обратной связи."""
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    text = feedback_text(lang)
    await bot.send_message(chat_id=message.chat.id, text=text, parse_mode="HTML", reply_markup=get_return_to_main_menu(lang))


async def get_inline(message: Message, bot: Bot, state: FSMContext):
    """Показывает инлайн-клавиатуру с ресторанами."""
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    await bot.send_message(chat_id=message.chat.id, text=get_inline_text(lang), reply_markup=select_restoran(lang))


async def user_regional_rest(message: Message, bot: Bot, state: FSMContext):
    """Показывает региональные рестораны."""
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    await bot.send_message(
        chat_id=message.chat.id, 
        text=regional_restoran_text(lang), 
        reply_markup=regional_restoran(lang)
    )


async def get_hello(message: Message, bot: Bot, state: FSMContext):
    """Обработчик приветственного сообщения."""
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    text = get_hello_text(lang)
    await message.answer(text=text, parse_mode="HTML")
    await main_menu(message, bot, state)


async def get_photo(message: Message, bot: Bot, state: FSMContext):
    """Отправляет фотографию с подписью."""
    user_data = await state.get_data()
    lang = user_data.get("lang", "ru")
    text = get_photo_text(lang)
    await bot.send_photo(
        chat_id=message.chat.id, 
        photo=open('media/photo.jpg', 'rb'), 
        caption=text, 
        parse_mode="HTML"
    )
    await main_menu(message, bot, state)


async def get_video(message: Message, bot: Bot, state: FSMContext):
    """Обработчик получения видео."""
    if message.video:
        user_data = await state.get_data()
        lang = user_data.get("lang", "ru")
        text = get_photo_text_el(lang)  # или другой подходящий текст
        await message.answer(text=text, parse_mode="HTML")
    await main_menu(message, bot, state)


async def get_file(message: Message, bot: Bot, state: FSMContext):
    """Обработчик получения файла."""
    if message.document:
        user_data = await state.get_data()
        lang = user_data.get("lang", "ru")
        text = get_photo_text_el(lang)  # или другой подходящий текст
        await message.answer(text=text, parse_mode="HTML")
    await main_menu(message, bot, state)


async def get_location(message: Message, bot: Bot, state: FSMContext):
    await message.answer(text=get_location_text)
    await main_menu(message, bot, state)


async def on_language_select(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Обработчик выбора языка."""
    try:
        user_id = callback_query.from_user.id
        lang = callback_query.data.split('_')[-1]
        
        # Проверяем, что выбранный язык поддерживается
        if lang not in translations:
            await callback_query.answer("Выбранный язык не поддерживается", show_alert=True)
            return
            
        # Сохраняем выбор языка в состояние
        await state.update_data(lang=lang)
        
        # Отправляем сообщение о выборе языка
        welcome_text = translations[lang].get('welcome', 'Добро пожаловать!')
        await bot.send_message(chat_id=user_id, text=welcome_text, parse_mode="HTML")
        
        # Показываем главное меню
        await main_menu(callback_query.message, bot, state)
        
        # Удаляем сообщение с выбором языка
        try:
            await bot.delete_message(
                chat_id=user_id,
                message_id=callback_query.message.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete language selection message: {e}")
            
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in on_language_select: {e}", exc_info=True)
        await callback_query.answer("Произошла ошибка при выборе языка. Пожалуйста, попробуйте снова.", show_alert=True)


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


async def ensure_policy_accepted(message: Message, bot: Bot, state: FSMContext) -> bool:
    """
    Проверяет, принял ли пользователь политику конфиденциальности.
    Если нет, показывает политику и просит принять её.
    
    Args:
        message: Сообщение от пользователя
        bot: Экземпляр бота
        state: Текущее состояние FSM
        
    Returns:
        bool: True, если политика принята, иначе False
    """
    try:
        user_data = await state.get_data()
        
        # Если пользователь уже принял политику, возвращаем True
        if user_data.get('policy_accepted', False):
            return True
            
        # Получаем язык пользователя или используем русский по умолчанию
        lang = user_data.get('lang', 'ru')
        
        # Текст политики конфиденциальности
        policy_text = translations.get(lang, {}).get(
            'privacy_policy', 
            '🔒 <b>Политика конфиденциальности</b>\n\n' 
            'Пожалуйста, ознакомьтесь с нашей политикой конфиденциальности и примите её, ' 
            'чтобы продолжить использование бота.'
        )
        
        # Создаем инлайн-клавиатуру с кнопками принятия/отклонения
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=translations.get(lang, {}).get('accept_policy', '✅ Принять'),
                    callback_data="accept_policy"
                ),
                InlineKeyboardButton(
                    text=translations.get(lang, {}).get('decline_policy', '❌ Отклонить'),
                    callback_data="decline_policy"
                )
            ]
        ])
        
        # Отправляем сообщение с политикой
        await message.answer(
            text=policy_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Устанавливаем состояние ожидания принятия политики
        await state.set_state("waiting_for_policy_acceptance")
        return False
        
    except Exception as e:
        logger.error(f"Error in ensure_policy_accepted: {e}", exc_info=True)
        # В случае ошибки разрешаем продолжить, чтобы не блокировать пользователя
        return True
    return True
