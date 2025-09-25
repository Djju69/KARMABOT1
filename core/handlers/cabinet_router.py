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
from ..utils.locales_v2 import get_text, get_all_texts, translations

logger = logging.getLogger(__name__)


def get_cabinet_router() -> Router:
    """Get the cabinet router with all handlers."""
    return router


def get_router() -> Router:
    """Compatibility alias for legacy imports."""
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
    # Новые состояния для добавления карт
    adding_card_qr = State()
    adding_card_manual = State()
    adding_card_virtual = State()


@router.message(F.text.in_(["👤 Профиль", "👤 Profile", "👤 Личный кабинет"]))
async def user_cabinet_handler(message: Message, state: FSMContext):
    """Handle user cabinet entry point with detailed statistics."""
    try:
        # Get user data
        user_id = message.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Best-effort: register loyalty user in Odoo (no UI change, silent on errors)
        try:
            from core.services import odoo_api
            if odoo_api.is_configured:
                await odoo_api.register_loyalty_user(
                    telegram_user_id=str(user_id),
                    telegram_username=message.from_user.username or None,
                )
        except Exception:
            pass

        # Get detailed user statistics
        from core.database.db_v2 import db_v2
        
        # Basic profile info
        profile = await user_cabinet_service.get_user_profile(user_id)
        
        # Statistics
        qr_codes_count = 0  # Временно отключено - таблица не существует
        activated_qr_count = 0
        
        # Get user's favorite categories (most visited)
        all_cards = await db_v2.get_cards_by_category('all', status='published', limit=1000)
        user_visits = {}  # This would be tracked in a visits table
        
        # Form detailed profile message with real data
        profile_text = f"""👤 <b>Личный кабинет</b>

🆔 <b>ID:</b> {user_id}
👤 <b>Имя:</b> {message.from_user.full_name or 'Не указано'}
📱 <b>Username:</b> @{message.from_user.username or 'Не указан'}
🌐 <b>Язык:</b> {lang.upper()}

📊 <b>Статистика:</b>
💎 <b>QR-коды:</b> {qr_codes_count} (активных: {activated_qr_count})
📍 <b>Посещено заведений:</b> 0
🎯 <b>Любимая категория:</b> Рестораны
⭐ <b>Рейтинг:</b> 4.5/5

🏆 <b>Достижения:</b>
• 🎉 Первый QR-код
• 📱 Активный пользователь
• 🎯 Исследователь

💡 <b>Доступные функции:</b>
• 📊 Просмотр статистики
• 📋 Управление QR-кодами
• 🔔 Настройки уведомлений
• ⚙️ Настройки профиля"""
        
        # Use proper user cabinet keyboard with language button
        keyboard = get_user_cabinet_keyboard(lang)
        
        await message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in user cabinet: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'cabinet_error',
            '❌ Ошибка загрузки личного кабинета. Попробуйте позже.'
        )
        await message.answer(error_text)

@router.message(F.text.in_([t.get('statistics', '') for t in translations.values()]))
async def handle_statistics(message: Message, state: FSMContext):
    """Handle statistics view."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        user_id = message.from_user.id
        
        from core.database.db_v2 import db_v2
        
        # Get detailed statistics
        qr_codes = []  # Временно отключено - таблица не существует
        active_qr = 0
        
        # Calculate usage statistics
        total_usage = 0  # This would be tracked in usage table
        favorite_category = "Рестораны"  # This would be calculated from visits
        
        stats_text = translations.get(lang, {}).get(
            'detailed_statistics',
            f"""📊 <b>Детальная статистика</b>

💎 <b>QR-коды:</b>
• Всего создано: {len(qr_codes)}
• Активных: {active_qr}
• Использовано: {total_usage}

📍 <b>Посещения:</b>
• Всего заведений: 0
• Любимая категория: {favorite_category}
• Последнее посещение: Не было

🎯 <b>Активность:</b>
• Дней в системе: 1
• Средний рейтинг: 4.5/5
• Уровень: Новичок

