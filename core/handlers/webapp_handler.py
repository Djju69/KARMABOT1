"""
Обработчик WebApp данных от Telegram
"""

import json
import logging
from aiogram import Router, F
from aiogram.types import WebAppData, Message
from aiogram.fsm.context import FSMContext

from core.handlers.profile import on_my_cards, on_my_points, on_become_partner
from core.handlers.main_menu_router import show_categories_v2
from core.keyboards.reply_v2 import get_profile_settings_keyboard
from core.services.profile_service import profile_service

logger = logging.getLogger(__name__)

webapp_router = Router()

@webapp_router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    """Обработка данных от WebApp"""
    try:
        webapp_data = message.web_app_data
        logger.info(f"🔍 WebApp data received: {webapp_data.data} from user {message.from_user.id}")
        
        data = json.loads(webapp_data.data)
        action = data.get('action')
        
        logger.info(f"🎯 WebApp action: {action} from user {message.from_user.id}")
        
        if action == 'cards' or action == 'my_cards':
            logger.info("🎯 Processing my_cards action")
            await on_my_cards(message)
        elif action == 'points' or action == 'my_points':
            logger.info("🎯 Processing my_points action")
            await on_my_points(message)
        elif action == 'catalog':
            logger.info("🎯 Processing catalog action")
            await show_categories_v2(message)
        elif action == 'partner' or action == 'become_partner':
            logger.info("🎯 Processing become_partner action")
            await on_become_partner(message, state)
        elif action == 'karma' or action == 'my_karma':
            logger.info("🎯 Processing my_karma action")
            await message.answer(
                "📊 <b>Моя карма</b>\n\n"
                "💰 <b>Текущий баланс:</b> 150 баллов\n"
                "📈 <b>Уровень:</b> 3 (Новичок)\n"
                "🎯 <b>До следующего уровня:</b> 50 баллов\n\n"
                "📊 <b>Статистика:</b>\n"
                "• Дней в системе: 15\n"
                "• Карт привязано: 3\n"
                "• Рефералов: 1",
                parse_mode="HTML"
            )
        elif action == 'achievements':
            logger.info("🎯 Processing achievements action")
            await message.answer(
                "🏆 <b>Достижения</b>\n\n"
                "✅ <b>Полученные:</b>\n"
                "• Первые шаги - Зарегистрировались\n"
                "• Коллекционер - Привязали первую карту\n"
                "• Постоянный клиент - 10 дней в системе\n\n"
                "🔒 <b>В процессе:</b>\n"
                "• Мастер карт - Привязать 5 карт (3/5)\n"
                "• Социальный - Пригласить 3 друзей (1/3)",
                parse_mode="HTML"
            )
        elif action == 'history':
            logger.info("🎯 Processing history action")
            await message.answer(
                "📋 <b>История операций</b>\n\n"
                "📅 <b>Сегодня:</b>\n"
                "• +5 баллов - Ежедневный бонус\n"
                "• +25 баллов - Привязка карты KS-1234-5678\n\n"
                "📅 <b>Вчера:</b>\n"
                "• +5 баллов - Ежедневный бонус\n"
                "• +10 баллов - Активность в боте\n\n"
                "📅 <b>Позавчера:</b>\n"
                "• +5 баллов - Ежедневный бонус",
                parse_mode="HTML"
            )
        elif action == 'notifications':
            logger.info("🎯 Processing notifications action")
            lang = await profile_service.get_lang(message.from_user.id)
            await message.answer(
                "🔔 <b>Настройки уведомлений</b>\n\n"
                "Выберите тип уведомлений:",
                parse_mode="HTML",
                reply_markup=get_profile_settings_keyboard(lang)
            )
        elif action == 'language':
            logger.info("🎯 Processing language action")
            await message.answer(
                "🌐 <b>Выбор языка</b>\n\n"
                "Выберите язык интерфейса:",
                parse_mode="HTML"
            )
        elif action == 'help':
            logger.info("🎯 Processing help action")
            await message.answer(
                "❓ <b>Помощь</b>\n\n"
                "🤖 <b>Основные функции:</b>\n"
                "• Привязка карт для получения скидок\n"
                "• Просмотр каталога партнеров\n"
                "• Накопление баллов за активность\n"
                "• Статус партнера для бизнеса\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @karmabot_support\n"
                "• Email: support@karmabot.ru\n"
                "• Телефон: +7 (999) 123-45-67",
                parse_mode="HTML"
            )
        else:
            logger.warning(f"❓ Unknown WebApp action: {action}")
            await message.answer(f"❓ Неизвестная команда: {action}")
            
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in WebApp data: {webapp_data.data}")
        await message.answer("❌ Ошибка обработки данных")
    except Exception as e:
        logger.error(f"Error handling WebApp data: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
