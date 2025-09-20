from __future__ import annotations

import logging
from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, Update

from core.settings import settings

# Экспортируемый роутер, который подключает main_v2.py
router = Router(name="basic")

# Локализация
from core.utils.locales import translations, get_text

# Клавиатуры
from core.keyboards.restaurant_keyboards import select_restoran, regional_restoran, kitchen_keyboard
from core.keyboards.language_keyboard import language_keyboard
from core.keyboards.reply_v2 import get_main_menu_reply, get_reply_keyboard, get_return_to_main_menu, get_test_restoran
from core.keyboards.reply_v2 import get_return_to_categories

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


async def handle_card_binding_start(message: Message, bot: Bot, state: FSMContext):
    """Handle start command with card binding parameters."""
    logger = logging.getLogger(__name__)
    
    try:
        # Extract card ID from startapp parameters
        import re
        match = re.search(r'cid=([A-Za-z0-9_-]+)', message.text)
        if not match:
            await message.answer(
                "❌ Неверная ссылка для привязки карты.\n\n"
                "Обратитесь в поддержку для получения правильной ссылки.",
                reply_markup=get_return_to_main_menu()
            )
            return
        
        card_id = match.group(1)
        user_id = message.from_user.id
        
        # Import plastic cards service
        from core.services.plastic_cards_service import plastic_cards_service
        
        # Try to bind the card (упрощенная версия - только одна карта)
        result = await plastic_cards_service.bind_card_to_user(
            telegram_id=user_id,
            card_id=card_id,
            card_id_printable=card_id
        )
        
        if result['success']:
            await message.answer(
                f"✅ {result['message']}\n\n"
                "Теперь вы можете использовать эту карту для получения скидок!\n\n"
                "Переходите в личный кабинет для управления картами.",
                reply_markup=get_return_to_main_menu(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                f"❌ {result['message']}\n\n"
                "Если проблема повторяется, обратитесь в поддержку.",
                reply_markup=get_return_to_main_menu(),
                parse_mode='HTML'
            )
        
        # Set language to Russian for new users
        await state.update_data(lang='ru')
        
    except Exception as e:
        logger.error(f"Error in handle_card_binding_start: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при привязке карты. Попробуйте позже.",
            reply_markup=get_return_to_main_menu()
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
    logger.info(f"[START] Starting get_start for user {message.from_user.id}")
    
    try:
        # Check for startapp parameters (for plastic cards binding)
        if message.text and 'startapp=bind' in message.text:
            await handle_card_binding_start(message, bot, state)
            return
        
        # Debug: Log feature flags
        logger.info(f"[DEBUG] Feature flags: new_menu={settings.features.new_menu}")
        
        # Get user state
        user_data = await state.get_data()
        current_lang = user_data.get('lang')
        
        logger.info(f"[DEBUG] Current language: {current_lang}")

        # Ensure policy consent first
        if not await ensure_policy_accepted(message, bot, state):
            return
            
        # If no language set, ask for language
        if not current_lang:
            from .language import build_language_inline_kb
            await message.answer(
                "🌐 Choose your language / Выберите язык / 언어를 선택하세요 / Chọn ngôn ngữ:",
                reply_markup=build_language_inline_kb()
            )
            return

        # Build spec-compliant main menu (reply keyboard v4.1)
        logger.info("[DEBUG] Building spec-compliant menu (reply v4.1)...")
        
        # Check user role to determine appropriate menu
        from core.security.roles import get_user_role
        try:
            user_role = await get_user_role(message.from_user.id)
            role_name = getattr(user_role, "name", str(user_role)).lower()
            logger.info(f"[DEBUG] User role: {role_name}")
            
            # Show admin menu for admins and super admins
            if role_name in ("admin", "super_admin"):
                from core.keyboards.reply_v2 import get_main_menu_reply_admin
                is_superadmin = role_name == "super_admin"
                keyboard = get_main_menu_reply_admin(current_lang, is_superadmin)
                logger.info(f"[DEBUG] Showing admin menu for {role_name}")
            else:
                # Regular user menu
                user_ctx = {"role": "user", "lang": current_lang, "has_partner_cards": False}
                keyboard = get_reply_keyboard(user_ctx, screen="main")
                logger.info(f"[DEBUG] Showing regular user menu")
        except Exception as e:
            logger.error(f"[ERROR] Failed to get user role: {e}")
            # Fallback to regular user menu
            user_ctx = {"role": "user", "lang": current_lang, "has_partner_cards": False}
            keyboard = get_reply_keyboard(user_ctx, screen="main")
            logger.info(f"[DEBUG] Using fallback menu due to role error")
        
        if not keyboard:
            logger.error("[ERROR] Failed to generate menu: keyboard is None")
            # Fallback to simple keyboard
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Test Button")]],
                resize_keyboard=True
            )
        
        logger.info(f"[DEBUG] Sending menu to user {message.from_user.id}")
        
        # Send welcome message with user name and menu
        user_name = message.from_user.first_name or "Пользователь"
        welcome_text = f"""{user_name} 👋 Добро пожаловать в Karma System! 

✨ Получай эксклюзивные скидки и предложения через QR-код в удобных категориях:  
🍽️ Рестораны и кафе  
🧖‍♀️ SPA и массаж  
🏍️ Аренда байков  
🏨 Отели  
🚶‍♂️ Экскурсии
🛍️ Магазины и услуги  

А если ты владелец бизнеса — присоединяйся к нам как партнёр и подключай свою систему лояльности! 🚀  

Начни экономить прямо сейчас — выбирай категорию и получай свои скидки! 

Продолжая пользоваться ботом вы соглашаетесь с политикой обработки персональных данных."""

        await bot.send_message(
            chat_id=message.chat.id,
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

        # Mark started
        await state.update_data(started=True)
        
        logger.info("[SUCCESS] Menu sent successfully")
        
    except Exception as e:
        logger.error(f"[ERROR] get_start failed: {str(e)}", exc_info=True)
        try:
            # Пытаемся отправить хотя бы простое сообщение об ошибке
            await bot.send_message(
                chat_id=message.chat.id,
                text="❌ Ошибка при загрузке меню. Пожалуйста, попробуйте снова.",
                parse_mode='HTML'
            )
        except Exception as send_error:
            logger.critical(f"[CRITICAL] Failed to send error message: {str(send_error)}")


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
        logger.info(f"[DEBUG] ===== MENU DEBUG START =====")
        logger.info(f"[DEBUG] User ID: {user_id}")
        logger.info(f"[DEBUG] Chat ID: {chat_id}")
        
        # Get current state and settings
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Log all relevant info
        logger.info(f"[DEBUG] Current language: {lang}")
        logger.info(f"[DEBUG] Feature flags: {settings.features.dict()}")
        logger.info(f"[DEBUG] User data: {user_data}")
        
        # Force enable menu for testing
        logger.info("[DEBUG] Forcing menu generation...")
        keyboard = get_main_menu_reply(lang)
        
        if not keyboard:
            logger.error("[ERROR] Menu generation returned None!")
            # Create emergency keyboard
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Test Button")]],
                resize_keyboard=True
            )
            await message.answer("⚠️ Меню не загружено, показан аварийный вариант")
        
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
    try:
        # Импортируем обработчик кабинета
        from core.handlers.cabinet_router import user_cabinet_handler
        await user_cabinet_handler(message, state)
    except Exception as e:
        logger.error(f"Error in open_cabinet: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Fallback - базовая информация
        user_info = (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"👤 Имя: {message.from_user.full_name}\n"
            f"🌐 Язык: {lang.upper()}\n"
        )
        
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
        # 1) Полный обход для супер-админа
        try:
            from core.settings import settings as _settings
            if int(message.from_user.id) == int(getattr(_settings.bots, 'admin_id', 0)):
                return True
        except Exception:
            pass

        # 2) Проверяем флаг в FSM
        user_data = await state.get_data()
        if user_data.get('policy_accepted', False):
            return True

        # 3) Если в FSM нет — читаем из БД и при необходимости устанавливаем в FSM
        import os
        database_url = os.getenv("DATABASE_URL", "").lower()
        try:
            if database_url.startswith("postgres"):
                import asyncpg
                conn_pg = await asyncpg.connect(os.getenv("DATABASE_URL"))
                try:
                    val = await conn_pg.fetchval(
                        "SELECT policy_accepted FROM users WHERE telegram_id = $1",
                        int(message.from_user.id),
                    )
                    if bool(val):
                        await state.update_data(policy_accepted=True)
                        return True
                finally:
                    await conn_pg.close()
            else:
                from core.database.db_v2 import db_v2
                conn = db_v2.get_connection()
                try:
                    cur = conn.execute(
                        "SELECT policy_accepted FROM users WHERE telegram_id = ?",
                        (int(message.from_user.id),),
                    )
                    row = cur.fetchone()
                    if row is not None and bool(row[0] if not isinstance(row, dict) else row.get('policy_accepted')):
                        await state.update_data(policy_accepted=True)
                        return True
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Exception:
            # Если проверка БД не удалась — продолжаем показом политики
            pass

        # 4) Политика не принята — показываем экран политики
        lang = user_data.get('lang', 'ru')
        policy_text = translations.get(lang, {}).get(
            'privacy_policy', 
            '🔒 <b>Политика конфиденциальности</b>\n\n'
            'Пожалуйста, ознакомьтесь с нашей политикой конфиденциальности и примите её, '
            'чтобы продолжить использование бота.'
        )

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

        await message.answer(
            text=policy_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        await state.set_state("waiting_for_policy_acceptance")
        return False

    except Exception as e:
        logger.error(f"Error in ensure_policy_accepted: {e}", exc_info=True)
        # В случае ошибки — не блокируем
        return True
    return True


# Обработчики политики конфиденциальности
@router.callback_query(lambda c: c.data == "accept_policy")
async def handle_accept_policy(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обработка принятия политики конфиденциальности"""
    try:
        # Отмечаем, что пользователь принял политику
        await state.update_data(policy_accepted=True)
        # Сохраняем флаг в локальную БД (SQLite), чтобы не терялся между рестартами
        try:
            import os
            database_url = os.getenv("DATABASE_URL", "")
            if database_url and database_url.lower().startswith("postgres"):
                # PostgreSQL путь (asyncpg)
                import asyncpg
                try:
                    conn_pg = await asyncpg.connect(database_url)
                    try:
                        await conn_pg.execute(
                            """
                            INSERT INTO users(telegram_id, username, first_name, last_name, language_code, policy_accepted)
                            VALUES($1,$2,$3,$4,$5, TRUE)
                            ON CONFLICT (telegram_id) DO UPDATE SET policy_accepted=EXCLUDED.policy_accepted, updated_at=NOW()
                            """,
                            int(callback.from_user.id),
                            (callback.from_user.username or None),
                            (callback.from_user.first_name or None),
                            (callback.from_user.last_name or None),
                            (getattr(callback.from_user, 'language_code', None) or 'ru'),
                        )
                    finally:
                        await conn_pg.close()
                except Exception:
                    # fallback не падаем
                    pass
            else:
                # SQLite путь
                from core.database.db_v2 import db_v2
                conn = db_v2.get_connection()
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO users(telegram_id, username, first_name, last_name, language_code, policy_accepted)
                        VALUES(?, ?, ?, ?, ?, 1)
                        """,
                        (
                            int(callback.from_user.id),
                            (callback.from_user.username or None),
                            (callback.from_user.first_name or None),
                            (callback.from_user.last_name or None),
                            (getattr(callback.from_user, 'language_code', None) or 'ru'),
                        ),
                    )
                    conn.execute(
                        "UPDATE users SET policy_accepted = 1, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                        (int(callback.from_user.id),),
                    )
                    conn.commit()
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Exception:
            # Не ломаем поток при ошибке записи
            pass
        
        # Отвечаем на callback
        await callback.answer("✅ Политика принята!")
        
        # Удаляем сообщение с политикой
        await callback.message.delete()
        
        # Сообщаем и не дергаем get_start (чтобы не спутать контекст пользователя)
        await bot.send_message(callback.from_user.id, "✅ Политика принята! Можете пользоваться меню.")
        
    except Exception as e:
        logger.error(f"Error handling policy acceptance: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка. Попробуйте снова.", show_alert=True)


@router.callback_query(lambda c: c.data == "decline_policy")
async def handle_decline_policy(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обработка отклонения политики конфиденциальности"""
    try:
        # Отвечаем на callback
        await callback.answer("❌ Для использования бота необходимо принять политику конфиденциальности", show_alert=True)
        
        # Не удаляем сообщение, чтобы пользователь мог принять политику
        
    except Exception as e:
        logger.error(f"Error handling policy decline: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка.", show_alert=True)
