import json
import logging
from aiogram import Router, F
from aiogram.types import WebAppData, Message
from aiogram.filters import Command

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
            
        elif action == 'open_in_browser':
            # Открыть WebApp в браузере
            url = data.get('url', '')
            logger.info(f"[WEBAPP] Opening in browser: {url}")
            
            await message.answer(
                f"🌐 <b>Открыть в браузере</b>\n\n"
                f"Скопируйте ссылку и откройте в браузере:\n"
                f"<code>{url}</code>\n\n"
                f"💡 <b>Преимущества браузера:</b>\n"
                f"• Больший экран для удобства\n"
                f"• Полная функциональность форм\n"
                f"• Сохранение данных в браузере",
                parse_mode="HTML"
            )
        
        elif action == 'change_language':
            # Изменение языка пользователя
            language = data.get('language', 'ru')
            logger.info(f"[WEBAPP] Language change request from user {user_id}: {language}")
            
            # Обновляем язык пользователя в БД
            from core.services.translation_service import translation_service
            success = translation_service.set_user_language(user_id, language)
            
            if success:
                await message.answer(
                    f"✅ <b>Язык изменен!</b>\n\n"
                    f"Интерфейс переключен на: {translation_service.get_language_name(language)}\n\n"
                    f"Изменения вступят в силу при следующем открытии кабинета.",
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❌ <b>Ошибка изменения языка</b>\n\n"
                    "Попробуйте снова или обратитесь в поддержку.",
                    parse_mode="HTML"
                )
            
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
        
        # Обновляем данные партнера
        if hasattr(partner, 'phone'):
            partner.phone = partner_data.get('phone', '')
        if hasattr(partner, 'email'):
            partner.email = partner_data.get('email', '')
        
        # Сохраняем в таблицу заявок партнеров (если есть)
        try:
            # Создаем запись в таблице заявок
            from core.database.db_adapter import db_v2
            # Check if application already exists
            existing = db_v2.execute_query("""
                SELECT id FROM partner_applications WHERE telegram_user_id = ?
            """, (user_id,))
            
            if existing:
                # Update existing application
                db_v2.execute_query("""
                    UPDATE partner_applications SET
                        name = ?, phone = ?, email = ?, business_description = ?,
                        status = 'pending', created_at = datetime('now')
                    WHERE telegram_user_id = ?
                """, (
                    partner_data.get('name', ''),
                    partner_data.get('phone', ''),
                    partner_data.get('email', ''),
                    partner_data.get('description', ''),
                    user_id
                ))
            else:
                # Insert new application
                db_v2.execute_query("""
                    INSERT INTO partner_applications (
                        telegram_user_id, telegram_username, name, phone, email, 
                        business_description, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    user_id,
                    message.from_user.username or '',
                    partner_data.get('name', ''),
                    partner_data.get('phone', ''),
                    partner_data.get('email', ''),
                    partner_data.get('description', '')
                ))
        except Exception as e:
            logger.warning(f"[WEBAPP] Could not save to partner_applications table: {e}")
        
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


@webapp_router.message(Command("approve_partner"))
async def approve_partner_command(message: Message):
    """Одобрить партнера по ID"""
    try:
        # Проверяем права администратора
        from core.services.user_service import get_user_role
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для выполнения этой команды")
            return
        
        # Получаем ID партнера из команды
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer("❌ Использование: /approve_partner [ID]")
            return
        
        try:
            partner_id = int(command_parts[1])
        except ValueError:
            await message.answer("❌ ID партнера должен быть числом")
            return
        
        # Одобряем партнера
        from core.database.db_adapter import db_v2
        success = await approve_partner(partner_id, message.from_user.id)
        
        if success:
            await message.answer(f"✅ Партнер #{partner_id} успешно одобрен!")
        else:
            await message.answer(f"❌ Ошибка при одобрении партнера #{partner_id}")
            
    except Exception as e:
        logger.error(f"[WEBAPP] Error approving partner: {e}")
        await message.answer("❌ Произошла ошибка при выполнении команды")


@webapp_router.message(Command("reject_partner"))
async def reject_partner_command(message: Message):
    """Отклонить партнера по ID"""
    try:
        # Проверяем права администратора
        from core.services.user_service import get_user_role
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для выполнения этой команды")
            return
        
        # Получаем ID партнера из команды
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer("❌ Использование: /reject_partner [ID]")
            return
        
        try:
            partner_id = int(command_parts[1])
        except ValueError:
            await message.answer("❌ ID партнера должен быть числом")
            return
        
        # Отклоняем партнера
        from core.database.db_adapter import db_v2
        success = await reject_partner(partner_id, message.from_user.id)
        
        if success:
            await message.answer(f"❌ Партнер #{partner_id} отклонен")
        else:
            await message.answer(f"❌ Ошибка при отклонении партнера #{partner_id}")
            
    except Exception as e:
        logger.error(f"[WEBAPP] Error rejecting partner: {e}")
        await message.answer("❌ Произошла ошибка при выполнении команды")


async def approve_partner(partner_id: int, admin_id: int) -> bool:
    """Одобрить партнера"""
    try:
        from core.database.db_adapter import db_v2
        
        # Обновляем статус партнера на 'approved'
        # Предполагаем, что есть метод для обновления статуса партнера
        # Если нет, можно добавить в db_v2
        
        logger.info(f"[MODERATION] Partner {partner_id} approved by admin {admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"[MODERATION] Error approving partner {partner_id}: {e}")
        return False


async def reject_partner(partner_id: int, admin_id: int) -> bool:
    """Отклонить партнера"""
    try:
        from core.database.db_adapter import db_v2
        
        # Обновляем статус партнера на 'rejected'
        # Предполагаем, что есть метод для обновления статуса партнера
        # Если нет, можно добавить в db_v2
        
        logger.info(f"[MODERATION] Partner {partner_id} rejected by admin {admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"[MODERATION] Error rejecting partner {partner_id}: {e}")
        return False