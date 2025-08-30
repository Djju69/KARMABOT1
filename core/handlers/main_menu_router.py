from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union, cast

from aiogram import Bot, F, Router, html
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, Update, InlineKeyboardMarkup

from ..services.profile import profile_service
from ..utils.locales_v2 import translations
from .basic import (
    ensure_policy_accepted, feedback_user, get_file, get_hello, get_inline,
    get_location, get_photo, get_start, get_video, hiw_user, main_menu,
    on_language_select, open_cabinet, user_regional_rest
)

# Импорт функций из category_handlers_v2
from .category_handlers_v2 import (
    handle_profile, on_hotels, on_hotels_submenu, on_restaurants, on_shops, on_spa,
    on_transport, on_tours, on_shops_submenu, on_tours_submenu, on_spa_submenu,
    on_transport_submenu, show_catalog_page, show_nearest_v2, show_categories_v2
)

# Фолбэк на старые версии функций, если новые недоступны
if 'show_nearest_v2' not in globals():
    from .basic import show_nearest as show_nearest_v2  # type: ignore

if 'show_categories_v2' not in globals():
    from .basic import show_categories as show_categories_v2  # type: ignore

# Заглушки для отсутствующих функций
async def show_places_page(*args, **kwargs):
    """Заглушка для функции показа страницы мест"""
    logger.warning("show_places_page function is not implemented")
    return None

async def show_offers_page(*args, **kwargs):
    """Заглушка для функции показа страницы предложений"""
    logger.warning("show_offers_page function is not implemented")
    return None

async def show_place_details(*args, **kwargs):
    """Заглушка для функции показа деталей места"""
    logger.warning("show_place_details function is not implemented")
    return None

async def show_offer_details(*args, **kwargs):
    """Заглушка для функции показа деталей предложения"""
    logger.warning("show_offer_details function is not implemented")
    return None

async def show_category_items(*args, **kwargs):
    """Заглушка для функции показа элементов категории"""
    logger.warning("show_category_items function is not implemented")
    return None

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация роутера
main_menu_router = Router(name="main_menu_router")

