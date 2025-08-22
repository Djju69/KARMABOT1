"""
Enhanced category handlers with unified card rendering
Backward compatible with existing functionality
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram import Bot
import logging

from ..database.db_v2 import db_v2
from ..services.card_renderer import card_service
from ..keyboards.reply_v2 import get_return_to_main_menu, get_location_request_keyboard
from ..keyboards.inline_v2 import (
    get_categories_inline,
    get_pagination_row,
    get_catalog_item_row,
    get_restaurant_filters_inline,
)
from ..utils.locales_v2 import get_text, get_all_texts
from ..settings import settings

logger = logging.getLogger(__name__)

# Router for category handlers
category_router = Router()

async def show_categories_v2(message: Message, bot: Bot, lang: str):
    """Показывает инлайн-меню из 5 категорий (pg:<slug>:1)."""
    try:
        await message.answer(
            "🗂 Выберите категорию:",
            reply_markup=get_categories_inline(lang)
        )
    except Exception as e:
        logger.error(f"Error in show_categories_v2: {e}")
        await message.answer(
            "❌ Ошибка при загрузке категорий. Попробуйте позже.",
            reply_markup=get_return_to_main_menu(lang)
        )

async def show_nearest_v2(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Enhanced nearest places handler"""
    t = get_all_texts(lang)
    
    city_hint = f" (город #{city_id})" if city_id else ""
    await message.answer(
        "📍 **Ближайшие заведения**" + city_hint + "\n\n"
        "Пожалуйста, отправьте свою геолокацию, чтобы найти заведения рядом с вами 🗺️",
        reply_markup=get_location_request_keyboard(lang)
    )

