"""
Router for user personal cabinet functionality.
Handles all user interactions with their personal account.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Union, Any, Dict
import logging

# Create router with a name
router = Router(name='cabinet_router')

# Import dependencies
from ..services.user_cabinet_service import user_cabinet_service
from ..keyboards.reply_v2 import (
    get_user_cabinet_keyboard,
    get_partner_cabinet_keyboard,
    get_return_to_main_menu
)
from ..utils.locales_v2 import get_text, get_all_texts

logger = logging.getLogger(__name__)


def get_cabinet_router() -> Router:
    """Get the cabinet router with all handlers."""
    return router


class CabinetStates(StatesGroup):
    """FSM states for user cabinet interactions."""
    viewing_profile = State()
    viewing_balance = State()
    viewing_history = State()
    viewing_cards = State()
    viewing_notifications = State()
    viewing_achievements = State()
    spending_points = State()
    viewing_settings = State()


@router.message(F.text.in_(["👤 Профиль", "👤 Profile"]))
async def user_cabinet_handler(message: Message, state: FSMContext):
    """Handle user cabinet entry point."""
    try:
        # Get user data
        user_id = message.from_user.id
        profile = await user_cabinet_service.get_user_profile(user_id)
        
        if not profile:
            await message.answer(
                "❌ Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже.",
                reply_markup=get_return_to_main_menu()
            )
            return
        
        # Format profile message according to TZ
        text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🏷 ID: <code>{profile['telegram_id']}</code>\n"
            f"👤 Имя: {profile['full_name'] or 'Не указано'}\n"
            f"💬 Логин: @{profile['username'] or 'Не указан'}\n"
            f"⭐ Карма: <b>{profile['karma_points']}</b> (Уровень {profile['level']})\n"
            f"🏆 Репутация: +{profile.get('reputation_score', 0)}\n"
            f"📅 Регистрация: {profile['registration_date']}\n"
            f"💳 Показать карту: {profile['cards_count']}"
        )
        
        # Add level progress if available
        if profile.get('level_progress'):
            progress = profile['level_progress']
            if progress.get('next_threshold'):
                text += f"\n📈 До следующего уровня: {progress['next_threshold'] - progress['progress_karma']} кармы"
        
        # Add notifications count
        if profile.get('unread_notifications', 0) > 0:
            text += f"\n🔔 Непрочитанных уведомлений: {profile['unread_notifications']}"
        
        # Add achievements count
        if profile.get('achievements_count', 0) > 0:
            text += f"\n🏅 Достижений: {profile['achievements_count']}"
        
        # Add partner info if user is a partner
        if profile.get('is_partner'):
            text += "\n\n🔹 <b>Партнёрский статус: Активирован</b>"
        
        # Add referral info if available
        if profile.get('referral_code'):
            text += f"\n🔗 Реферальный код: <code>{profile['referral_code']}</code>"
        
        # Send message with appropriate keyboard
        keyboard = (
            get_partner_cabinet_keyboard(has_cards=profile.get('is_partner', False))
            if profile.get('is_partner') 
            else get_user_cabinet_keyboard()
        )
        
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Set state to viewing profile
        await state.set_state(CabinetStates.viewing_profile)
        
    except Exception as e:
        logger.error(f"Error in user_cabinet_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже.",
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["📊 Моя карма", "📊 My Karma", "💎 Мои баллы"]))
async def view_karma_handler(message: Message, state: FSMContext):
    """Handle karma and loyalty points viewing according to TZ."""
    try:
        user_id = message.from_user.id
        profile = await user_cabinet_service.get_user_profile(user_id)
        
        if not profile:
            await message.answer(
                "❌ Произошла ошибка при загрузке данных. Пожалуйста, попробуйте позже.",
                reply_markup=get_user_cabinet_keyboard()
            )
            return
        
        karma_points = profile.get('karma_points', 0)
        level = profile.get('level', 1)
        level_progress = profile.get('level_progress', {})
        
        # Получаем баллы лояльности
        from core.services.loyalty_service import loyalty_service
        loyalty_points = await loyalty_service.get_user_points_balance(user_id)
        
        # Получаем историю баллов
        points_history = await loyalty_service.get_points_history(user_id, limit=5)
        
        text = (
            f"💎 <b>Мои баллы и карма</b>\n\n"
            f"⭐ <b>Карма:</b> {karma_points}\n"
            f"🎯 <b>Уровень:</b> {level} из 10\n"
            f"💰 <b>Баллы лояльности:</b> {loyalty_points}\n\n"
        )
        
        # Прогресс кармы
        if level_progress.get('next_threshold'):
            text += f"📈 До следующего уровня: {level_progress['next_threshold'] - karma_points} кармы\n"
            
            # Add progress bar
            progress_percent = level_progress.get('progress_percent', 0)
            filled_bars = int(progress_percent / 10)
            empty_bars = 10 - filled_bars
            progress_bar = "█" * filled_bars + "░" * empty_bars
            text += f"Прогресс: {progress_bar} {progress_percent:.0f}%\n\n"
        else:
            text += "🎉 Максимальный уровень кармы достигнут!\n\n"
        
        # История баллов
        if points_history:
            text += "📜 <b>Последние операции с баллами:</b>\n"
            for entry in points_history[:3]:  # Показываем только последние 3
                change_text = f"+{entry['change_amount']}" if entry['change_amount'] > 0 else str(entry['change_amount'])
                text += f"• {change_text} - {entry['reason']}\n"
        else:
            text += "📜 История операций с баллами пуста\n"
        
        # Добавляем информацию о том, как использовать баллы
        text += f"\n💡 <b>Как использовать баллы:</b>\n"
        text += f"• 1 балл = 5000 VND скидки\n"
        text += f"• Используйте QR-код для оплаты\n"
        text += f"• Получайте баллы за покупки\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_balance)
        
    except Exception as e:
        logger.error(f"Error in view_karma_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о баллах и карме. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["📜 История", "📜 History"]))
async def view_history_handler(message: Message, state: FSMContext):
    """Handle transaction history viewing."""
    try:
        user_id = message.from_user.id
        history = await user_cabinet_service.get_transaction_history(user_id, limit=5)
        
        if not history.get('transactions'):
            text = "📜 У вас пока нет истории операций."
        else:
            text = "📜 <b>Последние операции</b>\n\n"
            for txn in history['transactions']:
                amount = f"+{txn['amount']}" if txn['amount'] > 0 else str(txn['amount'])
                text += (
                    f"• {txn['description']}: <b>{amount} баллов</b>\n"
                    f"  <i>{txn['created_at']} • {txn['status']}</i>\n\n"
                )
            
            if history['total'] > 5:
                text += f"\n📊 Всего операций: {history['total']}"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_history)
        
    except Exception as e:
        logger.error(f"Error in view_history_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить историю операций. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["💳 Мои карты", "💳 My Cards"]))
async def view_cards_handler(message: Message, state: FSMContext):
    """Handle cards viewing according to TZ."""
    try:
        user_id = message.from_user.id
        cards = await user_cabinet_service.get_user_cards(user_id)
        
        if not cards:
            text = (
                "💳 <b>Мои карты</b>\n\n"
                "У вас пока нет привязанных карт.\n\n"
                "💡 Чтобы привязать карту, отсканируйте QR-код на пластиковой карте или введите код карты."
            )
        else:
            text = f"💳 <b>Мои карты</b>\n\n"
            for i, card in enumerate(cards, 1):
                status_emoji = "✅" if not card.get('is_blocked') else "🔒"
                text += f"{status_emoji} <b>{card['card_id_printable']}</b>\n"
                text += f"   Привязана: {card['bound_at'].strftime('%d.%m.%Y')}\n"
                if card.get('is_blocked'):
                    text += f"   🔒 Заблокирована\n"
                text += "\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_cards)
        
    except Exception as e:
        logger.error(f"Error in view_cards_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о картах. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🔔 Уведомления", "🔔 Notifications"]))
async def view_notifications_handler(message: Message, state: FSMContext):
    """Handle notifications viewing according to TZ."""
    try:
        user_id = message.from_user.id
        notifications = await user_cabinet_service.get_user_notifications(user_id, limit=10)
        
        if not notifications:
            text = (
                "🔔 <b>Уведомления</b>\n\n"
                "У вас нет уведомлений."
            )
        else:
            text = f"🔔 <b>Уведомления</b>\n\n"
            for i, notif in enumerate(notifications, 1):
                read_status = "✅" if notif['is_read'] else "🔴"
                text += f"{read_status} {notif['message']}\n"
                text += f"   📅 {notif['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_notifications)
        
    except Exception as e:
        logger.error(f"Error in view_notifications_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить уведомления. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🏆 Достижения", "🏆 Achievements"]))
async def view_achievements_handler(message: Message, state: FSMContext):
    """Handle achievements viewing according to TZ."""
    try:
        user_id = message.from_user.id
        achievements = await user_cabinet_service.get_user_achievements(user_id, limit=10)
        
        if not achievements:
            text = (
                "🏆 <b>Достижения</b>\n\n"
                "У вас пока нет достижений.\n\n"
                "💡 Выполняйте действия в боте, чтобы получить достижения!"
            )
        else:
            text = f"🏆 <b>Достижения</b>\n\n"
            for i, achievement in enumerate(achievements, 1):
                achievement_type = achievement['achievement_type']
                achievement_data = achievement['achievement_data']
                
                if achievement_type == 'level_up':
                    level = achievement_data.get('level', '?')
                    text += f"⭐ Достигнут {level} уровень\n"
                elif achievement_type == 'karma_milestone':
                    karma = achievement_data.get('karma', '?')
                    text += f"💎 {karma} кармы\n"
                elif achievement_type == 'first_card':
                    text += f"🎉 Первая карта\n"
                elif achievement_type == 'card_collector':
                    count = achievement_data.get('card_count', '?')
                    text += f"🏆 Коллекционер ({count} карт)\n"
                else:
                    text += f"🏅 {achievement_type}\n"
                
                text += f"   📅 {achievement['earned_at'].strftime('%d.%m.%Y')}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_achievements)
        
    except Exception as e:
        logger.error(f"Error in view_achievements_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить достижения. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["📱 Сканировать QR", "📱 Scan QR"]))
async def scan_qr_handler(message: Message, state: FSMContext):
    """Handle QR scanning functionality."""
    try:
        await message.answer(
            "📱 <b>Сканирование QR-кода</b>\n\n"
            "Для сканирования QR-кода:\n"
            "1. Наведите камеру на QR-код\n"
            "2. Или отправьте фото с QR-кодом\n"
            "3. Или введите код карты вручную\n\n"
            "💡 QR-коды можно найти на пластиковых картах или в приложении партнеров.",
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        await state.set_state(CabinetStates.viewing_profile)
    except Exception as e:
        logger.error(f"Error in scan_qr_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось запустить сканирование QR. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["💰 Потратить карму", "💰 Spend Karma"]))
async def spend_karma_handler(message: Message, state: FSMContext):
    """Handle karma spending functionality."""
    try:
        user_id = message.from_user.id
        profile = await user_cabinet_service.get_user_profile(user_id)
        
        if not profile:
            await message.answer(
                "❌ Произошла ошибка при загрузке баланса. Пожалуйста, попробуйте позже.",
                reply_markup=get_user_cabinet_keyboard()
            )
            return
        
        karma_points = profile.get('karma_points', 0)
        
        if karma_points <= 0:
            text = (
                "💰 <b>Трата кармы</b>\n\n"
                "❌ У вас недостаточно кармы для трат.\n\n"
                "💡 Зарабатывайте карму:\n"
                "• Ежедневный вход: +5 кармы\n"
                "• Привязка карты: +25 кармы\n"
                "• Приглашение друзей: +50 кармы"
            )
        else:
            text = (
                f"💰 <b>Трата кармы</b>\n\n"
                f"⭐ Доступно для трат: <b>{karma_points} кармы</b>\n\n"
                f"💡 <b>Доступные скидки:</b>\n"
                f"• 100 кармы = 5% скидка\n"
                f"• 200 кармы = 10% скидка\n"
                f"• 500 кармы = 20% скидка\n"
                f"• 1000 кармы = 30% скидка\n\n"
                f"🚧 <i>Функция траты кармы будет доступна в следующих обновлениях.</i>"
            )
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        await state.set_state(CabinetStates.spending_points)
        
    except Exception as e:
        logger.error(f"Error in spend_karma_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о тратах. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["⚙️ Настройки", "⚙️ Settings"]))
async def settings_handler(message: Message, state: FSMContext):
    """Handle settings functionality."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        text = (
            "⚙️ <b>Настройки</b>\n\n"
            f"🌐 <b>Язык:</b> {lang.upper()}\n"
            f"🔔 <b>Уведомления:</b> Включены\n"
            f"🔒 <b>Приватность:</b> Стандартная\n\n"
            f"💡 <b>Доступные настройки:</b>\n"
            f"• Изменение языка\n"
            f"• Управление уведомлениями\n"
            f"• Настройки приватности\n"
            f"• Экспорт данных\n\n"
            f"🚧 <i>Расширенные настройки будут доступны в следующих обновлениях.</i>"
        )
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        await state.set_state(CabinetStates.viewing_settings)
        
    except Exception as e:
        logger.error(f"Error in settings_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить настройки. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🏪 Каталог мест", "🏪 Catalog"]))
