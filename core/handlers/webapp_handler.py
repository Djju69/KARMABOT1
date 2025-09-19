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
            
        elif action == 'moderation':
            # Показать заявки на модерацию
            await show_moderation_queue(message)
            
        else:
            await message.answer(f"❌ Неизвестная команда: {action}")
            
    except Exception as e:
        logger.error(f"[WEBAPP] Error: {e}")
        await message.answer("❌ Ошибка обработки")

async def save_partner_application(user_id: int, partner_data: dict, message: Message):
    """Сохранить заявку партнера в базу данных"""
    try:
        from core.database.db_adapter import db_v2
        
        # Создаем партнера со статусом 'pending'
        partner = db_v2.get_or_create_partner(
            tg_user_id=user_id,
            display_name=partner_data.get('name', message.from_user.first_name or 'Партнер')
        )
        
        # Обновляем статус на 'pending' если партнер уже существовал
        if hasattr(partner, 'status'):
            partner.status = 'pending'
            # TODO: Добавить метод update_partner_status в db_adapter
        
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

async def show_moderation_queue(message: Message):
    """Показать заявки на модерацию"""
    try:
        from core.database.db_adapter import db_v2
        
        # Получаем всех партнеров со статусом 'pending'
        partners = db_v2.get_partners_by_status('pending')
        
        if not partners:
            await message.answer(
                "📋 <b>Модерация</b>\n\n"
                "✅ Нет заявок на модерацию\n"
                "Все заявки обработаны!",
                parse_mode="HTML"
            )
            return
        
        # Формируем список заявок
        applications_text = "📋 <b>Заявки на модерацию</b>\n\n"
        
        for i, partner in enumerate(partners[:10], 1):  # Показываем первые 10
            applications_text += (
                f"<b>{i}. Партнер #{partner.id}</b>\n"
                f"👤 Пользователь: {partner.display_name}\n"
                f"🆔 ID: {partner.tg_user_id}\n"
                f"📞 Телефон: {partner.phone or 'Не указан'}\n"
                f"📧 Email: {partner.email or 'Не указан'}\n"
                f"📅 Создан: {partner.created_at.strftime('%d.%m.%Y %H:%M') if partner.created_at else 'Неизвестно'}\n\n"
            )
        
        if len(partners) > 10:
            applications_text += f"... и еще {len(partners) - 10} заявок\n\n"
        
        applications_text += (
            "🔧 <b>Действия:</b>\n"
            "• /approve_partner [ID] - одобрить партнера\n"
            "• /reject_partner [ID] - отклонить заявку\n"
            "• /partner_info [ID] - подробная информация"
        )
        
        await message.answer(applications_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"[WEBAPP] Error showing moderation queue: {e}")
        await message.answer("❌ Ошибка загрузки заявок на модерацию")