async def handle_location_v2(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Enhanced location handler with actual nearby search"""
    
    try:
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        logger.info(f"Received location: {latitude}, {longitude}")
        
        # TODO: Implement actual geospatial search
        # For now, show all published cards as "nearby"
        nearby_cards = []
        categories = db_v2.get_categories(active_only=True)
        
        for category in categories[:3]:  # Limit to first 3 categories
            cards = db_v2.get_cards_by_category(category.slug, status='published', limit=2)
            nearby_cards.extend(cards)
        
        if nearby_cards:
            response = "📍 **Ближайшие заведения:**\n\n"
            response += card_service.render_cards_list(nearby_cards, lang, max_cards=5)
            response += "\n\n💡 *Функция точного поиска по геолокации будет доступна скоро*"
        else:
            response = "📭 **Поблизости пока нет заведений**\n\n"
            response += "Попробуйте выбрать категорию из главного меню или добавьте свое заведение!"
        
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
        await message.answer(
            "❌ Ошибка при обработке геолокации. Попробуйте позже.",
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
            response = f"📭 **{matching_category.name}**\n\n"
            response += "Заведения в этой категории появятся совсем скоро!\n\n"
            
            if settings.features.partner_fsm:
                response += "🤝 Хотите добавить свое заведение? Используйте команду /add_card"
        
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
        await message.answer(
            "Вот список ресторанов, участвующих в программе скидок: 🍽️\n\n"
            "1. Hải sản Mộc quán Nha Trang\n"
            "2. Test рест\n\n"
            "Покажите QR-код перед заказом, чтобы получить скидку!"
        )
    elif category_text == '🧘 SPA и массаж':
        await message.answer("Список салонов SPA и массажей появится совсем скоро 💆‍♀️")
    elif category_text == '🛵 Аренда байков':
        await message.answer("Сервис аренды байков будет доступен в ближайшее время 🛵")
    elif category_text == '🏨 Отели':
        await message.answer("Мы работаем над добавлением отелей 🏨")
    elif category_text == '🗺️ Экскурсии':
        await message.answer("Экскурсионные туры скоро будут доступны 🗺️")
    else:
        await message.answer("Пожалуйста, выберите категорию из списка.")

# Profile handler (new feature)
async def handle_profile(message: Message, bot: Bot, lang: str):
    """Handle profile button press"""
    if not settings.features.partner_fsm:
        await message.answer(
            "🚧 **Личный кабинет**\n\n"
            "Функция находится в разработке и будет доступна в ближайшее время.\n\n"
            "Следите за обновлениями! 🔔"
        )
        return
    
    t = get_all_texts(lang)
    
    # Get partner info
    partner = db_v2.get_partner_by_tg_id(message.from_user.id)
    
    if not partner:
        # New user
        response = f"👤 **{t['profile_main']}**\n\n"
        response += "Добро пожаловать! Вы можете:\n\n"
        response += f"➕ {t['add_card']} - добавить заведение\n"
        response += f"📋 {t['my_cards']} - просмотреть карточки\n"
        response += f"📊 {t['profile_stats']} - статистика\n\n"
        response += "Начните с добавления первой карточки командой /add_card"
    else:
        # Existing partner
        cards = db_v2.get_partner_cards(partner.id)
        
        response = f"👤 **{t['profile_main']}**\n\n"
        response += f"Привет, {partner.display_name or 'Партнер'}! 👋\n\n"
        response += f"📊 **{t['profile_stats']}:**\n"
        response += f"   • {t['cards_count']}: {len(cards)}\n"
        
        # Count by status
        status_counts = {}
        for card in cards:
            status = card['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            response += "\n📋 **По статусам:**\n"
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

 


@category_router.callback_query(F.data.regexp(r"^pg:(restaurants|spa|transport|hotels|tours):[0-9]+$"))
async def on_catalog_pagination(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None):
    """Хендлер пагинации каталога. Формат: pg:<slug>:<page>"""
    data = callback.data  # e.g., pg:restaurants:1
    try:
        _, slug, page_str = data.split(":")
        page = max(1, int(page_str))

        # Получаем карточки (пока без реального offset; 5 шт/страница по ТЗ)
        cards = db_v2.get_cards_by_category(slug, status='published', limit=50)
        # Опциональная фильтрация по городу, если поле присутствует в данных
        if city_id is not None and cards and 'city_id' in cards[0]:
            cards = [c for c in cards if (c.get('city_id') == city_id)]
        # Ограничим выдачу до 5 на страницу (как и было)
        cards = cards[:5]

        # Рендер заголовка
        count = len(cards)
        pages = max(1, page)  # Заглушка: точное кол-во страниц зависит от БД
        header = f"Найдено {count}. Стр. {page}/{pages}"

        # Сборка инлайн-кнопок под каждым элементом
        inline_rows = []
        for card in cards:
            listing_id = card.get('id') if isinstance(card, dict) else getattr(card, 'id', None)
            gmaps = card.get('google_maps_url') if isinstance(card, dict) else getattr(card, 'google_maps_url', None)
            if listing_id:
                inline_rows.append(get_catalog_item_row(listing_id, gmaps, lang))

        # Кнопки фильтров только для restaurants
        if slug == 'restaurants':
            filter_block = get_restaurant_filters_inline(lang=lang)
            # Добавим фильтры перед пагинацией
            kb_rows = filter_block.inline_keyboard + [get_pagination_row(slug, page, pages)]
        else:
            kb_rows = [get_pagination_row(slug, page, pages)]

        # Объединяем ряды: элементы + блоки управления
        kb = inline_rows + kb_rows
        await callback.message.edit_text(
            text=header + "\n\n" + card_service.render_cards_list(cards, lang, max_cards=5),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"on_catalog_pagination error: {e}")
        await callback.answer("Ошибка, попробуйте позже", show_alert=False)


@category_router.callback_query(F.data.regexp(r"^filt:restaurants:(asia|europe|street|vege|all)$"))
async def on_restaurants_filter(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None):
    """Применение фильтра ресторанов и перерисовка pg:restaurants:1.
    Формат: filt:restaurants:<filter>
    """
    try:
        _, _, filt = callback.data.split(":")
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
        await callback.answer()
    except Exception as e:
        logger.error(f"on_restaurants_filter error: {e}")
        await callback.answer("Ошибка, попробуйте позже", show_alert=False)


@category_router.callback_query(F.data.regexp(r"^act:view:[0-9]+$"))
async def on_card_view(callback: CallbackQuery, bot: Bot, lang: str):
    """Просмотр карточки по id. Формат: act:view:<id>"""
    try:
        _, _, id_str = callback.data.split(":")
        listing_id = int(id_str)

        # Пытаемся получить карточку; если интерфейса нет — показываем заглушку.
        card = None
        try:
            card = db_v2.get_card_by_id(listing_id)
        except Exception:
            card = None

        if card:
            text = card_service.render_card(card if isinstance(card, dict) else dict(card), lang)
        else:
            text = (
                "Карточка скоро будет доступна.\n"
                "ID: " + str(listing_id)
            )

        # Кнопки действия: карта/контакты, если есть данные
        gmaps = card.get('google_maps_url') if isinstance(card, dict) else getattr(card, 'google_maps_url', None) if card else None
        kb = [get_catalog_item_row(listing_id, gmaps, lang)]

        await callback.message.edit_text(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        await callback.answer()
    except Exception as e:
        logger.error(f"on_card_view error: {e}")
        await callback.answer("Ошибка, попробуйте позже", show_alert=False)

def get_category_router() -> Router:
    """Get category router (always enabled)"""
    return category_router

# Export handlers for registration
__all__ = [
    'show_categories_v2',
    'show_nearest_v2', 
    'handle_location_v2',
    'category_selected_v2',
    'handle_profile',
    'get_category_router'
]