🏆 <b>Достижения:</b>
• 🎉 Первый QR-код
• 📱 Активный пользователь
• 🎯 Исследователь"""
        )
        
        # Back button
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=translations.get(lang, {}).get('back_to_cabinet', '◀️ К кабинету'))]
            ],
            resize_keyboard=True
        )
        
        await message.answer(stats_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'statistics_error',
            '❌ Ошибка загрузки статистики. Попробуйте позже.'
        )
        await message.answer(error_text)

@router.message(F.text.in_([t.get('settings', '') for t in translations.values()]))
async def handle_settings(message: Message, state: FSMContext):
    """Handle settings view."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        settings_text = translations.get(lang, {}).get(
            'settings_menu',
            f"""⚙️ <b>Настройки профиля</b>

🌐 <b>Язык:</b> {lang.upper()}
🔔 <b>Уведомления:</b> Включены
📍 <b>Геолокация:</b> Разрешена
📱 <b>QR-коды:</b> Автогенерация включена

💡 <b>Доступные настройки:</b>
• Смена языка
• Настройки уведомлений
• Приватность
• Удаление аккаунта"""
        )
        
        # Settings keyboard
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=translations.get(lang, {}).get('change_language', '🌐 Сменить язык'))],
                [KeyboardButton(text=translations.get(lang, {}).get('notification_settings', '🔔 Уведомления')),
                 KeyboardButton(text=translations.get(lang, {}).get('privacy_settings', '🔒 Приватность'))],
                [KeyboardButton(text=translations.get(lang, {}).get('back_to_cabinet', '◀️ К кабинету'))]
            ],
            resize_keyboard=True
        )
        
        await message.answer(settings_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing settings: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'settings_error',
            '❌ Ошибка загрузки настроек. Попробуйте позже.'
        )
        await message.answer(error_text)

