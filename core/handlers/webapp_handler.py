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
        elif action == 'partner_registration':
            # Обработка регистрации партнера
            partner_data = data.get('data', {})
            logger.info(f"[WEBAPP] Partner registration from user {user_id}: {partner_data}")
            
            # Сохраняем заявку партнера
            await save_partner_application(user_id, partner_data, message)
            
            # Уведомляем пользователя
            await message.answer(
                "✅ <b>Заявка на регистрацию партнера принята!</b>\n\n"
                f"📝 <b>Данные:</b>\n"
                f"• Название: {partner_data.get('name', 'Не указано')}\n"
                f"• Телефон: {partner_data.get('phone', 'Не указан')}\n"
                f"• Email: {partner_data.get('email', 'Не указан')}\n\n"
                "⏰ Мы свяжемся с вами в течение 24 часов для подтверждения регистрации.",
                parse_mode="HTML"
            )
            
            # Уведомляем админов
            await notify_admins_about_partner_application(user_id, partner_data, message)
            
        else:
            await message.answer(f"❌ Неизвестная команда: {action}")
            
    except Exception as e:
        logger.error(f"[WEBAPP] Error: {e}")
        await message.answer("❌ Ошибка обработки")

async def save_partner_application(user_id: int, partner_data: dict, message: Message):
    """Сохранить заявку партнера в базу данных"""
    try:
        from core.database.db_adapter import db_v2
        
        # Создаем партнера
        partner = db_v2.get_or_create_partner(
            tg_user_id=user_id,
            display_name=partner_data.get('name', message.from_user.first_name or 'Партнер')
        )
        
        logger.info(f"[WEBAPP] Partner application saved: {partner.id}")
        
    except Exception as e:
        logger.error(f"[WEBAPP] Error saving partner application: {e}")

async def notify_admins_about_partner_application(user_id: int, partner_data: dict, message: Message):
    """Уведомить админов о новой заявке партнера"""
    try:
        from core.settings import settings
        
        admin_id = settings.bot.admin_id
        if admin_id:
            from aiogram import Bot
            bot = Bot.get_current()
            
            await bot.send_message(
                admin_id,
                f"🆕 <b>Новая заявка на регистрацию партнера!</b>\n\n"
                f"👤 <b>Пользователь:</b> {message.from_user.first_name} (@{message.from_user.username or 'без username'})\n"
                f"🆔 <b>ID:</b> {user_id}\n\n"
                f"📝 <b>Данные заявки:</b>\n"
                f"• Название: {partner_data.get('name', 'Не указано')}\n"
                f"• Телефон: {partner_data.get('phone', 'Не указан')}\n"
                f"• Email: {partner_data.get('email', 'Не указан')}\n"
                f"• Время: {partner_data.get('timestamp', 'Не указано')}",
                parse_mode="HTML"
            )
            
            logger.info(f"[WEBAPP] Admin notified about partner application from user {user_id}")
            
    except Exception as e:
        logger.error(f"[WEBAPP] Error notifying admin: {e}")