"""
Profile handler for personal cabinet functionality
"""
from aiogram.types import Message
from aiogram import Bot

from ..database.db_v2 import db_v2
from ..utils.locales_v2 import get_all_texts
from ..keyboards.reply_v2 import get_profile_keyboard
from ..settings import settings

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
    
    await message.answer(response, reply_markup=get_profile_keyboard(lang))
