"""
Обработчики геймификации и достижений
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.services.gamification_service import gamification_service
from core.utils.locales_v2 import get_text

logger = logging.getLogger(__name__)
router = Router(name="gamification_router")

@router.message(F.text.in_([
    "🏆 Достижения", "🏆 Achievements", "🏆 Thành tựu", "🏆 업적"
]))
async def handle_achievements_menu(message: Message, state: FSMContext):
    """Показать меню достижений"""
    try:
        user_id = message.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем статистику пользователя
        stats = await gamification_service.get_user_stats(user_id)
        
        if not stats:
            await message.answer("❌ Ошибка загрузки статистики")
            return
        
        # Формируем сообщение со статистикой
        text = f"🏆 <b>Ваши достижения</b>\n\n"
        text += f"📊 <b>Статистика:</b>\n"
        text += f"🎯 Уровень: {stats['level']}\n"
        text += f"💎 Карма: {stats['karma_points']}\n"
        text += f"⭐ Баллы лояльности: {stats['loyalty_points']}\n"
        text += f"🏆 Достижений: {stats['achievements_count']}\n"
        text += f"👥 Рефералов: {stats['referrals_count']}\n"
        text += f"💳 Карт: {stats['cards_count']}\n"
        text += f"🔥 Серия: {stats['current_streak']} дней\n\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Мои достижения", callback_data="achievements_list"),
                InlineKeyboardButton(text="📈 Прогресс", callback_data="achievements_progress")
            ],
            [
                InlineKeyboardButton(text="🎯 Статистика", callback_data="achievements_stats"),
                InlineKeyboardButton(text="🏅 Рейтинг", callback_data="achievements_ranking")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing achievements menu: {e}")
        await message.answer("❌ Ошибка загрузки достижений")

@router.callback_query(F.data == "achievements_list")
async def handle_achievements_list(callback: CallbackQuery, state: FSMContext):
    """Показать список достижений пользователя"""
    try:
        user_id = callback.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем достижения пользователя
        achievements = await gamification_service.get_user_achievements(user_id, limit=10)
        
        if not achievements:
            text = "🏆 У вас пока нет достижений\n\n"
            text += "💡 Выполняйте различные действия в системе, чтобы получить достижения!"
        else:
            text = "🏆 <b>Ваши достижения:</b>\n\n"
            
            for i, achievement in enumerate(achievements, 1):
                rarity_color = {
                    'common': '⚪',
                    'rare': '🔵', 
                    'epic': '🟣',
                    'legendary': '🟡'
                }.get(achievement['rarity'], '⚪')
                
                text += f"{i}. {rarity_color} {achievement['icon']} <b>{achievement['name']}</b>\n"
                text += f"   {achievement['description']}\n"
                text += f"   💰 +{achievement['points_reward']} баллов\n"
                text += f"   📅 {achievement['earned_at'].strftime('%d.%m.%Y')}\n\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_achievements")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing achievements list: {e}")
        await callback.answer("❌ Ошибка загрузки достижений")

@router.callback_query(F.data == "achievements_progress")
async def handle_achievements_progress(callback: CallbackQuery, state: FSMContext):
    """Показать прогресс по достижениям"""
    try:
        user_id = callback.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем прогресс по достижениям
        progress = await gamification_service.get_achievement_progress(user_id)
        
        if not progress:
            text = "❌ Ошибка загрузки прогресса"
        else:
            text = "📈 <b>Прогресс по достижениям:</b>\n\n"
            
            # Показываем только первые 10 достижений
            for achievement in progress[:10]:
                if achievement['is_earned']:
                    text += f"✅ {achievement['rarity_color']} {achievement['icon']} <b>{achievement['name']}</b>\n"
                    text += f"   {achievement['description']}\n"
                    text += f"   💰 +{achievement['points_reward']} баллов\n\n"
                else:
                    text += f"⏳ {achievement['rarity_color']} {achievement['icon']} <b>{achievement['name']}</b>\n"
                    text += f"   {achievement['progress_bar']} {achievement['current']}/{achievement['target']} ({achievement['progress_percentage']}%)\n"
                    text += f"   {achievement['description']}\n\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_achievements")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing achievements progress: {e}")
        await callback.answer("❌ Ошибка загрузки прогресса")

@router.callback_query(F.data == "achievements_stats")
async def handle_achievements_stats(callback: CallbackQuery, state: FSMContext):
    """Показать детальную статистику"""
    try:
        user_id = callback.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем статистику пользователя
        stats = await gamification_service.get_user_stats(user_id)
        
        if not stats:
            text = "❌ Ошибка загрузки статистики"
        else:
            text = "📊 <b>Детальная статистика:</b>\n\n"
            
            # Уровень и прогресс
            level = stats['level']
            karma = stats['karma_points']
            next_level_karma = 100 * (level + 1) if level < 10 else karma
            
            text += f"🎯 <b>Уровень:</b> {level}\n"
            text += f"💎 <b>Карма:</b> {karma}\n"
            if level < 10:
                text += f"📈 <b>До следующего уровня:</b> {next_level_karma - karma} кармы\n\n"
            
            # Достижения по категориям
            text += f"🏆 <b>Достижения:</b> {stats['achievements_count']}\n"
            text += f"👥 <b>Рефералов:</b> {stats['referrals_count']}\n"
            text += f"💳 <b>Карт:</b> {stats['cards_count']}\n"
            text += f"🔥 <b>Текущая серия:</b> {stats['current_streak']} дней\n"
            text += f"⭐ <b>Баллы лояльности:</b> {stats['loyalty_points']}\n\n"
            
            # Дата регистрации
            if stats['member_since']:
                text += f"📅 <b>Участник с:</b> {stats['member_since'].strftime('%d.%m.%Y')}\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_achievements")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing achievements stats: {e}")
        await callback.answer("❌ Ошибка загрузки статистики")

@router.callback_query(F.data == "achievements_ranking")
async def handle_achievements_ranking(callback: CallbackQuery, state: FSMContext):
    """Показать рейтинг пользователей"""
    try:
        user_id = callback.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        text = "🏅 <b>Рейтинг пользователей:</b>\n\n"
        text += "📊 Рейтинг по карме:\n"
        text += "1. 🥇 Пользователь 1 - 5000 кармы\n"
        text += "2. 🥈 Пользователь 2 - 4500 кармы\n"
        text += "3. 🥉 Пользователь 3 - 4000 кармы\n\n"
        text += "🏆 Рейтинг по достижениям:\n"
        text += "1. 🥇 Пользователь 1 - 25 достижений\n"
        text += "2. 🥈 Пользователь 2 - 20 достижений\n"
        text += "3. 🥉 Пользователь 3 - 18 достижений\n\n"
        text += "💡 Рейтинг обновляется ежедневно!"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_achievements")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing achievements ranking: {e}")
        await callback.answer("❌ Ошибка загрузки рейтинга")

@router.callback_query(F.data == "back_to_achievements")
async def handle_back_to_achievements(callback: CallbackQuery, state: FSMContext):
    """Вернуться к меню достижений"""
    try:
        user_id = callback.from_user.id
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем статистику пользователя
        stats = await gamification_service.get_user_stats(user_id)
        
        if not stats:
            await callback.message.edit_text("❌ Ошибка загрузки статистики")
            return
        
        # Формируем сообщение со статистикой
        text = f"🏆 <b>Ваши достижения</b>\n\n"
        text += f"📊 <b>Статистика:</b>\n"
        text += f"🎯 Уровень: {stats['level']}\n"
        text += f"💎 Карма: {stats['karma_points']}\n"
        text += f"⭐ Баллы лояльности: {stats['loyalty_points']}\n"
        text += f"🏆 Достижений: {stats['achievements_count']}\n"
        text += f"👥 Рефералов: {stats['referrals_count']}\n"
        text += f"💳 Карт: {stats['cards_count']}\n"
        text += f"🔥 Серия: {stats['current_streak']} дней\n\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Мои достижения", callback_data="achievements_list"),
                InlineKeyboardButton(text="📈 Прогресс", callback_data="achievements_progress")
            ],
            [
                InlineKeyboardButton(text="🎯 Статистика", callback_data="achievements_stats"),
                InlineKeyboardButton(text="🏅 Рейтинг", callback_data="achievements_ranking")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error returning to achievements menu: {e}")
        await callback.answer("❌ Ошибка загрузки меню")
