from aiogram import Bot, types, F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from core.keyboards.inline import regional_restoran, kitchen_keyboard, language_keyboard
from core.utils.geo import find_restaurants  # Функция поиска ресторанов по координатам
from core.utils.locales import get_text
from core.handlers.category_handlers import show_categories  # Показываем категории через хендлер

router = Router()

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
    await show_categories(callback.message, bot, state)
    await callback.answer()

# --- Смена языка ---
@router.callback_query(F.data == "change_language")
async def change_language_callback(callback: CallbackQuery):
    text = "🌐 Choose your language / Выберите язык / 언어를 선택하세요:"
    await callback.message.edit_text(text, reply_markup=language_keyboard)
    await callback.answer()

# --- Обработчик прочих callback (если потребуется) ---
@router.callback_query(F.data.in_({"rests_by_district", "rest_near_me", "rests_by_kitchen"}))
async def main_menu_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    # Здесь можно обработать что-то общее, сейчас просто ответ без действий
    await callback.answer()
