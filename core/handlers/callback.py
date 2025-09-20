from aiogram import Bot, types, F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from core.keyboards.restaurant_keyboards import regional_restoran, kitchen_keyboard
from core.keyboards.language_keyboard import language_keyboard
from core.keyboards.inline_v2 import get_language_inline, get_policy_inline
from core.utils.geo import find_restaurants  # Функция поиска ресторанов по координатам
from core.utils.locales import get_text
from core.utils.locales_v2 import get_text as get_text_v2
from core.handlers.category_handlers_v2 import show_categories_v2  # Показываем категории через хендлер
from core.handlers.basic import get_start

router = Router(name="callback_router")

# --- Рестораны рядом с пользователем ---
@router.callback_query(F.data == "rest_near_me")
async def rest_near_me_handler(callback: CallbackQuery, bot: Bot):
    lang = callback.from_user.language_code or "en"
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text(lang, "please_send_location"),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=get_text(lang, "send_location"), request_location=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await callback.answer()

# --- Обработка геолокации пользователя ---
@router.message(F.content_type == types.ContentType.LOCATION)
async def location_handler(message: Message, bot: Bot):
    latitude = message.location.latitude
    longitude = message.location.longitude
    lang = message.from_user.language_code or "en"

    restaurants = find_restaurants(latitude, longitude, radius=2000, lang=lang)

    if not restaurants:
        await bot.send_message(message.chat.id, get_text(lang, "no_places"))
        return

    for rest in restaurants:
        # Можно расширить информацию, например: название, адрес, скидка и т.д.
        await bot.send_message(message.chat.id, text=rest["name"])

# --- Рестораны по районам ---
@router.callback_query(F.data == "rests_by_district")
async def rests_by_district_handler(callback: CallbackQuery, bot: Bot):
    lang = callback.from_user.language_code or "en"
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text(lang, "choose_district"),
        reply_markup=regional_restoran
    )
    await callback.answer()

# --- Рестораны по кухне ---
@router.callback_query(F.data == "rests_by_kitchen")
async def rests_by_kitchen_handler(callback: CallbackQuery, bot: Bot):
    lang = callback.from_user.language_code or "en"
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=get_text(lang, "choose_kitchen"),
        reply_markup=kitchen_keyboard
    )
    await callback.answer()

# --- Показать категории (через callback) ---
@router.callback_query(F.data == "show_categories")
async def show_categories_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    lang = (await state.get_data()).get("lang", callback.from_user.language_code or "en")
    await show_categories_v2(callback.message, bot, lang)
    await callback.answer()

# --- Смена языка ---
@router.callback_query(F.data == "change_language")
async def change_language_callback(callback: CallbackQuery):
    text = "🌐 Choose your language / Выберите язык / 언어를 선택하세요:"
    await callback.message.edit_text(text, reply_markup=language_keyboard)
    await callback.answer()

# --- Выбор языка (новый обработчик) ---
@router.callback_query(F.data.regexp(r"^lang:set:(ru|en|vi|ko)$"))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработчик выбора языка из inline клавиатуры"""
    try:
        # Извлекаем код языка из callback_data
        lang_code = callback.data.split(":")[-1]
        
        # Сохраняем язык в FSM
        await state.update_data(lang=lang_code)
        
        # Получаем имя пользователя
        user_name = callback.from_user.first_name or "Пользователь"
        
        # Создаем приветственное сообщение с именем пользователя
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
        
        # Показываем приветственное сообщение с политикой
        policy_keyboard = get_policy_inline(lang_code)
        
        await callback.message.edit_text(
            text=welcome_text,
            reply_markup=policy_keyboard,
            parse_mode='HTML'
        )
        
        await callback.answer(f"✅ Язык установлен: {lang_code}")
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in language selection: {e}")
        await callback.answer("❌ Ошибка при выборе языка")

# --- Принятие политики ---
@router.callback_query(F.data == "policy:accept")
async def handle_policy_accept(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработчик принятия политики конфиденциальности: без вызова get_start от имени бота."""
    try:
        # Отмечаем принятие в FSM
        await state.update_data(policy_accepted=True)
        
        # Пытаемся сохранить флаг в БД (PG/SQLite), чтобы middleware и хендлеры видели принятие
        try:
            import os
            database_url = os.getenv("DATABASE_URL", "")
            if database_url and database_url.lower().startswith("postgres"):
                # PostgreSQL (asyncpg)
                import asyncpg
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
            # Не прерываем поток при ошибке записи
            pass
        # Короткий ответ на callback, чтобы убрать спиннер
        await callback.answer("✅ Политика принята")
        
        # Удаляем сообщение с политикой
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        # Вызываем get_start для показа меню
        try:
            from core.handlers.basic import get_start
            from aiogram.types import Message
            
            # Создаем фейковое сообщение для вызова get_start
            fake_message = Message(
                message_id=callback.message.message_id + 1,
                from_user=callback.from_user,
                chat=callback.message.chat,
                date=callback.message.date,
                text="/start"
            )
            
            await get_start(fake_message, bot, state)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calling get_start after policy acceptance: {e}")
            
            # Fallback - просто отправляем сообщение
            await bot.send_message(
                callback.from_user.id, 
                f"✅ Политика принята! Нажмите /start для продолжения."
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in policy acceptance: {e}")
        await callback.answer("❌ Ошибка при принятии политики")

# --- Просмотр политики ---
@router.callback_query(F.data == "policy:view")
async def handle_policy_view(callback: CallbackQuery, state: FSMContext):
    """Обработчик просмотра политики конфиденциальности"""
    try:
        # Получаем язык из FSM
        data = await state.get_data()
        lang = data.get("lang", "ru")
        
        # Получаем текст политики
        policy_text = get_text_v2("policy_text", lang)
        
        # Показываем текст политики
        await callback.message.edit_text(
            text=policy_text,
            reply_markup=get_policy_inline(lang)
        )
        
        await callback.answer("📄 Политика конфиденциальности")
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in policy view: {e}")
        await callback.answer("❌ Ошибка при просмотре политики")

# --- Обработчик прочих callback (если потребуется) ---
@router.callback_query(F.data.in_({"rests_by_district", "rest_near_me", "rests_by_kitchen"}))
async def main_menu_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    # Здесь можно обработать что-то общее, сейчас просто ответ без действий
    await callback.answer()


# --- Catch-all (SAFE): не перехватывает неймспейсы бизнес-логики ---
@router.callback_query(
    ~F.data.startswith("pfsm:") &
    ~F.data.startswith("pc:") &
    ~F.data.startswith("partner_cat:") &
    ~F.data.startswith("partner:") &
    ~F.data.startswith("partner") &
    ~F.data.startswith("act:") &
    ~F.data.startswith("adm:") &
    ~F.data.startswith("mod_") &
    ~F.data.startswith("pg:") &
    ~F.data.startswith("filt:") &
    ~F.data.startswith("ai_agent:") &
    ~F.data.startswith("qr") &
    ~F.data.startswith("gallery:") &
    ~F.data.startswith("catalog:") &
    ~F.data.startswith("lang:set:") &
    ~F.data.startswith("policy:") &
    ~F.data.startswith("city:set:")
)
async def handle_any_callback(callback: CallbackQuery):
    """Диагностический обработчик прочих callback_query, не относящихся к основным потокам."""
    try:
        import logging
        logging.getLogger(__name__).info("[CB] Received callback_query (fallback): %s from user %s", callback.data, callback.from_user.id)
    except Exception:
        pass
    await callback.answer("✅ Получен callback")
