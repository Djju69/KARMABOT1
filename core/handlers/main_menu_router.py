from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union, cast

from aiogram import Bot, F, Router, html
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, Update, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from ..services.profile import profile_service
from ..utils.locales_v2 import translations
from .basic import (
    ensure_policy_accepted, feedback_user, get_file, get_hello, get_inline,
    get_location, get_photo, get_start, get_video, hiw_user, main_menu,
    on_language_select, open_cabinet, user_regional_rest
)
from .user_profile import show_profile

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

# Реализованные функции вместо заглушек
async def show_places_page(callback_query: CallbackQuery, bot: Bot, lang: str, city_id: int, page: int = 1):
    """Показывает страницу мест с пагинацией"""
    try:
        from core.handlers.category_handlers_v2 import show_catalog_page
        await show_catalog_page(bot, callback_query.message.chat.id, lang, 'places', 'all', page, city_id)
    except Exception as e:
        logger.error(f"Error in show_places_page: {e}")
        await callback_query.answer("Ошибка загрузки мест", show_alert=True)

async def show_offers_page(callback_query: CallbackQuery, bot: Bot, lang: str, city_id: int, page: int = 1):
    """Показывает страницу предложений с пагинацией"""
    try:
        from core.handlers.category_handlers_v2 import show_catalog_page
        await show_catalog_page(bot, callback_query.message.chat.id, lang, 'offers', 'all', page, city_id)
    except Exception as e:
        logger.error(f"Error in show_offers_page: {e}")
        await callback_query.answer("Ошибка загрузки предложений", show_alert=True)

