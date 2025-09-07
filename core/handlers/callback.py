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
        
        # Получаем текст для политики на выбранном языке
        policy_text = get_text_v2("policy_message", lang_code)
        
        # Показываем политику конфиденциальности
        policy_keyboard = get_policy_inline(lang_code)
        
        await callback.message.edit_text(
            text=policy_text,
            reply_markup=policy_keyboard
        )
        
        await callback.answer(f"✅ Язык установлен: {lang_code}")
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in language selection: {e}")
        await callback.answer("❌ Ошибка при выборе языка")

# --- Принятие политики ---
@router.callback_query(F.data == "policy:accept")
async def handle_policy_accept(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработчик принятия политики конфиденциальности"""
    try:
        # Получаем язык из FSM
        data = await state.get_data()
        lang = data.get("lang", "ru")
        
        # Отмечаем, что пользователь принял политику
        await state.update_data(policy_accepted=True)
        
        # Показываем главное меню
        await get_start(callback.message, bot, state)
        
        await callback.answer("✅ Политика принята")
        
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


# --- Catch-all: лог и быстрый ответ на любые callback_query ---
@router.callback_query()
async def handle_any_callback(callback: CallbackQuery):
    """Диагностический обработчик всех callback_query, чтобы убедиться, что события доходят."""
    try:
        import logging
        logging.getLogger(__name__).info("[CB] Received callback_query: %s from user %s", callback.data, callback.from_user.id)
    except Exception:
        pass
    await callback.answer("✅ Получен callback")
