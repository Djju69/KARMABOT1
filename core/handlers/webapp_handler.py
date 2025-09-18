import json
import logging
from aiogram import Router, F
from aiogram.types import WebAppData, Message

logger = logging.getLogger(__name__)
webapp_router = Router(name="webapp_handler")

@webapp_router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        user_id = message.from_user.id
        
        logger.info(f"[WEBAPP] Action '{action}' from user {user_id}")
        
        if action == 'request_card':
            await message.answer("🎯 Заявка на карту принята! Мы свяжемся с вами в течение 24 часов")
        elif action == 'show_karma_history':
            await message.answer("📊 История кармы:\n➕50 - Регистрация\n➕25 - Активность")
        elif action == 'update_profile':
            await message.answer("✏️ Редактирование профиля временно недоступно")
        elif action == 'show_referral_program':
            await message.answer("🤝 Приглашайте друзей и получайте бонусы!")
        else:
            await message.answer(f"❌ Неизвестная команда: {action}")
            
    except Exception as e:
        logger.error(f"[WEBAPP] Error: {e}")
        await message.answer("❌ Ошибка обработки")