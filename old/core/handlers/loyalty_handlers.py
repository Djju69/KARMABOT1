"""
Обработчики команд для системы лояльности.
"""
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.services.loyalty_service import LoyaltyService, ActivityType
from core.database import get_db
from core.models.loyalty_models import LoyaltyBalance

router = Router()
logger = logging.getLogger(__name__)

# Клавиатура для меню лояльности
def get_loyalty_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для меню лояльности."""
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Баланс", callback_data="loy:balance"),
            InlineKeyboardButton(text="📜 История", callback_data="loy:history:1"),
        ],
        [
            InlineKeyboardButton(text="🎯 Активности", callback_data="actv:list"),
            InlineKeyboardButton(text="👥 Пригласить друга", callback_data="loy:referral"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Клавиатура для списка активностей
def get_activities_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру с доступными активностями."""
    activities = [
        ("✅ Ежедневный вход", "actv:claim:daily_checkin"),
        ("📝 Заполнить профиль", "actv:claim:profile"),
        ("💳 Привязать карту", "actv:claim:bindcard"),
        ("📍 Отметить посещение", "actv:claim:geocheckin"),
    ]
    
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=callback)]
        for text, callback in activities
    ]
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="loy:menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == "loy:menu")
async def show_loyalty_menu(callback: CallbackQuery):
    """Показать меню лояльности."""
    await callback.message.edit_text(
        "💎 <b>Программа лояльности</b>\n\n"
        "Зарабатывайте бонусные баллы за активность и обменивайте их на привилегии!",
        reply_markup=get_loyalty_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "loy:balance")
async def show_balance(callback: CallbackQuery):
    """Показать баланс баллов пользователя."""
    # TODO: Получить user_id из callback.from_user.id
    user_id = UUID(int=0)  # Заглушка
    
    async with get_db() as db:
        service = LoyaltyService(db)
        await service.initialize()
        balance = await service.get_balance(user_id)
    
    await callback.message.edit_text(
        f"💎 <b>Ваш баланс</b>\n\n"
        f"Доступно: <b>{balance.available_points} баллов</b>\n"
        f"Всего накоплено: <b>{balance.total_points} баллов</b>",
        reply_markup=get_loyalty_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("loy:history:"))
async def show_history(callback: CallbackQuery):
    """Показать историю операций."""
    # TODO: Реализовать пагинацию
    page = int(callback.data.split(":")[2])
    
    # Заглушка для истории
    history = [
        ("+50", "Заполнение профиля", "сегодня"),
        ("+10", "Ежедневный вход", "вчера"),
        ("-100", "Покупка купона", "неделю назад"),
    ]
    
    history_text = "\n".join(
        f"{points} - {desc} ({date})"
        for points, desc, date in history
    )
    
    await callback.message.edit_text(
        f"📜 <b>История операций</b>\n\n{history_text}",
        reply_markup=get_loyalty_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "actv:list")
async def show_activities(callback: CallbackQuery):
    """Показать список доступных активностей."""
    await callback.message.edit_text(
        "🎯 <b>Активности</b>\n\n"
        "Выполняйте задания и получайте бонусные баллы!",
        reply_markup=get_activities_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("actv:claim:"))
async def claim_activity(callback: CallbackQuery):
    """Запрос на выполнение активности."""
    activity_type = callback.data.split(":")[2]
    user_id = UUID(int=0)  # TODO: Получить из callback.from_user.id
    
    try:
        activity_enum = ActivityType(activity_type)
    except ValueError:
        await callback.answer("Неизвестный тип активности", show_alert=True)
        return
    
    async with get_db() as db:
        service = LoyaltyService(db)
        await service.initialize()
        
        # Обработка специальных случаев
        if activity_enum == ActivityType.PROFILE_COMPLETION:
            # TODO: Проверить, заполнен ли профиль
            profile_complete = False  # Заглушка
            if not profile_complete:
                await callback.answer(
                    "Заполните профиль в настройках",
                    show_alert=True
                )
                return
        
        # Записываем активность
        transaction = await service.record_activity(user_id, activity_enum)
        
        if transaction:
            await callback.answer(
                f"+{transaction.points} баллов за активность!",
                show_alert=True
            )
            # Обновляем меню
            await show_activities(callback)
        else:
            await callback.answer(
                "Не удалось засчитать активность. Попробуйте позже.",
                show_alert=True
            )
    
    await callback.answer()

@router.callback_query(F.data == "loy:referral")
async def show_referral_info(callback: CallbackQuery):
    """Показать информацию о реферальной программе."""
    user_id = UUID(int=0)  # TODO: Получить из callback.from_user.id
    
    async with get_db() as db:
        service = LoyaltyService(db)
        await service.initialize()
        
        # Генерируем реферальный код, если его еще нет
        referral_code = await service.generate_referral_code(user_id)
        
        # Получаем статистику
        stats = await service.get_referral_stats(user_id)
    
    # Формируем реферальную ссылку
    bot_username = "your_bot_username"  # TODO: Получить из конфига
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"
    
    await callback.message.edit_text(
        "👥 <b>Пригласите друзей</b>\n\n"
        f"Ваша реферальная ссылка:\n<code>{referral_link}</code>\n\n"
        f"🔹 Приглашено друзей: {stats['total_referrals']}\n"
        f"🔹 Заработано баллов: {stats['total_bonus_earned']}\n\n"
        "За каждого приглашенного друга вы получите бонусные баллы!",
        reply_markup=get_loyalty_keyboard(),
        disable_web_page_preview=True
    )
    await callback.answer()

# Обработчик команды /start с реферальным кодом
@router.message(F.text.startswith("/start ref_"))
async def handle_referral_start(message: Message):
    """Обработка входа по реферальной ссылке."""
    # TODO: Получить реферальный код из сообщения
    # TODO: Зарегистрировать реферала
    # TODO: Показать приветственное сообщение с бонусами
    
    await message.answer(
        "👋 Добро пожаловать! Вы зарегистрировались по реферальной ссылке. "
        "Получите бонусные баллы за регистрацию!"
    )
