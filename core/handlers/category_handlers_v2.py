"""
Enhanced category handlers with unified card rendering
Backward compatible with existing functionality
"""
from aiogram import Router, F, Bot as AioBot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram import Bot
import logging

from ..database.db_v2 import db_v2
from ..services.card_renderer import card_service
from ..utils.helpers import get_city_id_from_message
from ..keyboards.reply_v2 import (
    get_return_to_main_menu, 
    get_location_request_keyboard,
    get_categories_keyboard,
    get_transport_reply_keyboard,
    get_tours_reply_keyboard,
    get_spa_reply_keyboard,
    get_hotels_reply_keyboard,
    get_shops_reply_keyboard,
)
from ..keyboards.inline_v2 import (
    get_pagination_row,
    get_catalog_item_row,
    get_restaurant_filters_inline,
    get_categories_inline,
)
from ..utils.locales_v2 import get_text, get_all_texts
from ..utils.telemetry import log_event
from ..settings import settings
from ..services.profile import profile_service
from typing import Optional

logger = logging.getLogger(__name__)

# Router for category handlers
category_router = Router(name="category_router")

async def show_categories_v2(message: Message, bot: Bot, lang: str):
    """Показывает Reply-клавиатуру с 6 категориями согласно ТЗ с подсчетом заведений."""
    try:
        await log_event("categories_menu_shown", user=message.from_user, lang=lang)
        
        # Получаем категории из БД с подсчетом заведений
        categories = db_v2.get_categories(only_active=True)
        
        # Формируем текст с информацией о количестве заведений
        categories_text = get_text('choose_category', lang) + "\n\n"
        
        for category in categories:
            # Подсчитываем количество заведений в категории
            cards_count = len(db_v2.get_cards_by_category(category.slug, status='published', limit=1000))
            
            categories_text += f"{category.emoji} <b>{category.name}</b> ({cards_count})\n"
        
        await message.answer(
            text=categories_text,
            reply_markup=get_categories_keyboard(lang),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in show_categories_v2: {e}")
        await message.answer(
            get_text('catalog_error', lang),
            reply_markup=get_return_to_main_menu(lang)
        )


# --- Этап 2: Интеграция с сервисом каталога ---

async def show_cards(user_id: int, category: str, sub_slug: Optional[str] = None, page: int = 1):
    """
    Загружает и отображает карточки по фильтрам (унифицированная точка входа):
    - category: обязательный slug ('restaurants'|'spa'|'transport'|'hotels'|'tours'|'shops')
    - sub_slug: подкатегория (например 'asia', 'group', 'bikes'), по умолчанию 'all'
    - page: номер страницы (>=1)
    """
    try:
        bot = AioBot.get_current()
    except Exception:
        # В редких случаях контекст отсутствует — не выполняем
        return
    try:
        lang = await profile_service.get_lang(user_id) or 'ru'
    except Exception:
        lang = 'ru'
    try:
        city_id = await profile_service.get_city_id(user_id)
    except Exception:
        city_id = None
    await show_catalog_page(
        bot=bot,
        chat_id=user_id,
        lang=lang,
        slug=category,
        sub_slug=(sub_slug or 'all'),
        page=max(1, int(page or 1)),
        city_id=city_id,
    )
async def show_catalog_page(bot: Bot, chat_id: int, lang: str, slug: str, sub_slug: str = "all", page: int = 1, city_id: int | None = None, message_id: int | None = None):
    """
    Универсальный обработчик для отображения страницы каталога с фильтрацией по sub_slug.
    """
    try:
        # 1. Получение данных и фильтрация
        await log_event("catalog_query", slug=slug, sub_slug=sub_slug, page=page, city_id=city_id, lang=lang)
        all_cards = db_v2.get_cards_by_category(slug, status='published', limit=100)
        if city_id is not None and all_cards and 'city_id' in all_cards[0]:
            all_cards = [c for c in all_cards if c.get('city_id') == city_id]
        if sub_slug != "all" and all_cards and 'sub_slug' in all_cards[0]:
             all_cards = [c for c in all_cards if str(c.get('sub_slug') or '').lower() == sub_slug]

        # 2. Пагинация
        per_page = 5
        total_items = len(all_cards)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        cards_page = all_cards[(page - 1) * per_page:page * per_page]

        # 3. Рендеринг контента
        if not cards_page:
            text = get_text('catalog_empty_sub', lang)
            kb = None
        else:
            header = f"{get_text('catalog_found', lang)}: {total_items} | {get_text('catalog_page', lang)}. {page}/{total_pages}"
            text = header + "\n\n" + card_service.render_cards_list(cards_page, lang, max_cards=per_page)
            
            # 4. Сборка клавиатуры
            inline_rows = [get_catalog_item_row(c.get('id'), c.get('google_maps_url'), lang) for c in cards_page]
            pagination_row = [get_pagination_row(slug, page, total_pages, sub_slug)]
            kb_rows = inline_rows + pagination_row
            kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

        # 5. Отправка или редактирование сообщения
        if message_id:
            await bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        else:
            await bot.send_message(chat_id, text, reply_markup=kb)
        await log_event("catalog_rendered", slug=slug, sub_slug=sub_slug, page=page, total_items=total_items)

    except Exception as e:
        logger.error(f"show_catalog_page error for slug={slug}, sub_slug={sub_slug}: {e}")
        await bot.send_message(chat_id, get_text('catalog_error', lang))


async def on_restaurants(message: Message, bot: Bot, lang: str, city_id: int | None):
    # Показываем reply клавиатуру с фильтрами кухни
    from ..keyboards.reply_v2 import get_restaurants_reply_keyboard
    await log_event("category_open", user=message.from_user, slug="restaurants", lang=lang, city_id=city_id)
    await message.answer(
        text=get_text('restaurants_choose_cuisine', lang),
        reply_markup=get_restaurants_reply_keyboard(lang)
    )

async def on_spa(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Show SPA submenu (salon/massage/sauna)."""
    await log_event("category_open", user=message.from_user, slug="spa", lang=lang, city_id=city_id)
    await message.answer(get_text('spa_choose', lang), reply_markup=get_spa_reply_keyboard(lang))

async def on_hotels(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Show Hotels submenu (hotels/apartments)."""
    await log_event("category_open", user=message.from_user, slug="hotels", lang=lang, city_id=city_id)
    await message.answer(get_text('hotels_choose', lang), reply_markup=get_hotels_reply_keyboard(lang))

async def on_transport(message: Message, bot: Bot, lang: str):
    await log_event("category_open", user=message.from_user, slug="transport", lang=lang)
    await message.answer(get_text('transport_choose', lang), reply_markup=get_transport_reply_keyboard(lang))

async def on_tours(message: Message, bot: Bot, lang: str):
    await log_event("category_open", user=message.from_user, slug="tours", lang=lang)
    await message.answer(get_text('tours_choose', lang), reply_markup=get_tours_reply_keyboard(lang))


# --- Обработчики подменю --- 

async def on_transport_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Транспорт'."""
    sub_slug_map = {
        get_text('transport_bikes', lang): 'bikes',
        get_text('transport_cars', lang): 'cars',
        get_text('transport_bicycles', lang): 'bicycles'
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="transport", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='transport', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    await show_catalog_page(bot, message.chat.id, lang, 'transport', sub_slug, page=1, city_id=city_id)

async def on_tours_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Экскурсии'."""
    sub_slug_map = {
        get_text('tours_group', lang): 'group',
        get_text('tours_private', lang): 'private'
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="tours", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='tours', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    await show_catalog_page(bot, message.chat.id, lang, 'tours', sub_slug, page=1, city_id=city_id)

async def on_spa_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'SPA'."""
    sub_slug_map = {
        get_text('spa_salon', lang): 'salon',
        get_text('spa_massage', lang): 'massage',
        get_text('spa_sauna', lang): 'sauna',
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="spa", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='spa', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    await show_catalog_page(bot, message.chat.id, lang, 'spa', sub_slug, page=1, city_id=city_id)

async def on_hotels_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Отели'."""
    sub_slug_map = {
        get_text('hotels_hotels', lang): 'hotel',
        get_text('hotels_apartments', lang): 'apartments',
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="hotels", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='hotels', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    await show_catalog_page(bot, message.chat.id, lang, 'hotels', sub_slug, page=1, city_id=city_id)

async def on_shops(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Show Shops & Services submenu (shops/services)."""
    await log_event("category_open", user=message.from_user, slug="shops", lang=lang, city_id=city_id)
    await message.answer(get_text('shops_choose', lang), reply_markup=get_shops_reply_keyboard(lang))

async def on_shops_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Магазины и услуги'."""
    sub_slug_map = {
        get_text('shops_shops', lang): 'shops',
        get_text('shops_services', lang): 'services',
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="shops", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='shops', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    await show_catalog_page(bot, message.chat.id, lang, 'shops', sub_slug, page=1, city_id=city_id)

async def show_nearest_v2(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Enhanced nearest places handler"""
    t = get_all_texts(lang)
    
    city_hint = f" (город #{city_id})" if city_id else ""
    title = get_text('nearest_places_title', lang)
    request_text = get_text('nearest_places_request', lang)
    
    await message.answer(
        f"{title}**{city_hint}\n\n{request_text}",
        reply_markup=get_location_request_keyboard(lang)
    )

async def handle_location_v2(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Enhanced location handler with actual nearby search"""
    
    try:
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        logger.info(f"Received location: {latitude}, {longitude}")
        
        # Импортируем утилиты геопоиска
        from ..utils.geo import find_places_in_radius, format_distance
        
        # Получаем все опубликованные карточки с координатами
        all_cards = []
        categories = db_v2.get_categories(active_only=True)
        
        for category in categories:
            cards = db_v2.get_cards_by_category(category.slug, status='published', limit=50)
            # Добавляем информацию о категории к каждой карточке
            for card in cards:
                if isinstance(card, dict):
                    card['category_slug'] = category.slug
                    card['category_name'] = category.name
                else:
                    # Если card - это объект, конвертируем в dict
                    card_dict = dict(card) if hasattr(card, '__dict__') else card
                    card_dict['category_slug'] = category.slug
                    card_dict['category_name'] = category.name
                    card = card_dict
                all_cards.append(card)
        
        # Ищем ближайшие заведения в радиусе 5 км
        nearby_cards = find_places_in_radius(
            latitude=latitude,
            longitude=longitude,
            places=all_cards,
            radius_km=5.0,
            limit=10
        )
        
        if nearby_cards:
            response = get_text('nearest_places_found', lang) + "\n\n"
            
            # Группируем по категориям для лучшего отображения
            by_category = {}
            for card in nearby_cards:
                category = card.get('category_name', 'Другое')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(card)
            
            # Отображаем результаты по категориям
            for category_name, cards in by_category.items():
                response += f"**{category_name}:**\n"
                for card in cards:
                    distance_str = format_distance(card['distance_km'])
                    name = card.get('name', 'Без названия')
                    address = card.get('address', 'Адрес не указан')
                    response += f"• {name} - {distance_str}\n"
                    if address:
                        response += f"  📍 {address}\n"
                response += "\n"
            
            # Добавляем информацию о точности поиска
            count_text = get_text('nearest_places_count', lang).format(count=len(nearby_cards))
            tip_text = get_text('nearest_places_tip', lang)
            response += f"{count_text}\n{tip_text}"
            
        else:
            response = get_text('nearest_places_none', lang) + "\n\n"
            response += get_text('nearest_places_none_desc', lang)
        
        await log_event("nearest_results_shown", user=message.from_user, count=len(nearby_cards), radius_km=5.0)
        await message.answer(response)
        
        # Return to main menu
        from ..windows.main_menu import main_menu_text
        await bot.send_message(
            chat_id=message.chat.id, 
            text=main_menu_text(lang), 
            reply_markup=get_return_to_main_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in handle_location_v2: {e}")
        error_text = get_text('location_error', lang)
        await message.answer(
            error_text,
            reply_markup=get_return_to_main_menu(lang)
        )

async def category_selected_v2(message: Message, bot: Bot, lang: str):
    """Enhanced category selection with unified card rendering"""
    category_text = message.text
    
    try:
        # Extract category name (remove emoji if present)
        category_name = category_text
        if ' ' in category_text:
            parts = category_text.split(' ', 1)
            if len(parts[0]) <= 2:  # Likely emoji
                category_name = parts[1]
        
        # Find category by name
        categories = db_v2.get_categories()
        matching_category = None
        
        for category in categories:
            if category.name == category_text or category.name == category_name:
                matching_category = category
                break
        
        if not matching_category:
            # Fallback to legacy handling for backward compatibility
            await handle_legacy_category(message, bot, category_text)
            return
        
        # Get cards for this category
        cards = db_v2.get_cards_by_category(
            matching_category.slug, 
            status='published', 
            limit=10
        )
        
        if cards:
            response = f"🗂️ **{matching_category.name}**\n\n"
            response += card_service.render_cards_list(cards, lang)
            
            # Add category-specific actions
            if matching_category.slug == 'restaurants':
                response += "\n\n💡 *Покажите QR-код перед заказом, чтобы получить скидку!*"
            
        else:
            response = get_text('category_empty', lang).format(category_name=matching_category.name) + "\n\n"
            
            if settings.features.partner_fsm:
                response += get_text('category_empty_partner', lang)
        
        await message.answer(response)
        
        # Return to main menu after showing results
        from ..windows.main_menu import main_menu_text
        await bot.send_message(
            chat_id=message.chat.id,
            text=main_menu_text(lang),
            reply_markup=get_return_to_main_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in category_selected_v2: {e}")
        await handle_legacy_category(message, bot, category_text)

async def handle_legacy_category(message: Message, bot: Bot, category_text: str):
    """Fallback to legacy category handling for backward compatibility"""
    lang = 'ru'
    
    # Legacy category responses (preserved exactly)
    if category_text == '🍜 Рестораны':
        restaurants_text = get_text('legacy_restaurants', lang)
        await message.answer(restaurants_text)
    elif category_text == '🧘 SPA и массаж':
        spa_text = get_text('legacy_spa', lang)
        await message.answer(spa_text)
    elif category_text == '🛵 Аренда байков':
        transport_text = get_text('legacy_transport', lang)
        await message.answer(transport_text)
    elif category_text == '🏨 Отели':
        hotels_text = get_text('legacy_hotels', lang)
        await message.answer(hotels_text)
    elif category_text == '🗺️ Экскурсии':
        tours_text = get_text('legacy_tours', lang)
        await message.answer(tours_text)
    else:
        choose_text = get_text('legacy_choose_category', lang)
        await message.answer(choose_text)

# Profile handler (new feature)
async def handle_profile(message: Message, bot: Bot, lang: str):
    """Handle profile button press"""
    if not settings.features.partner_fsm:
        profile_text = get_text('profile_development', lang)
        await message.answer(profile_text)
        return
    
    t = get_all_texts(lang)
    
    # Get partner info
    partner = db_v2.get_partner_by_tg_id(message.from_user.id)
    
    if not partner:
        # New user
        response = f"👤 **{t['profile_main']}**\n\n"
        welcome_text = get_text('profile_welcome', lang)
        add_desc = get_text('profile_add_card_desc', lang)
        cards_desc = get_text('profile_my_cards_desc', lang)
        stats_desc = get_text('profile_stats_desc', lang)
        start_text = get_text('profile_start_add', lang)
        
        response += f"{welcome_text}\n\n"
        response += f"➕ {t['add_card']}{add_desc}\n"
        response += f"📋 {t['my_cards']}{cards_desc}\n"
        response += f"📊 {t['profile_stats']}{stats_desc}\n\n"
        response += start_text
    else:
        # Existing partner
        cards = db_v2.get_partner_cards(partner.id)
        
        response = f"👤 **{t['profile_main']}**\n\n"
        hello_text = get_text('profile_hello_partner', lang).format(name=partner.display_name or 'Партнер')
        response += f"{hello_text}\n\n"
        response += f"📊 **{t['profile_stats']}:**\n"
        response += f"   • {t['cards_count']}: {len(cards)}\n"
        
        # Count by status
        status_counts = {}
        for card in cards:
            status = card['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            by_status_text = get_text('profile_stats_by_status', lang)
            response += f"\n{by_status_text}\n"
            for status, count in status_counts.items():
                status_emoji = {
                    'draft': '📝',
                    'pending': '⏳', 
                    'published': '✅',
                    'rejected': '❌',
                    'archived': '🗂️'
                }.get(status, '📄')
                response += f"   • {status_emoji} {status}: {count}\n"
    
    from ..keyboards.reply_v2 import get_profile_keyboard
    await message.answer(response, reply_markup=get_profile_keyboard(lang))

 


@category_router.callback_query(F.data.regexp(r"^pg:(restaurants|spa|transport|hotels|tours|shops):([a-zA-Z0-9_]+):([0-9]+)$"))
async def on_catalog_pagination(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Хендлер пагинации каталога. Формат: pg:<slug>:<sub_slug>:<page>"""
    try:
        _, slug, sub_slug, page_str = callback.data.split(":")
        page = int(page_str)

        # Вызываем универсальную функцию для обновления сообщения
        await log_event("catalog_page_click", user=callback.from_user, slug=slug, sub_slug=sub_slug, page=page)
        await show_catalog_page(bot, callback.message.chat.id, lang, slug, sub_slug, page, city_id, callback.message.message_id)
        try:
            await state.update_data(category=slug, sub_slug=sub_slug, page=page)
        except Exception:
            pass
        await callback.answer()
    except Exception as e:
        logger.error(f"on_catalog_pagination error: {e}")
        await callback.answer(get_text('catalog_error', lang), show_alert=False)


@category_router.callback_query(F.data.regexp(r"^filt:restaurants:(asia|europe|street|vege|all)$"))
async def on_restaurants_filter(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Применение фильтра ресторанов и перерисовка pg:restaurants:1.
    Формат: filt:restaurants:<filter>
    """
    try:
        _, _, filt = callback.data.split(":")
        await log_event("restaurants_filter", user=callback.from_user, filter=filt, lang=lang, city_id=city_id)
        slug = 'restaurants'
        page = 1

        # Получаем карточки категории (5 шт.)
        all_cards = db_v2.get_cards_by_category(slug, status='published', limit=50)
        # Опциональная фильтрация по городу, если поле присутствует
        if city_id is not None and all_cards and 'city_id' in all_cards[0]:
            all_cards = [c for c in all_cards if (c.get('city_id') == city_id)]
        if filt != 'all':
            # Локальная фильтрация по sub_slug, если поле присутствует
            cards = [c for c in all_cards if str(c.get('sub_slug') or '').lower() == filt]
        else:
            cards = all_cards

        # Обрезаем до 5 элементов (первая страница)
        per_page = 5
        count = len(cards)
        pages = max(1, (count + per_page - 1) // per_page)
        cards_page = cards[:per_page]

        # Рендер строк элементов (каждый ряд = [ℹ️, (карта)])
        inline_rows = []
        for c in cards_page:
            listing_id = c.get('id') if isinstance(c, dict) else getattr(c, 'id', None)
            gmaps = c.get('google_maps_url') if isinstance(c, dict) else getattr(c, 'google_maps_url', None)
            inline_rows.append(get_catalog_item_row(listing_id, gmaps, lang))

        # Блок фильтров (с активным маркером) + пагинация
        filter_block = get_restaurant_filters_inline(active=filt, lang=lang)
        kb_rows = filter_block.inline_keyboard + [get_pagination_row(slug, page, pages)]
        kb = inline_rows + kb_rows

        header = f"Найдено {count}. Стр. {page}/{pages}"
        await callback.message.edit_text(
            text=header + "\n\n" + card_service.render_cards_list(cards_page, lang, max_cards=5),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        try:
            await state.update_data(category='restaurants', sub_slug=filt, page=page)
        except Exception:
            pass
        await callback.answer()
    except Exception as e:
        logger.error(f"on_restaurants_filter error: {e}")
        error_text = get_text('error_try_later', lang)
        await callback.answer(error_text, show_alert=False)


@category_router.callback_query(F.data.regexp(r"^act:view:[0-9]+$"))
async def on_card_view(callback: CallbackQuery, bot: Bot, lang: str):
    """Просмотр карточки по id. Формат: act:view:<id>"""
    try:
        _, _, id_str = callback.data.split(":")
        listing_id = int(id_str)
        await log_event("card_view", user=callback.from_user, id=listing_id)

        # Пытаемся получить карточку; если интерфейса нет — показываем заглушку.
        card = None
        try:
            card = db_v2.get_card_by_id(listing_id)
        except Exception:
            card = None

        if card:
            text = card_service.render_card(card if isinstance(card, dict) else dict(card), lang)
        else:
            text = get_text('card_soon_available', lang).format(card_id=str(listing_id))

        # Кнопки действия: карта/контакты, если есть данные
        gmaps = card.get('google_maps_url') if isinstance(card, dict) else getattr(card, 'google_maps_url', None) if card else None
        kb = [get_catalog_item_row(listing_id, gmaps, lang)]

        await callback.message.edit_text(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        await callback.answer()
    except Exception as e:
        logger.error(f"on_card_view error: {e}")
        error_text = get_text('error_try_later', lang)
        await callback.answer(error_text, show_alert=False)

def get_category_router() -> Router:
    """Get category router (always enabled)"""
    return category_router

# Export handlers for registration
__all__ = [
    'show_categories_v2',
    'show_nearest_v2',
    'show_places_page',
    'show_offers_page',
    'show_place_details',
    'show_offer_details',
    'show_category_items',
    'handle_location_v2',
    'category_selected_v2',
    'handle_profile',
    'get_category_router',
    # -- Новые обработчики для Этапа 1 --
    'on_restaurants',
    'on_spa',
    'on_hotels',
    'on_transport',
    'on_tours',
    'on_transport_submenu',
    'on_tours_submenu'
    , 'on_spa_submenu', 'on_hotels_submenu',
    'on_shops', 'on_shops_submenu'
]