async def view_catalog_handler(message: Message, state: FSMContext):
    """Handle catalog viewing."""
    try:
        await message.answer(
            "🏪 <b>Каталог мест</b>\n\n"
            "Здесь будет отображаться каталог всех заведений с возможностью поиска и фильтрации.",
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in view_catalog_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить каталог. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🌐 Язык", "🌐 Language"]))
async def language_handler(message: Message, state: FSMContext):
    """Handle language selection."""
    try:
        from core.handlers.language import build_language_inline_kb
        await message.answer(
            "🌐 <b>Выбор языка</b>\n\nВыберите язык интерфейса:",
            reply_markup=build_language_inline_kb(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in language_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить выбор языка. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🤝 Стать партнером", "🤝 Become Partner"]))
async def become_partner_handler(message: Message, state: FSMContext):
    """Handle become partner functionality."""
    try:
        # Проверяем, не является ли пользователь уже партнером
        from core.database.db_v2 import get_connection
        
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, status FROM partners WHERE contact_telegram = ?",
                (message.from_user.id,)
            )
            existing_partner = cursor.fetchone()
        
        if existing_partner:
            status_text = {
                'pending': '⏳ Ожидает рассмотрения',
                'approved': '✅ Одобрен',
                'rejected': '❌ Отклонен',
                'suspended': '⏸️ Приостановлен'
            }.get(existing_partner[1], '❓ Неизвестный статус')
            
            await message.answer(
                f"🤝 <b>Статус партнерства</b>\n\n"
                f"📋 Ваша заявка на партнерство уже подана.\n"
                f"📊 Статус: {status_text}\n\n"
                f"💡 Если у вас есть вопросы, обратитесь в поддержку.",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
            return
        
                    # Начинаем процесс регистрации с подтверждением через код
                    from core.fsm.partner_confirmation import start_partner_confirmation
                    await start_partner_confirmation(message, state)
        
    except Exception as e:
        logger.error(f"Error in become_partner_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о партнерстве. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["❓ Помощь", "❓ Help"]))
async def help_handler(message: Message, state: FSMContext):
    """Handle help functionality."""
    try:
        await message.answer(
            "❓ <b>Помощь</b>\n\n"
            "Добро пожаловать в KarmaBot!\n\n"
            "💡 <b>Основные функции:</b>\n"
            "• 📊 Карма - зарабатывайте баллы за активность\n"
            "• 💳 Карты - привязывайте пластиковые карты\n"
            "• 🏪 Каталог - найдите интересные места\n"
            "• 🏆 Достижения - получайте награды\n\n"
            "📞 <b>Поддержка:</b>\n"
            "Если у вас есть вопросы, обратитесь к администратору.",
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in help_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить справку. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["◀️ Назад", "◀️ Back"]))
async def back_to_profile_handler(message: Message, state: FSMContext):
    """Handle back button to return to main menu."""
    try:
        # Просто показываем главное меню без приветствия
        from core.keyboards.reply_v2 import get_main_menu_reply
        await message.answer(
            "🏠 Главное меню",
            reply_markup=get_main_menu_reply()
        )
    except Exception as e:
        logger.error(f"Error returning to main menu from cabinet: {e}", exc_info=True)
        await message.answer("Не удалось вернуться в главное меню. Попробуйте позже.")


# Register all handlers with correct button texts according to new menu
router.message.register(user_cabinet_handler, F.text == "👤 Личный кабинет")
router.message.register(view_karma_handler, F.text == "📊 Моя карма")
router.message.register(view_cards_handler, F.text == "💳 Мои карты")
router.message.register(view_karma_handler, F.text == "💎 Мои баллы")
router.message.register(view_catalog_handler, F.text == "🏪 Каталог мест")
router.message.register(view_achievements_handler, F.text == "🏆 Достижения")
router.message.register(view_history_handler, F.text == "📋 История")
router.message.register(view_notifications_handler, F.text == "🔔 Уведомления")
router.message.register(language_handler, F.text == "🌐 Язык")
router.message.register(become_partner_handler, F.text == "🤝 Стать партнером")
router.message.register(help_handler, F.text == "❓ Помощь")
router.message.register(back_to_profile_handler, F.text == "◀️ Назад")

# For backward compatibility
def get_cabinet_router():
    """Get the cabinet router instance."""
    return router

# Export the router
__all__ = ['router', 'get_cabinet_router']
