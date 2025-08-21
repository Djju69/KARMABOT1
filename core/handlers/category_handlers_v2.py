"""
Enhanced category handlers with unified card rendering
Backward compatible with existing functionality
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
import logging

from ..database.db_v2 import db_v2
from ..services.card_renderer import card_service
from ..keyboards.reply_v2 import get_return_to_main_menu, get_location_request_keyboard
from ..utils.locales_v2 import get_text, get_all_texts
from ..settings import settings

logger = logging.getLogger(__name__)

# Router for category handlers
category_router = Router()

async def show_categories_v2(message: Message, bot: Bot):
    """Enhanced categories handler with unified rendering"""
    lang = 'ru'  # TODO: Get from user settings
    t = get_all_texts(lang)
    
    try:
        categories = db_v2.get_categories(active_only=True)
        
        if not categories:
            await message.answer(
                "📭 Категории временно недоступны.",
                reply_markup=get_return_to_main_menu(lang)
            )
            return
        
        # Build categories keyboard
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        keyboard_buttons = []
        for category in categories:
            button_text = f"{category.emoji} {category.name}" if category.emoji else category.name
            keyboard_buttons.append([KeyboardButton(text=button_text)])
        
        # Add additional options
        keyboard_buttons.append([KeyboardButton(text=t['show_nearest'])])
        keyboard_buttons.append([KeyboardButton(text=t['back_to_main'])])
        
        categories_keyboard = ReplyKeyboardMarkup(
            keyboard=keyboard_buttons,
            resize_keyboard=True
        )
        
        await message.answer(
            "🗂️ **Выберите категорию:**\n\n"
            "Найдите заведения по типу услуг",
            reply_markup=categories_keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in show_categories_v2: {e}")
        await message.answer(
            "❌ Ошибка при загрузке категорий. Попробуйте позже.",
            reply_markup=get_return_to_main_menu(lang)
        )

async def show_nearest_v2(message: Message, bot: Bot):
    """Enhanced nearest places handler"""
    lang = 'ru'  # TODO: Get from user settings
    t = get_all_texts(lang)
    
    await message.answer(
        "📍 **Ближайшие заведения**\n\n"
        "Пожалуйста, отправьте свою геолокацию, чтобы найти заведения рядом с вами 🗺️",
        reply_markup=get_location_request_keyboard(lang)
    )

async def handle_location_v2(message: Message, bot: Bot):
    """Enhanced location handler with actual nearby search"""
    lang = 'ru'  # TODO: Get from user settings
    
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
            text=main_menu_text, 
            reply_markup=get_return_to_main_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in handle_location_v2: {e}")
        await message.answer(
            "❌ Ошибка при обработке геолокации. Попробуйте позже.",
            reply_markup=get_return_to_main_menu(lang)
        )

async def category_selected_v2(message: Message, bot: Bot):
    """Enhanced category selection with unified card rendering"""
    lang = 'ru'  # TODO: Get from user settings
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
            text=main_menu_text,
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
async def handle_profile(message: Message, bot: Bot):
    """Handle profile button press"""
    if not settings.features.partner_fsm:
        await message.answer(
            "🚧 **Личный кабинет**\n\n"
            "Функция находится в разработке и будет доступна в ближайшее время.\n\n"
            "Следите за обновлениями! 🔔"
        )
        return
    
    lang = 'ru'  # TODO: Get from user settings
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