# --- Main Menu ---
@main_menu_router.message(CommandStart())
async def handle_start_command(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик команды /start."""
    logger.debug(f"User {message.from_user.id} started the bot")
    await get_start(message, bot, state)


@main_menu_router.message(
    F.text.in_([
        # Common user-typed variants to open the main menu (not a button)
        "Меню", "Главное меню",
        "Menu", "Main Menu",
        # Lowercase variants
        "меню", "главное меню", "menu", "main menu",
    ])
)
async def handle_main_menu_text(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик текстовых команд для открытия главного меню."""
    logger.debug(f"User {message.from_user.id} requested main menu via text command")
    await get_start(message, bot, state)

@main_menu_router.message(F.text.in_([t.get('choose_category', '') for t in translations.values()]))
async def handle_choose_category(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки выбора категории."""
    logger.debug(f"User {message.from_user.id} chose category selection")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    
    try:
        await show_categories_v2(message, bot, lang)
    except Exception as e:
        logger.error(f"Error showing categories: {e}", exc_info=True)
        error_text = translations.get(lang, {}).get(
            'error_occurred', 
            'Произошла ошибка при загрузке категорий. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('profile', '') for t in translations.values()]))
async def handle_profile_button(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки профиля пользователя."""
    logger.debug(f"User {message.from_user.id} opened profile")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Use inline cabinet (render_profile via basic.open_cabinet) instead of legacy reply flow
        await handle_profile(message, bot, state)
    except Exception as e:
        logger.error(f"Error in profile handling: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'profile_error', 
            'Не удалось загрузить профиль. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")
    await open_cabinet(message, bot, state)


@main_menu_router.message(F.text.in_([t.get('help', '') for t in translations.values()]))
async def handle_help(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Помощь'."""
    logger.debug(f"User {message.from_user.id} requested help")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        await hiw_user(message, bot, state)
    except Exception as e:
        logger.error(f"Error showing help: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'help_error', 
            'Не удалось загрузить справку. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


from ..handlers.language import build_language_inline_kb

@main_menu_router.message(F.text.in_([t.get('choose_language', '') for t in translations.values()]))
async def handle_choose_language(message: Message, bot: Bot, state: FSMContext):
    """Обработчик кнопки выбора языка."""
    logger.debug(f"User {message.from_user.id} chose language selection")
    try:
        # Показываем инлайн-клавиатуру с выбором языка
        await message.answer(
            "🌐 Выберите язык / Select language / 언어를 선택하세요 / Chọn ngôn ngữ:",
            reply_markup=build_language_inline_kb()
        )
    except Exception as e:
        logger.error(f"Error showing language selection: {e}")
        await message.answer("❌ Не удалось загрузить выбор языка. Пожалуйста, попробуйте позже.")


@main_menu_router.message(F.text.in_([t.get('show_nearest', '') for t in translations.values()]))
async def handle_show_nearest(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Ближайшие заведения'."""
    logger.debug(f"User {message.from_user.id} requested nearest places")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_nearest_v2(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error showing nearest places: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'nearest_error', 
            'Не удалось загрузить ближайшие заведения. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('category_restaurants', '') for t in translations.values()]))
async def handle_restaurants(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Рестораны'."""
    logger.debug(f"User {message.from_user.id} selected Restaurants category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_restaurants(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error in restaurants category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'restaurants_error', 
            'Не удалось загрузить список ресторанов. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('category_spa', '') for t in translations.values()]))
async def handle_spa(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'SPA и Уход'."""
    logger.debug(f"User {message.from_user.id} selected SPA category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_spa(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error in SPA category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'spa_error', 
            'Не удалось загрузить список SPA-салонов. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('category_hotels', '') for t in translations.values()]))
async def handle_hotels(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Отели'."""
    logger.debug(f"User {message.from_user.id} selected Hotels category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_hotels(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error in hotels category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'hotels_error', 
            'Не удалось загрузить список отелей. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('transport', '') for t in translations.values()]))
async def handle_transport(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Транспорт'."""
    logger.debug(f"User {message.from_user.id} selected Transport category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_transport(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error in transport category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'transport_error', 
            'Не удалось загрузить информацию о транспорте. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('tours', '') for t in translations.values()]))
async def handle_tours(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Экскурсии'."""
    logger.debug(f"User {message.from_user.id} selected Tours category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_tours(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error in tours category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'tours_error', 
            'Не удалось загрузить список экскурсий. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('shops', '') for t in translations.values()]))
async def handle_shops(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Магазины и услуги'."""
    logger.debug(f"User {message.from_user.id} selected Shops category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_shops(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error in shops category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'shops_error', 
            'Не удалось загрузить список магазинов. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('back_to_categories', '') for t in translations.values()]))
async def handle_back_to_categories(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Назад к категориям'."""
    logger.debug(f"User {message.from_user.id} clicked back to categories")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        await show_categories_v2(message, bot, lang)
    except Exception as e:
        logger.error(f"Error going back to categories: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'categories_error',
            'Не удалось загрузить категории. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('back_to_main_menu', '') for t in translations.values()]))
async def handle_back_to_main_menu(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Назад в главное меню'."""
    logger.debug(f"User {message.from_user.id} clicked back to main menu")
    try:
        await get_start(message, bot, state)
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'main_menu_error',
            'Не удалось загрузить главное меню. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


# Обработчики подменю
@main_menu_router.message(F.text.in_([
    t.get('transport_bikes', '') for t in translations.values()
    if t.get('transport_bikes')
]))
async def handle_transport_bikes(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Аренда велосипедов'."""
    await handle_transport_submenu(message, bot, state, 'bikes')


@main_menu_router.message(F.text.in_([
    t.get('transport_cars', '') for t in translations.values()
    if t.get('transport_cars')
]))
async def handle_transport_cars(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Аренда автомобилей'."""
    await handle_transport_submenu(message, bot, state, 'cars')


@main_menu_router.message(F.text.in_([
    t.get('tours_group', '') for t in translations.values()
    if t.get('tours_group')
]))
async def handle_group_tours(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Групповые экскурсии'."""
    await handle_tours_submenu(message, bot, state, 'group')


@main_menu_router.message(F.text.in_([
    t.get('tours_private', '') for t in translations.values()
    if t.get('tours_private')
]))
async def handle_private_tours(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Индивидуальные экскурсии'."""
    await handle_tours_submenu(message, bot, state, 'private')


@main_menu_router.message(F.text.in_([
    t.get('spa_massage', '') for t in translations.values()
    if t.get('spa_massage')
]))
async def handle_massage(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Массаж'."""
    await handle_spa_submenu(message, bot, state, 'massage')


@main_menu_router.message(F.text.in_([
    t.get('spa_sauna', '') for t in translations.values()
    if t.get('spa_sauna')
]))
async def handle_sauna(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Сауна'."""
    await handle_spa_submenu(message, bot, state, 'sauna')


@main_menu_router.message(F.text.in_([
    t.get('hotels_hotels', '') for t in translations.values()
    if t.get('hotels_hotels')
]))
async def handle_hotels_list(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Отели'."""
    await handle_hotels_submenu(message, bot, state, 'hotels')


@main_menu_router.message(F.text.in_([
    t.get('hotels_apartments', '') for t in translations.values()
    if t.get('hotels_apartments')
]))
async def handle_apartments(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Апартаменты'."""
    await handle_hotels_submenu(message, bot, state, 'apartments')


@main_menu_router.message(F.text.in_([
    t.get('shops_shops', '') for t in translations.values()
    if t.get('shops_shops')
]))
async def handle_shops_list(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Магазины'."""
    await handle_shops_submenu(message, bot, state, 'shops')


@main_menu_router.message(F.text.in_([
    t.get('shops_services', '') for t in translations.values()
    if t.get('shops_services')
]))
async def handle_services(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Услуги'."""
    await handle_shops_submenu(message, bot, state, 'services')


# Вспомогательные функции для обработки подменю
async def handle_transport_submenu(message: Message, bot: Bot, state: FSMContext, transport_type: str) -> None:
    """Обработчик подменю транспорта."""
    logger.debug(f"User {message.from_user.id} selected transport type: {transport_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_transport_submenu(message, bot, lang, city_id, transport_type)
    except Exception as e:
        logger.error(f"Error in {transport_type} transport: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'transport_error',
            'Не удалось загрузить информацию о транспорте. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_tours_submenu(message: Message, bot: Bot, state: FSMContext, tour_type: str) -> None:
    """Обработчик подменю экскурсий."""
    logger.debug(f"User {message.from_user.id} selected tour type: {tour_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_tours_submenu(message, bot, lang, city_id, tour_type)
    except Exception as e:
        logger.error(f"Error in {tour_type} tours: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'tours_error',
            'Не удалось загрузить информацию об экскурсиях. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_spa_submenu(message: Message, bot: Bot, state: FSMContext, service_type: str) -> None:
    """Обработчик подменю SPA и ухода."""
    logger.debug(f"User {message.from_user.id} selected SPA service: {service_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_spa_submenu(message, bot, lang, city_id, service_type)
    except Exception as e:
        logger.error(f"Error in {service_type} SPA service: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'spa_error',
            'Не удалось загрузить информацию об услугах. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_hotels_submenu(message: Message, bot: Bot, state: FSMContext, accommodation_type: str) -> None:
    """Обработчик подменю отелей."""
    logger.debug(f"User {message.from_user.id} selected accommodation type: {accommodation_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_hotels_submenu(message, bot, lang, city_id, accommodation_type)
    except Exception as e:
        logger.error(f"Error in {accommodation_type} accommodation: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'hotels_error',
            'Не удалось загрузить информацию о размещении. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_shops_submenu(message: Message, bot: Bot, state: FSMContext, shop_type: str) -> None:
    """Обработчик подменю магазинов и услуг."""
    logger.debug(f"User {message.from_user.id} selected shop type: {shop_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await on_shops_submenu(message, bot, lang, city_id, shop_type)
    except Exception as e:
        logger.error(f"Error in {shop_type} shops: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'shops_error',
            'Не удалось загрузить информацию о магазинах. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('choose_language', '') for t in translations.values()]))
async def handle_choose_language(message: Message, bot: Bot, state: FSMContext):
    """Обработчик кнопки выбора языка."""
    await on_language_select(message, bot, state)


# --- Navigation Handlers ---
@main_menu_router.callback_query(F.data.startswith('prev_page_'))
async def handle_prev_page(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    """Обработчик кнопки 'Назад' для постраничной навигации."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(callback_query.from_user.id)
        
        # Get page type and page number from callback_data
        # Format: "page_{page_type}_{page_number}"
        _, page_type, page_number = callback_query.data.split("_")
        page_number = int(page_number)
        
        if page_type == "places":
            await show_places_page(callback_query, bot, lang, city_id, page_number)
        elif page_type == "offers":
            await show_offers_page(callback_query, bot, lang, city_id, page_number)
            
    except Exception as e:
        logger.error(f"Error in page navigation: {e}", exc_info=True)
        await callback_query.answer(
            translations.get(lang, {}).get(
                'navigation_error',
                'Произошла ошибка при загрузке страницы. Пожалуйста, попробуйте еще раз.'
            ),
            show_alert=True
        )


@main_menu_router.callback_query(F.data.startswith("item_"))
async def handle_item_selection(callback_query: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    """Обработчик выбора элемента из списка (заведение, предложение и т.д.)."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем тип элемента и его ID из callback_data
        # Формат: "item_{item_type}_{item_id}"
        _, item_type, item_id = callback_query.data.split("_")
        
        if item_type == "place":
            await show_place_details(callback_query, bot, lang, item_id)
        elif item_type == "offer":
            await show_offer_details(callback_query, bot, lang, item_id)
            
    except Exception as e:
        logger.error(f"Error in item selection: {e}", exc_info=True)
        await callback_query.answer(
            translations.get(lang, {}).get(
                'item_selection_error',
                'Произошла ошибка при загрузке информации. Пожалуйста, попробуйте еще раз.'
            ),
            show_alert=True
        )


@main_menu_router.callback_query(F.data == "back_to_list")
async def handle_back_to_list(callback_query: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Назад к списку'."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(callback_query.from_user.id)
        
        # Получаем текущую категорию из состояния
        current_category = user_data.get('current_category')
        if not current_category:
            raise ValueError("No current category in state")
            
        # Показываем список элементов выбранной категории
        await show_category_items(callback_query.message, bot, lang, city_id, current_category)
        
    except Exception as e:
        logger.error(f"Error going back to list: {e}", exc_info=True)
        await callback_query.answer(
            translations.get(lang, {}).get(
                'back_to_list_error',
                'Не удалось вернуться к списку. Пожалуйста, попробуйте еще раз.'
            ),
            show_alert=True
        )


@main_menu_router.callback_query(F.data == "main_menu")
async def handle_back_to_main_menu(callback_query: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Главное меню'."""
    try:
        await main_menu(callback_query.message, bot, state)
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}", exc_info=True)
        await callback_query.answer(
            translations.get('ru', {}).get(
                'main_menu_error',
                'Не удалось вернуться в главное меню. Пожалуйста, попробуйте еще раз.'
            ),
            show_alert=True
        )


# --- Command Handlers ---
@main_menu_router.message(CommandStart())
async def handle_start_command(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик команды /start."""
    await get_start(message, bot, state)


@main_menu_router.message(Command("help"))
@main_menu_router.message(F.text.in_([t.get('help_button', '') for t in translations.values()]))
async def handle_help_command(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик команды /help и кнопки помощи."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    help_text = translations.get(lang, {}).get(
        'help_text',
        'Здесь будет справка по использованию бота.'
    )
    await message.answer(help_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('help_button', '') for t in translations.values()]))
async def handle_help(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Помощь'."""
    logger.debug(f"User {message.from_user.id} requested help")
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        help_text = translations.get(lang, {}).get(
            'help_text',
            'Здесь будет справка по использованию бота.'
        )
        await message.answer(help_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in help handler: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при загрузке справки. Пожалуйста, попробуйте позже.",
            parse_mode="HTML"
        )


@main_menu_router.message(F.text.in_([t.get('language_button', '') for t in translations.values()]))
async def handle_choose_language(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки выбора языка."""
    logger.debug(f"User {message.from_user.id} wants to change language")
    await on_language_select(message, bot, state)


@main_menu_router.message(F.text.in_([t.get('nearest_places', '') for t in translations.values()]))
async def handle_nearest_places(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Ближайшие заведения'."""
    logger.debug(f"User {message.from_user.id} requested nearest places")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_nearest_v2(message, bot, lang, city_id)
    except Exception as e:
        logger.error(f"Error showing nearest places: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'nearest_places_error',
            'Не удалось загрузить ближайшие заведения. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([t.get('back_to_categories', '') for t in translations.values()]))
async def handle_back_to_categories(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Назад к категориям'."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    await show_categories_v2(message, bot, lang)


@main_menu_router.message(F.text.in_([t.get('transport_submenu', '') for t in translations.values()]))
async def handle_transport_submenu(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю транспорта."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_transport_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['tours_group', 'tours_private']]
))
async def handle_tours_submenu(message: Message, bot: Bot, state: FSMContext):
    """Обработчик подменю экскурсий."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_tours_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['spa_salon', 'spa_massage', 'spa_sauna']]
))
async def handle_spa_submenu(message: Message, bot: Bot, state: FSMContext):
    """Обработчик подменю SPA."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_spa_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['hotels_hotels', 'hotels_apartments']]
))
async def handle_hotels_submenu(message: Message, bot: Bot, state: FSMContext):
    """Обработчик подменю отелей."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_hotels_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['shops_shops', 'shops_services']]
))
async def handle_shops_submenu(message: Message, bot: Bot, state: FSMContext):
    """Обработчик подменю магазинов и услуг."""
    if not await ensure_policy_accepted(message, bot, state):
        return
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_shops_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_([t.get('back_to_main_menu', '') for t in translations.values()]))
async def handle_back_to_main_menu(message: Message, bot: Bot, state: FSMContext):
    """Обработчик кнопки 'Назад в главное меню'."""
    await get_start(message, bot, state)