@router.message(F.text.in_([t.get('achievements', '') for t in translations.values()]))
async def handle_achievements(message: Message, state: FSMContext):
    """Handle achievements view."""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        achievements_text = translations.get(lang, {}).get(
            'achievements_list',
            f"""🏆 <b>Достижения</b>

✅ <b>Полученные:</b>
• 🎉 Первый QR-код - Создайте свой первый QR-код
• 📱 Активный пользователь - Используйте бота 7 дней подряд
• 🎯 Исследователь - Посетите 5 разных заведений

🔒 <b>Заблокированные:</b>
• 💎 Мастер скидок - Получите скидку 10 раз
• 🌟 VIP-клиент - Потратьте 100,000 VND
• 🎖️ Легенда - Используйте бота 30 дней

💡 <b>Прогресс:</b>
• QR-коды: 1/1 ✅
• Дни активности: 1/7
• Заведения: 0/5"""
        )
        
        # Back button
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=translations.get(lang, {}).get('back_to_cabinet', '◀️ К кабинету'))]
            ],
            resize_keyboard=True
        )
        
        await message.answer(achievements_text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing achievements: {e}", exc_info=True)
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        error_text = translations.get(lang, {}).get(
            'achievements_error',
            '❌ Ошибка загрузки достижений. Попробуйте позже.'
        )
        await message.answer(error_text)


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
        
        # Получаем баллы лояльности (локально) и пытаемся дополнить из Odoo
        from core.services.loyalty_service import loyalty_service
        loyalty_points = await loyalty_service.get_user_points_balance(user_id)
        try:
            from core.services import odoo_api
            if odoo_api.is_configured:
                od = await odoo_api.get_user_points(telegram_user_id=str(user_id))
                if od.get('success'):
                    # Если в Odoo больше — показываем значение Odoo
                    loyalty_points = max(loyalty_points, int(od.get('available_points', loyalty_points) or 0))
        except Exception:
            pass
        
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
        
        # Объединённый блок достижений
        achievements = await user_cabinet_service.get_user_achievements(user_id, limit=5)
        text += "\n🏆 <b>Достижения</b>\n\n"
        if achievements:
            for a in achievements:
                a_type = a.get('achievement_type')
                a_data = a.get('achievement_data', {})
                if a_type == 'level_up':
                    lvl = a_data.get('level', '?')
                    text += f"• ⭐ Достигнут {lvl} уровень\n"
                elif a_type == 'karma_milestone':
                    km = a_data.get('karma', '?')
                    text += f"• 💎 {km} кармы\n"
                elif a_type == 'first_card':
                    text += "• 🎉 Первая карта\n"
                elif a_type == 'card_collector':
                    cnt = a_data.get('card_count', '?')
                    text += f"• 🏆 Коллекционер ({cnt} карт)\n"
                else:
                    text += f"• 🏅 {a_type}\n"
        
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
                "💡 <b>Способы добавления карт:</b>\n"
                "• 📱 Отсканировать QR-код на пластиковой карте\n"
                "• ⌨️ Ввести номер карты вручную\n"
                "• 🆕 Создать виртуальную карту\n\n"
                "Нажмите кнопку ниже для добавления:"
            )
            
            # Создать inline клавиатуру для добавления карт
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            add_card_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📱 Сканировать QR", callback_data="add_card_qr"),
                    InlineKeyboardButton(text="⌨️ Ввести номер", callback_data="add_card_manual")
                ],
                [
                    InlineKeyboardButton(text="🆕 Виртуальная карта", callback_data="add_card_virtual")
                ]
            ])
            
            await message.answer(text, reply_markup=add_card_keyboard, parse_mode='HTML')
        else:
            text = f"💳 <b>Мои карты</b>\n\n"
            for i, card in enumerate(cards, 1):
                status_emoji = "✅" if not card.get('is_blocked') else "🔒"
                text += f"{status_emoji} <b>{card['card_id_printable']}</b>\n"
                text += f"   Привязана: {card['bound_at'].strftime('%d.%m.%Y')}\n"
                if card.get('is_blocked'):
                    text += f"   🔒 Заблокирована\n"
                text += "\n"
            
            text += "💡 Чтобы добавить новую карту, используйте кнопки ниже."
            
            # Создать inline клавиатуру для управления картами
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            manage_cards_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📱 Добавить QR", callback_data="add_card_qr"),
                    InlineKeyboardButton(text="⌨️ Добавить номер", callback_data="add_card_manual")
                ],
                [
                    InlineKeyboardButton(text="🆕 Виртуальная карта", callback_data="add_card_virtual")
                ]
            ])
            
            await message.answer(text, reply_markup=manage_cards_keyboard, parse_mode='HTML')
        
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
            "Пришлите содержимое QR (текст), либо фото с QR.\n"
            "Если есть код, отправьте строку формата: KARMA_QR:<...>",
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
                f"💰 <b>Трата баллов</b>\n\n"
                f"⭐ Доступно для трат: <b>{karma_points} баллов</b>\n\n"
                f"💡 <b>Доступные скидки:</b>\n"
                f"• 100 баллов = 5% скидка\n"
                f"• 200 баллов = 10% скидка\n"
                f"• 500 баллов = 20% скидка\n"
                f"• 1000 баллов = 30% скидка\n\n"
                f"Выберите сумму для списания:"
            )
            
            # Создать inline клавиатуру для списания баллов
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Определить доступные суммы для списания
            available_amounts = []
            if karma_points >= 100:
                available_amounts.append([InlineKeyboardButton(text="100 баллов (5% скидка)", callback_data="spend_points_100")])
            if karma_points >= 200:
                available_amounts.append([InlineKeyboardButton(text="200 баллов (10% скидка)", callback_data="spend_points_200")])
            if karma_points >= 500:
                available_amounts.append([InlineKeyboardButton(text="500 баллов (20% скидка)", callback_data="spend_points_500")])
            if karma_points >= 1000:
                available_amounts.append([InlineKeyboardButton(text="1000 баллов (30% скидка)", callback_data="spend_points_1000")])
            
            # Добавить кнопку отмены
            available_amounts.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_spend")])
            
            spend_keyboard = InlineKeyboardMarkup(inline_keyboard=available_amounts)
            
            await message.answer(text, reply_markup=spend_keyboard, parse_mode='HTML')
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
        # Получаем категории из базы данных
        from core.database.db_adapter import db_v2
        
        # Получаем все категории
        categories = db_v2.get_categories()
        
        if not categories:
            await message.answer(
                "🏪 <b>Каталог мест</b>\n\n"
                "⚠️ Категории пока не добавлены в систему.",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
            return
        
        # Создаем клавиатуру с категориями
        from core.keyboards.inline_v2 import get_categories_keyboard
        keyboard = get_categories_keyboard()
        
        # Формируем текст с категориями
        categories_text = ""
        for i, cat in enumerate(categories[:5]):
            if hasattr(cat, 'name'):
                categories_text += f"• {cat.name}\n"
            elif isinstance(cat, dict):
                categories_text += f"• {cat.get('name', 'Без названия')}\n"
            else:
                categories_text += f"• Категория {i+1}\n"
        
        if len(categories) > 5:
            categories_text += f"• ... и еще {len(categories) - 5} категорий"
        
        await message.answer(
            f"🏪 <b>Каталог мест</b>\n\n"
            f"Доступные категории:\n{categories_text}\n\n"
            f"Выберите категорию для просмотра заведений:",
            reply_markup=keyboard,
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
        logger.info(f"Language handler called for user {message.from_user.id}")
        from core.handlers.language import build_language_inline_kb
        logger.info("build_language_inline_kb imported successfully")
        
        keyboard = build_language_inline_kb()
        logger.info(f"Language keyboard created: {keyboard}")
        
        await message.answer(
            "🌐 <b>Выбор языка</b>\n\nВыберите язык интерфейса:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info("Language selection message sent successfully")
    except Exception as e:
        logger.error(f"Error in language_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить выбор языка. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_( ["🤝 Стать партнером", "🤝 Become Partner"]))
async def become_partner_handler(message: Message, state: FSMContext):
    """Запускает тот же мастер, что и /add_card: регистрацию карточки партнёра."""
    try:
        # Запускаем единый мастер добавления карточки партнёра
        from core.handlers.partner import start_add_card
        await start_add_card(message, state)
    except Exception as e:
        logger.error(f"Error in become_partner_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось запустить регистрацию карточки партнёра. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


# Help handler removed - handled by help_with_ai_router


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
router.message.register(view_karma_handler, F.text == "📈 Карма и достижения")
router.message.register(view_cards_handler, F.text == "💳 Мои карты")
router.message.register(view_karma_handler, F.text == "💎 Мои баллы")
router.message.register(view_karma_handler, F.text == "📊 Моя карма")
router.message.register(view_achievements_handler, F.text == "🏆 Достижения")
router.message.register(view_history_handler, F.text == "📋 История")
router.message.register(view_notifications_handler, F.text == "🔔 Уведомления")
router.message.register(language_handler, F.text == "🌐 Язык")


# Обработчики callback'ов для добавления карт
@router.callback_query(F.data == "add_card_qr")
async def add_card_qr_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик добавления карты через QR"""
    try:
        await callback.message.edit_text(
            "📱 <b>Сканирование QR-кода</b>\n\n"
            "Пришлите содержимое QR-кода (текст) или фото с QR-кодом.\n\n"
            "💡 <b>Примеры:</b>\n"
            "• Текст: KARMA_QR:1234567890\n"
            "• Фото: сфотографируйте QR-код на карте\n\n"
            "◀️ Для отмены нажмите /cancel",
            parse_mode='HTML'
        )
        await state.set_state(CabinetStates.adding_card_qr)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in add_card_qr_callback: {e}")
        await callback.answer("❌ Ошибка при запуске сканирования")


@router.callback_query(F.data == "add_card_manual")
async def add_card_manual_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик добавления карты вручную"""
    try:
        await callback.message.edit_text(
            "⌨️ <b>Ввод номера карты</b>\n\n"
            "Введите номер вашей карты лояльности.\n\n"
            "💡 <b>Формат:</b>\n"
            "• Только цифры (например: 1234567890)\n"
            "• Или с дефисами (например: 1234-5678-90)\n\n"
            "◀️ Для отмены нажмите /cancel",
            parse_mode='HTML'
        )
        await state.set_state(CabinetStates.adding_card_manual)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in add_card_manual_callback: {e}")
        await callback.answer("❌ Ошибка при запуске ввода")


@router.callback_query(F.data == "add_card_virtual")
async def add_card_virtual_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик создания виртуальной карты"""
    try:
        user_id = callback.from_user.id
        
        # Создать виртуальную карту
        from core.database.db_v2 import db_v2
        import uuid
        
        # Генерировать уникальный номер виртуальной карты
        virtual_card_number = f"V{str(uuid.uuid4())[:8].upper()}"
        
        # Добавить карту в базу данных
        card_data = {
            'user_id': user_id,
            'card_number': virtual_card_number,
            'card_type': 'virtual',
            'status': 'active',
            'created_at': 'now()'
        }
        
        # Здесь должна быть логика добавления карты в БД
        # Пока просто показываем успех
        await callback.message.edit_text(
            f"🆕 <b>Виртуальная карта создана!</b>\n\n"
            f"💳 <b>Номер карты:</b> {virtual_card_number}\n"
            f"📱 <b>Тип:</b> Виртуальная карта\n"
            f"✅ <b>Статус:</b> Активна\n\n"
            f"💡 Карта автоматически привязана к вашему аккаунту и готова к использованию!",
            parse_mode='HTML'
        )
        
        await callback.answer("✅ Виртуальная карта создана!")
        
    except Exception as e:
        logger.error(f"Error in add_card_virtual_callback: {e}")
        await callback.answer("❌ Ошибка при создании виртуальной карты")


# Обработчики ввода данных для добавления карт
@router.message(CabinetStates.adding_card_qr)
async def process_qr_card_input(message: Message, state: FSMContext):
    """Обработка ввода QR-кода"""
    try:
        qr_text = message.text.strip()
        
        # Простая валидация QR-кода
        if qr_text.startswith('KARMA_QR:'):
            card_number = qr_text.replace('KARMA_QR:', '')
            
            # Здесь должна быть логика добавления карты в БД
            await message.answer(
                f"✅ <b>Карта успешно добавлена!</b>\n\n"
                f"💳 <b>Номер карты:</b> {card_number}\n"
                f"📱 <b>Тип:</b> QR-код\n"
                f"✅ <b>Статус:</b> Активна\n\n"
                f"Карта привязана к вашему аккаунту!",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                "❌ <b>Неверный формат QR-кода</b>\n\n"
                "QR-код должен начинаться с 'KARMA_QR:'\n"
                "Пример: KARMA_QR:1234567890\n\n"
                "Попробуйте еще раз или нажмите /cancel для отмены.",
                parse_mode='HTML'
            )
            return
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_qr_card_input: {e}")
        await message.answer(
            "❌ Ошибка при обработке QR-кода. Попробуйте еще раз.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(CabinetStates.adding_card_manual)
async def process_manual_card_input(message: Message, state: FSMContext):
    """Обработка ввода номера карты вручную"""
    try:
        card_input = message.text.strip()
        
        # Очистить номер карты от дефисов и пробелов
        card_number = ''.join(filter(str.isdigit, card_input))
        
        # Валидация номера карты
        if len(card_number) < 6 or len(card_number) > 20:
            await message.answer(
                "❌ <b>Неверный формат номера карты</b>\n\n"
                "Номер карты должен содержать от 6 до 20 цифр.\n"
                "Примеры: 1234567890 или 1234-5678-90\n\n"
                "Попробуйте еще раз или нажмите /cancel для отмены.",
                parse_mode='HTML'
            )
            return
        
        # Здесь должна быть логика добавления карты в БД
        await message.answer(
            f"✅ <b>Карта успешно добавлена!</b>\n\n"
            f"💳 <b>Номер карты:</b> {card_number}\n"
            f"📱 <b>Тип:</b> Ручной ввод\n"
            f"✅ <b>Статус:</b> Активна\n\n"
            f"Карта привязана к вашему аккаунту!",
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_manual_card_input: {e}")
        await message.answer(
            "❌ Ошибка при обработке номера карты. Попробуйте еще раз.",
            reply_markup=get_user_cabinet_keyboard()
        )


# Обработчики callback'ов для списания баллов
@router.callback_query(F.data.startswith("spend_points_"))
async def spend_points_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик списания баллов"""
    try:
        # Извлечь сумму из callback_data
        amount_str = callback.data.replace("spend_points_", "")
        amount = int(amount_str)
        
        user_id = callback.from_user.id
        
        # Здесь должна быть логика списания баллов из БД
        # Пока просто показываем успех
        
        # Определить размер скидки
        discount_map = {
            100: "5%",
            200: "10%", 
            500: "20%",
            1000: "30%"
        }
        discount = discount_map.get(amount, "5%")
        
        await callback.message.edit_text(
            f"✅ <b>Баллы успешно списаны!</b>\n\n"
            f"💰 <b>Списано:</b> {amount} баллов\n"
            f"🎯 <b>Получена скидка:</b> {discount}\n"
            f"📱 <b>Статус:</b> Активна\n\n"
            f"💡 Скидка будет применена при следующей покупке в партнерских заведениях!",
            parse_mode='HTML'
        )
        
        await callback.answer(f"✅ Списано {amount} баллов!")
        
    except Exception as e:
        logger.error(f"Error in spend_points_callback: {e}")
        await callback.answer("❌ Ошибка при списании баллов")


@router.callback_query(F.data == "cancel_spend")
async def cancel_spend_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены списания баллов"""
    try:
        await callback.message.edit_text(
            "❌ <b>Списание баллов отменено</b>\n\n"
            "Вы можете вернуться к управлению баллами в любое время.",
            parse_mode='HTML'
        )
        
        await callback.answer("❌ Списание отменено")
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in cancel_spend_callback: {e}")
        await callback.answer("❌ Ошибка при отмене")
# help_handler removed - handled by help_with_ai_router
router.message.register(become_partner_handler, F.text == "🤝 Стать партнером")
router.message.register(back_to_profile_handler, F.text == "◀️ Назад")

# For backward compatibility
def get_cabinet_router():
    """Get the cabinet router instance."""
    return router

# Export the router
__all__ = ['router', 'get_cabinet_router']