async def show_place_details(callback_query: CallbackQuery, bot: Bot, lang: str, place_id: str):
    """Показывает детали места"""
    try:
        from core.database.db_v2 import db_v2
        place = db_v2.get_card_by_id(int(place_id))
        
        if not place:
            await callback_query.answer("Место не найдено", show_alert=True)
            return
            
        # Формируем сообщение с деталями
        details_text = f"""
🏢 <b>{place.get('name', 'Название не указано')}</b>

📍 <b>Адрес:</b> {place.get('address', 'Не указан')}
📞 <b>Телефон:</b> {place.get('phone', 'Не указан')}
⭐ <b>Рейтинг:</b> {place.get('rating', 'Н/Д')}

📝 <b>Описание:</b>
{place.get('description', 'Описание отсутствует')}

💎 <b>Скидка:</b> {place.get('discount', 'Н/Д')}%
        """
        
        # Клавиатура с действиями
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📍 Показать на карте", callback_data=f"map_{place_id}")],
            [InlineKeyboardButton(text="📱 QR-код", callback_data=f"qr_{place_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_list")]
        ])
        
        await callback_query.message.edit_text(
            details_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in show_place_details: {e}")
        await callback_query.answer("Ошибка загрузки деталей", show_alert=True)

async def show_offer_details(callback_query: CallbackQuery, bot: Bot, lang: str, offer_id: str):
    """Показывает детали предложения"""
    try:
        from core.database.db_v2 import db_v2
        offer = db_v2.get_card_by_id(int(offer_id))
        
        if not offer:
            await callback_query.answer("Предложение не найдено", show_alert=True)
            return
            
        # Формируем сообщение с деталями предложения
        details_text = f"""
🎁 <b>{offer.get('name', 'Предложение не указано')}</b>

💰 <b>Цена:</b> {offer.get('price', 'Н/Д')}
📅 <b>Действует до:</b> {offer.get('valid_until', 'Не указано')}
⭐ <b>Рейтинг:</b> {offer.get('rating', 'Н/Д')}

📝 <b>Описание:</b>
{offer.get('description', 'Описание отсутствует')}

💎 <b>Скидка:</b> {offer.get('discount', 'Н/Д')}%
        """
        
        # Клавиатура с действиями
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Активировать", callback_data=f"activate_{offer_id}")],
            [InlineKeyboardButton(text="📱 QR-код", callback_data=f"qr_{offer_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_list")]
        ])
        
        await callback_query.message.edit_text(
            details_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in show_offer_details: {e}")
        await callback_query.answer("Ошибка загрузки деталей предложения", show_alert=True)

async def show_category_items(message: Message, bot: Bot, lang: str, city_id: int, category: str):
    """Показывает элементы категории"""
    try:
        from core.handlers.category_handlers_v2 import show_catalog_page
        await show_catalog_page(bot, message.chat.id, lang, category, 'all', 1, city_id)
    except Exception as e:
        logger.error(f"Error in show_category_items: {e}")
        await message.answer("Ошибка загрузки элементов категории")

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

@main_menu_router.message(F.text.in_([
    t.get('choose_category', '') for t in translations.values()
] + [
    t.get('menu.categories', '') for t in translations.values()
] + [
    'КАТЕГОРИИ', 'Категории', 'CATEGORIES', 'Categories', '🗂️ Категории'
]))
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


@main_menu_router.message(F.text.in_([
    t.get('profile', '') for t in translations.values()
] + [
    t.get('menu.profile', '') for t in translations.values()
]))
async def handle_profile_button(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки профиля пользователя."""
    logger.debug(f"User {message.from_user.id} opened profile")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Используем обработчик кабинета напрямую
        from core.handlers.cabinet_router import user_cabinet_handler
        await user_cabinet_handler(message, state)
    except Exception as e:
        logger.error(f"Error in profile handling: {e}", exc_info=True)
        
        # Fallback - показываем базовую информацию о пользователе
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем информацию о пользователе
        user_name = message.from_user.full_name or "Пользователь"
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
        
        # Показываем базовую информацию
        profile_text = (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"🆔 <b>ID:</b> {user_id}\n"
            f"👤 <b>Имя:</b> {user_name}\n"
            f"📱 <b>Username:</b> {username}\n"
            f"🌐 <b>Язык:</b> {lang.upper()}\n\n"
            f"💡 <b>Доступные функции:</b>\n"
            f"• 📊 Карма и достижения\n"
            f"• 📋 Управление картами\n"
            f"• 🔔 Уведомления\n"
            f"• ⚙️ Настройки\n\n"
            f"🚧 <i>Полный функционал кабинета будет доступен после настройки базы данных.</i>"
        )
        
        # Создаем простую клавиатуру
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="◀️ Назад")],
                [KeyboardButton(text="📊 Карма"), KeyboardButton(text="📋 Моя карта")],
                [KeyboardButton(text="🔔 Уведомления"), KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")


@main_menu_router.message(F.text.in_(["👑 Админ кабинет", "Админ кабинет"]))
async def handle_admin_cabinet_button(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки админ-кабинета."""
    logger.debug(f"User {message.from_user.id} opened admin cabinet")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Проверяем права доступа
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав для доступа к админ-кабинету")
            return
        
        # Импортируем и вызываем админ-кабинет
        from core.handlers.admin_cabinet import admin_cabinet_handler
        await admin_cabinet_handler(message, state)
        
    except Exception as e:
        logger.error(f"Error in admin cabinet handling: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при открытии админ-кабинета. Пожалуйста, попробуйте позже.")


@main_menu_router.message(F.text.in_([
    t.get('help', '') for t in translations.values()
] + [
    t.get('menu.help', '') for t in translations.values()
]))
async def handle_help(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Помощь' - новая справочная система."""
    logger.debug(f"User {message.from_user.id} requested help")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Импортируем сервис помощи
        from ..services.help_service import HelpService
        help_service = HelpService()
        
        # Получаем справочное сообщение
        help_message = await help_service.get_help_message(message.from_user.id)
        
        # Отправляем сообщение с поддержкой HTML
        await message.answer(
            help_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error showing help: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'help_error', 
            'Не удалось загрузить справку. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

# Favorites (v4.2.5) — real implementation
@main_menu_router.message(F.text.in_([t.get('menu.favorites', '') for t in translations.values()]))
async def handle_favorites(message: Message, bot: Bot, state: FSMContext) -> None:
    """Показывает список избранных заведений пользователя."""
    logger.debug(f"User {message.from_user.id} opened favorites")
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    
    from core.services.favorites_service import favorites_service
    
    # Получаем избранные заведения
    favorites = await favorites_service.get_user_favorites(message.from_user.id, limit=10)
    
    if not favorites:
        empty_text = translations.get(lang, {}).get(
            'favorites_empty',
            '⭐ Избранные\n\nУ вас пока нет избранных заведений.\nДобавляйте понравившиеся места в избранное!'
        )
        await message.answer(empty_text)
        return
    
    # Формируем список избранных
    response = translations.get(lang, {}).get(
        'favorites_title',
        '⭐ Избранные заведения'
    ) + "\n\n"
    
    for i, fav in enumerate(favorites, 1):
        name = fav.get('name', 'Без названия')
        category = fav.get('category_name', 'Другое')
        address = fav.get('address', 'Адрес не указан')
        
        response += f"{i}. **{name}**\n"
        response += f"   📂 {category}\n"
        response += f"   📍 {address}\n\n"
    
    # Добавляем кнопки управления
    from core.keyboards.inline_v2 import get_favorites_keyboard
    keyboard = get_favorites_keyboard(lang)
    
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")


# Invite friends (reply menu with 3 items)
@main_menu_router.message(F.text.in_([
    t.get('menu.invite_friends', '') for t in translations.values()
]))
async def handle_invite_friends_menu(message: Message, bot: Bot, state: FSMContext) -> None:
    """Показывает меню "Пригласить друзей" (3 пункта)."""
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    logger.debug(f"User {message.from_user.id} opened Invite Friends menu")

    back_text = translations.get(lang, {}).get('back_to_main_menu', '🏠 Главное меню')
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Моя ссылка"), KeyboardButton(text="📋 Приглашённые"), KeyboardButton(text="💵 Доходы")],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )

    await message.answer("👥 Пригласить друзей", reply_markup=kb, parse_mode="HTML")


# Real implementation for invite submenu actions
@main_menu_router.message(F.text.in_(["🔗 Моя ссылка"]))
async def handle_invite_my_link(message: Message, bot: Bot, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    
    from core.services.referral_service import referral_service
    from core.settings import settings
    
    # Генерируем реферальную ссылку
    bot_username = (await bot.get_me()).username
    referral_link = referral_service.generate_referral_link(message.from_user.id, bot_username)
    
    # Получаем статистику
    stats = await referral_service.get_referral_stats(message.from_user.id)
    
    response = translations.get(lang, {}).get(
        'referral_link_title',
        '🔗 Ваша реферальная ссылка'
    ) + "\n\n"
    
    response += f"<code>{referral_link}</code>\n\n"
    response += translations.get(lang, {}).get(
        'referral_stats',
        '📊 Статистика:'
    ) + "\n"
    response += f"• Приглашено: {stats['total_referrals']}\n"
    response += f"• Активных: {stats['active_referrals']}\n"
    response += f"• Заработано: {stats['total_earnings']} баллов\n\n"
    
    response += translations.get(lang, {}).get(
        'referral_instructions',
        '💡 Поделитесь ссылкой с друзьями и получайте бонусы за каждого приглашенного!'
    )
    
    await message.answer(response, parse_mode="HTML")


@main_menu_router.message(F.text.in_(["📋 Приглашённые"]))
async def handle_invite_list(message: Message, bot: Bot, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    
    from core.services.referral_service import referral_service
    
    # Получаем список приглашенных
    referrals = await referral_service.get_user_referrals(message.from_user.id)
    
    if not referrals:
        empty_text = translations.get(lang, {}).get(
            'referrals_empty',
            '📋 Приглашённые\n\nВы пока никого не пригласили.\nПоделитесь своей ссылкой с друзьями!'
        )
        await message.answer(empty_text)
        return
    
    response = translations.get(lang, {}).get(
        'referrals_title',
        '📋 Ваши приглашённые'
    ) + "\n\n"
    
    for i, ref in enumerate(referrals, 1):
        name = ref.get('first_name', '') or ref.get('username', 'Пользователь')
        created_at = ref.get('created_at', '')
        reward = ref.get('reward_points', 0)
        
        response += f"{i}. **{name}**\n"
        response += f"   📅 {created_at}\n"
        response += f"   💰 +{reward} баллов\n\n"
    
    await message.answer(response, parse_mode="Markdown")


@main_menu_router.message(F.text.in_(["💵 Доходы"]))
async def handle_invite_earnings(message: Message, bot: Bot, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    
    from core.services.referral_service import referral_service
    
    # Получаем статистику доходов
    stats = await referral_service.get_referral_stats(message.from_user.id)
    
    response = translations.get(lang, {}).get(
        'earnings_title',
        '💵 Доходы от рефералов'
    ) + "\n\n"
    
    response += f"💰 **Всего заработано:** {stats['total_earnings']} баллов\n"
    response += f"👥 **Приглашено:** {stats['total_referrals']} человек\n"
    response += f"🔥 **Активных:** {stats['active_referrals']} за 30 дней\n\n"
    
    if stats['total_referrals'] > 0:
        avg_earnings = stats['total_earnings'] / stats['total_referrals']
        response += f"📊 **Средний доход:** {avg_earnings:.1f} баллов с человека\n\n"
    
    response += translations.get(lang, {}).get(
        'earnings_tip',
        '💡 Приглашайте больше друзей, чтобы увеличить доходы!'
    )
    
    await message.answer(response, parse_mode="Markdown")


# --- Policy consent callbacks ---
@main_menu_router.callback_query(F.data == "accept_policy")
async def on_accept_policy(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    try:
        await state.update_data(policy_accepted=True)
        await callback.answer("✅ Принято")
        try:
            await callback.message.edit_text("✅ Политика принята. Продолжайте пользоваться ботом.")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error in accept_policy: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка", show_alert=True)


@main_menu_router.callback_query(F.data == "decline_policy")
async def on_decline_policy(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    await callback.answer("❌ Отклонено", show_alert=False)
    try:
        await callback.message.edit_text("❌ Вы отклонили политику. Некоторые функции будут недоступны.")
    except Exception:
        pass


@main_menu_router.message(F.text.in_([t.get('choose_language', '') for t in translations.values()]))
async def handle_choose_language(message: Message, bot: Bot, state: FSMContext):
    """Обработчик кнопки выбора языка."""
    logger.debug(f"User {message.from_user.id} chose language selection")
    try:
        # Get current language from state
        user_data = await state.get_data()
        current_lang = user_data.get('lang', 'ru')
        
        # Show inline keyboard with language selection
        from core.keyboards.inline_v2 import get_language_inline
        # Получаем текст на текущем языке
        lang_text = translations.get(current_lang, {}).get(
            'choose_language_text', 
            'Выберите язык:'
        )
        
        await message.answer(
            lang_text,
            reply_markup=get_language_inline(active=current_lang)
        )
    except Exception as e:
        logger.error(f"Error showing language selection: {e}", exc_info=True)
        await message.answer("❌ Не удалось загрузить выбор языка. Пожалуйста, попробуйте позже.")


@main_menu_router.message(F.text.in_([t.get('show_nearest', '') for t in translations.values()]))
async def handle_show_nearest(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Ближайшие заведения' с запросом геолокации."""
    logger.debug(f"User {message.from_user.id} requested nearest places")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Запрашиваем геолокацию
        from core.keyboards.reply_v2 import get_location_request_keyboard
        location_text = translations.get(lang, {}).get(
            'request_location',
            '📍 Поделитесь своим местоположением, чтобы найти ближайшие заведения:'
        )
        
        await message.answer(
            location_text,
            reply_markup=get_location_request_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Error requesting location: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'nearest_error', 
            'Не удалось загрузить ближайшие заведения. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.location)
async def handle_location(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик геолокации для поиска ближайших заведений."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем координаты
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        logger.info(f"User {message.from_user.id} shared location: {latitude}, {longitude}")
        
        # Ищем ближайшие заведения
        from core.database.db_v2 import db_v2
        all_cards = db_v2.get_cards_by_category('all', status='published', limit=50)
        
        if not all_cards:
            no_places_text = translations.get(lang, {}).get(
                'no_places_found',
                '❌ Поблизости не найдено заведений. Попробуйте другой район.'
            )
            await message.answer(no_places_text)
            return
        
        # Вычисляем расстояния и сортируем
        places_with_distance = []
        for card in all_cards:
            if card.get('latitude') and card.get('longitude'):
                distance = calculate_distance(
                    latitude, longitude,
                    card['latitude'], card['longitude']
                )
                places_with_distance.append((card, distance))
        
        # Сортируем по расстоянию
        places_with_distance.sort(key=lambda x: x[1])
        
        # Показываем топ-5 ближайших
        nearest_places = places_with_distance[:5]
        
        if not nearest_places:
            no_places_text = translations.get(lang, {}).get(
                'no_places_found',
                '❌ Поблизости не найдено заведений. Попробуйте другой район.'
            )
            await message.answer(no_places_text)
            return
        
        # Формируем сообщение
        result_text = translations.get(lang, {}).get(
            'nearest_places_found',
            '📍 <b>Ближайшие заведения:</b>\n\n'
        )
        
        for i, (place, distance) in enumerate(nearest_places, 1):
            distance_text = f"{distance:.1f} км" if distance >= 1 else f"{distance*1000:.0f} м"
            result_text += f"{i}. <b>{place.get('name', 'Название не указано')}</b>\n"
            result_text += f"   📍 {place.get('address', 'Адрес не указан')}\n"
            result_text += f"   📏 {distance_text}\n"
            result_text += f"   💎 Скидка: {place.get('discount', 'Н/Д')}%\n\n"
        
        # Клавиатура с действиями
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=translations.get(lang, {}).get('back_to_main_menu', '◀️ Главное меню'))],
                [KeyboardButton(text=translations.get(lang, {}).get('choose_category', '🗂️ Категории'))]
            ],
            resize_keyboard=True
        )
        
        await message.answer(result_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error processing location: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'location_error',
            '❌ Ошибка обработки геолокации. Попробуйте еще раз.'
        )
        await message.answer(error_text)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычисляет расстояние между двумя точками в километрах (формула гаверсинуса)."""
    import math
    
    # Радиус Земли в километрах
    R = 6371.0
    
    # Преобразуем в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Разности координат
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Формула гаверсинуса
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


@main_menu_router.message(F.text.in_([
    t.get('category_restaurants', '') for t in translations.values()
] + [
    '🍽 restaurants', '🍽 Restaurants'
]))
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


@main_menu_router.message(F.text.in_([
    t.get('category_spa', '') for t in translations.values()
] + [
    '🧖‍♀ spa', '🧖‍♀ Spa'
]))
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


@main_menu_router.message(F.text.in_([
    t.get('category_hotels', '') for t in translations.values()
] + [
    '🏨 hotels', '🏨 Hotels'
]))
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


@main_menu_router.message(F.text.in_([
    t.get('category_transport', '') for t in translations.values()
] + [
    '🚗 transport', '🚗 Transport'
]))
async def handle_transport(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Транспорт'."""
    logger.debug(f"User {message.from_user.id} selected Transport category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        # 'on_transport' не требует city_id
        await on_transport(message, bot, lang)
    except Exception as e:
        logger.error(f"Error in transport category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'transport_error', 
            'Не удалось загрузить информацию о транспорте. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([
    t.get('category_tours', '') for t in translations.values()
] + [
    '🚶‍♂ tours', '🚶‍♂ Tours'
]))
async def handle_tours(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Экскурсии'."""
    logger.debug(f"User {message.from_user.id} selected Tours category")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        # 'on_tours' не требует city_id
        await on_tours(message, bot, lang)
    except Exception as e:
        logger.error(f"Error in tours category: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'tours_error', 
            'Не удалось загрузить список экскурсий. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([
    t.get('category_shops_services', '') for t in translations.values()
] + [
    '🛍 shops', '🛍 Shops'
]))
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


@main_menu_router.message(F.text.in_([t.get('choose_district', '') for t in translations.values()]))
async def handle_choose_district(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'По районам' - показывает группировку по районам."""
    logger.debug(f"User {message.from_user.id} requested districts")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        
        # Получаем все заведения
        from core.database.db_v2 import db_v2
        all_cards = db_v2.get_cards_by_category('all', status='published', limit=1000)
        
        if city_id is not None:
            all_cards = [c for c in all_cards if c.get('city_id') == city_id]
        
        # Группируем по районам
        districts = {}
        for card in all_cards:
            district = card.get('district', 'Не указан')
            if district not in districts:
                districts[district] = []
            districts[district].append(card)
        
        if not districts:
            no_districts_text = translations.get(lang, {}).get(
                'no_districts_found',
                '❌ Заведений по районам не найдено.'
            )
            await message.answer(no_districts_text)
            return
        
        # Формируем сообщение с районами
        districts_text = translations.get(lang, {}).get(
            'districts_found',
            '🌆 <b>Заведения по районам:</b>\n\n'
        )
        
        for district, cards in sorted(districts.items()):
            districts_text += f"📍 <b>{district}</b> ({len(cards)} заведений)\n"
        
        # Создаем клавиатуру с районами
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard_rows = []
        
        # Группируем кнопки по 2 в ряд
        district_list = list(districts.keys())
        for i in range(0, len(district_list), 2):
            row = [KeyboardButton(text=district_list[i])]
            if i + 1 < len(district_list):
                row.append(KeyboardButton(text=district_list[i + 1]))
            keyboard_rows.append(row)
        
        # Добавляем кнопку "Назад"
        keyboard_rows.append([KeyboardButton(text=translations.get(lang, {}).get('back_to_main_menu', '◀️ Главное меню'))])
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=keyboard_rows,
            resize_keyboard=True
        )
        
        await message.answer(districts_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing districts: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'districts_error',
            '❌ Ошибка загрузки районов. Попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([t.get('qr_codes', '') for t in translations.values()]))
async def handle_qr_codes(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'QR-коды' - показывает QR-коды пользователя."""
    logger.debug(f"User {message.from_user.id} requested QR codes")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем QR-коды пользователя
        from core.database.db_v2 import db_v2
        user_qr_codes = db_v2.get_user_qr_codes(message.from_user.id)
        
        if not user_qr_codes:
            no_qr_text = translations.get(lang, {}).get(
                'no_qr_codes',
                '📱 У вас пока нет QR-кодов.\n\nСоздайте QR-код для получения скидок в заведениях-партнерах.'
            )
            
            # Клавиатура для создания QR-кода
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=translations.get(lang, {}).get('create_qr_code', '📱 Создать QR-код'))],
                    [KeyboardButton(text=translations.get(lang, {}).get('back_to_main_menu', '◀️ Главное меню'))]
                ],
                resize_keyboard=True
            )
            
            await message.answer(no_qr_text, reply_markup=keyboard)
            return
        
        # Формируем сообщение с QR-кодами
        qr_text = translations.get(lang, {}).get(
            'qr_codes_list',
            '📱 <b>Ваши QR-коды:</b>\n\n'
        )
        
        for i, qr_code in enumerate(user_qr_codes[:5], 1):  # Показываем только первые 5
            status_emoji = "✅" if qr_code.get('is_active') else "❌"
            qr_text += f"{i}. {status_emoji} <b>{qr_code.get('name', 'QR-код')}</b>\n"
            qr_text += f"   💎 Скидка: {qr_code.get('discount', 'Н/Д')}%\n"
            qr_text += f"   📅 Создан: {qr_code.get('created_at', 'Н/Д')}\n\n"
        
        if len(user_qr_codes) > 5:
            qr_text += f"... и еще {len(user_qr_codes) - 5} QR-кодов"
        
        # Клавиатура с действиями
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=translations.get(lang, {}).get('create_qr_code', '📱 Создать QR-код'))],
                [KeyboardButton(text=translations.get(lang, {}).get('my_qr_codes', '📋 Мои QR-коды'))],
                [KeyboardButton(text=translations.get(lang, {}).get('back_to_main_menu', '◀️ Главное меню'))]
            ],
            resize_keyboard=True
        )
        
        await message.answer(qr_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing QR codes: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'qr_codes_error',
            '❌ Ошибка загрузки QR-кодов. Попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([t.get('create_qr_code', '') for t in translations.values()]))
async def handle_create_qr_code(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик создания QR-кода."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Генерируем QR-код
        import qrcode
        import io
        from aiogram.types import InputFile
        
        # Создаем уникальный код
        import uuid
        qr_id = str(uuid.uuid4())[:8]
        
        # Создаем QR-код
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"KARMA_QR:{qr_id}:{message.from_user.id}")
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем в байты
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        # Отправляем QR-код
        qr_text = translations.get(lang, {}).get(
            'qr_code_created',
            f'📱 <b>Ваш QR-код создан!</b>\n\n'
            f'🆔 Код: {qr_id}\n'
            f'💎 Скидка: 10%\n'
            f'📅 Действует: 30 дней\n\n'
            f'Покажите этот QR-код в заведениях-партнерах для получения скидки.'
        )
        
        await message.answer_photo(
            photo=InputFile(bio, filename=f"qr_{qr_id}.png"),
            caption=qr_text,
            parse_mode="HTML"
        )
        
        # Сохраняем QR-код в БД
        from core.database.db_v2 import db_v2
        db_v2.create_user_qr_code(
            user_id=message.from_user.id,
            qr_id=qr_id,
            name=f"QR-код {qr_id}",
            discount=10
        )
        
    except Exception as e:
        logger.error(f"Error creating QR code: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'qr_create_error',
            '❌ Ошибка создания QR-кода. Попробуйте позже.'
        )
        await message.answer(error_text)

@main_menu_router.message(F.text.in_([t.get('back_to_main_menu', '') for t in translations.values()]))
async def handle_back_to_main_menu(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'В главное меню' - возвращает в главное меню."""
    logger.debug(f"User {message.from_user.id} clicked back to main menu")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Импортируем get_start из basic.py
        from core.handlers.basic import get_start
        await get_start(message, bot, state)
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось вернуться в главное меню. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


# Обработчики фильтров ресторанов
@main_menu_router.message(F.text.in_([
    t.get('filter_asia', '') for t in translations.values()
    if t.get('filter_asia')
]))
async def handle_restaurants_asia(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик фильтра 'Азиатская кухня' для ресторанов."""
    logger.debug(f"User {message.from_user.id} selected Asian cuisine filter")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_catalog_page(bot, message.chat.id, lang, 'restaurants', 'asia', page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"Error in Asian cuisine filter: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось загрузить рестораны. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([
    t.get('filter_europe', '') for t in translations.values()
    if t.get('filter_europe')
]))
async def handle_restaurants_europe(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик фильтра 'Европейская кухня' для ресторанов."""
    logger.debug(f"User {message.from_user.id} selected European cuisine filter")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_catalog_page(bot, message.chat.id, lang, 'restaurants', 'europe', page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"Error in European cuisine filter: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось загрузить рестораны. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([
    t.get('filter_street', '') for t in translations.values()
    if t.get('filter_street')
]))
async def handle_restaurants_street(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик фильтра 'Уличная еда' для ресторанов."""
    logger.debug(f"User {message.from_user.id} selected Street food filter")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_catalog_page(bot, message.chat.id, lang, 'restaurants', 'street', page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"Error in Street food filter: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось загрузить рестораны. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([
    t.get('filter_vege', '') for t in translations.values()
    if t.get('filter_vege')
]))
async def handle_restaurants_vegetarian(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик фильтра 'Вегетарианская кухня' для ресторанов."""
    logger.debug(f"User {message.from_user.id} selected Vegetarian cuisine filter")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_catalog_page(bot, message.chat.id, lang, 'restaurants', 'vege', page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"Error in Vegetarian cuisine filter: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось загрузить рестораны. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([
    t.get('restaurants_show_all', '') for t in translations.values()
    if t.get('restaurants_show_all')
]))
async def handle_restaurants_show_all(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Показать все' для ресторанов."""
    logger.debug(f"User {message.from_user.id} selected Show all restaurants")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        await show_catalog_page(bot, message.chat.id, lang, 'restaurants', 'all', page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"Error in Show all restaurants: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось загрузить рестораны. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")

@main_menu_router.message(F.text.in_([
    t.get('back_to_categories', '') for t in translations.values()
    if t.get('back_to_categories')
]))
async def handle_back_to_categories(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'К категориям' - показывает категории."""
    logger.debug(f"User {message.from_user.id} clicked back to categories")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Показываем категории
        from core.handlers.category_handlers_v2 import show_categories_v2
        await show_categories_v2(message, bot, state)
    except Exception as e:
        logger.error(f"Error showing categories: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось показать категории. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


@main_menu_router.message(F.text.in_([
    t.get('back', '') for t in translations.values()
    if t.get('back')
] + [
    t.get('back_to_main_menu', '') for t in translations.values()
    if t.get('back_to_main_menu')
]))
async def handle_back_to_main_menu(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик кнопки 'Назад' - возвращает в главное меню."""
    logger.debug(f"User {message.from_user.id} clicked back to main menu")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        # Возвращаемся в главное меню
        from core.handlers.basic import get_start
        await get_start(message, bot, state)
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'menu_error',
            'Не удалось вернуться в главное меню. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


# Обработчики подменю
@main_menu_router.message(F.text.in_([
    t.get('transport_bikes', '') for t in translations.values()
    if t.get('transport_bikes')
]))
async def handle_transport_bikes(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Аренда велосипедов'."""
    await handle_transport_submenu_typed(message, bot, state, 'bikes')


@main_menu_router.message(F.text.in_([
    t.get('transport_cars', '') for t in translations.values()
    if t.get('transport_cars')
]))
async def handle_transport_cars(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Аренда автомобилей'."""
    await handle_transport_submenu_typed(message, bot, state, 'cars')


@main_menu_router.message(F.text.in_([
    t.get('transport_bicycles', '') for t in translations.values()
    if t.get('transport_bicycles')
]))
async def handle_transport_bicycles(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Аренда велосипедов'."""
    await handle_transport_submenu_typed(message, bot, state, 'bicycles')


@main_menu_router.message(F.text.in_([
    t.get('tours_group', '') for t in translations.values()
    if t.get('tours_group')
]))
async def handle_group_tours(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Групповые экскурсии'."""
    await handle_tours_submenu_typed(message, bot, state, 'group')


@main_menu_router.message(F.text.in_([
    t.get('tours_private', '') for t in translations.values()
    if t.get('tours_private')
]))
async def handle_private_tours(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Индивидуальные экскурсии'."""
    await handle_tours_submenu_typed(message, bot, state, 'private')


@main_menu_router.message(F.text.in_([
    t.get('spa_massage', '') for t in translations.values()
    if t.get('spa_massage')
]))
async def handle_massage(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Массаж'."""
    await handle_spa_submenu_typed(message, bot, state, 'massage')


@main_menu_router.message(F.text.in_([
    t.get('spa_sauna', '') for t in translations.values()
    if t.get('spa_sauna')
]))
async def handle_sauna(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Сауна'."""
    await handle_spa_submenu_typed(message, bot, state, 'sauna')


@main_menu_router.message(F.text.in_([
    t.get('spa_salon', '') for t in translations.values()
    if t.get('spa_salon')
]))
async def handle_beauty_salon(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Салон красоты'."""
    await handle_spa_submenu_typed(message, bot, state, 'salon')


@main_menu_router.message(F.text.in_([
    t.get('hotels_hotels', '') for t in translations.values()
    if t.get('hotels_hotels')
]))
async def handle_hotels_list(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Отели'."""
    await handle_hotels_submenu_typed(message, bot, state, 'hotels')


@main_menu_router.message(F.text.in_([
    t.get('hotels_apartments', '') for t in translations.values()
    if t.get('hotels_apartments')
]))
async def handle_apartments(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Апартаменты'."""
    await handle_hotels_submenu_typed(message, bot, state, 'apartments')


@main_menu_router.message(F.text.in_([
    t.get('shops_shops', '') for t in translations.values()
    if t.get('shops_shops')
]))
async def handle_shops_list(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Магазины'."""
    await handle_shops_submenu_typed(message, bot, state, 'shops')


@main_menu_router.message(F.text.in_([
    t.get('shops_services', '') for t in translations.values()
    if t.get('shops_services')
]))
async def handle_services(message: Message, bot: Bot, state: FSMContext) -> None:
    """Обработчик подменю 'Услуги'."""
    await handle_shops_submenu_typed(message, bot, state, 'services')


# Вспомогательные функции для обработки подменю
async def handle_transport_submenu_typed(message: Message, bot: Bot, state: FSMContext, transport_type: str) -> None:
    """Обработчик подменю транспорта."""
    logger.debug(f"User {message.from_user.id} selected transport type: {transport_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        # Внутренний обработчик сам определяет sub_slug по тексту кнопки
        await on_transport_submenu(message, bot, lang, city_id, state)
    except Exception as e:
        logger.error(f"Error in {transport_type} transport: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'transport_error',
            'Не удалось загрузить информацию о транспорте. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_tours_submenu_typed(message: Message, bot: Bot, state: FSMContext, tour_type: str) -> None:
    """Обработчик подменю экскурсий."""
    logger.debug(f"User {message.from_user.id} selected tour type: {tour_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        # Внутренний обработчик сам определяет sub_slug по тексту кнопки
        await on_tours_submenu(message, bot, lang, city_id, state)
    except Exception as e:
        logger.error(f"Error in {tour_type} tours: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'tours_error',
            'Не удалось загрузить информацию об экскурсиях. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_spa_submenu_typed(message: Message, bot: Bot, state: FSMContext, service_type: str) -> None:
    """Обработчик подменю SPA и ухода."""
    logger.debug(f"User {message.from_user.id} selected SPA service: {service_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        # Внутренний обработчик сам определяет sub_slug по тексту кнопки
        await on_spa_submenu(message, bot, lang, city_id, state)
    except Exception as e:
        logger.error(f"Error in {service_type} SPA service: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'spa_error',
            'Не удалось загрузить информацию об услугах. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_hotels_submenu_typed(message: Message, bot: Bot, state: FSMContext, accommodation_type: str) -> None:
    """Обработчик подменю отелей."""
    logger.debug(f"User {message.from_user.id} selected accommodation type: {accommodation_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        # Внутренний обработчик сам определяет sub_slug по тексту кнопки
        await on_hotels_submenu(message, bot, lang, city_id, state)
    except Exception as e:
        logger.error(f"Error in {accommodation_type} accommodation: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'hotels_error',
            'Не удалось загрузить информацию о размещении. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


async def handle_shops_submenu_typed(message: Message, bot: Bot, state: FSMContext, shop_type: str) -> None:
    """Обработчик подменю магазинов и услуг."""
    logger.debug(f"User {message.from_user.id} selected shop type: {shop_type}")
    if not await ensure_policy_accepted(message, bot, state):
        return
        
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        city_id = await profile_service.get_city_id(message.from_user.id)
        # Внутренний обработчик сам определяет sub_slug по тексту кнопки
        await on_shops_submenu(message, bot, lang, city_id, state)
    except Exception as e:
        logger.error(f"Error in {shop_type} shops: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'shops_error',
            'Не удалось загрузить информацию о магазинах. Пожалуйста, попробуйте позже.'
        )
        await message.answer(error_text, parse_mode="HTML")


 


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
 


 


 


 


 


 


 


 


 


 


 
