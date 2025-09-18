"""
Роутер для ИИ помощника админов
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional
import logging

from ..services.ai_assistant import ai_assistant
from ..utils.locales_v2 import get_text
from ..security.roles import get_user_role

logger = logging.getLogger(__name__)
router = Router(name='ai_assistant_router')


class AIAssistantStates(StatesGroup):
    """Состояния ИИ помощника"""
    waiting_for_query = State()
    analyzing_logs = State()
    analyzing_analytics = State()
    searching_data = State()


@router.message(F.text.in_(["🤖 ИИ Помощник", "🤖 AI Assistant"]))
async def ai_assistant_handler(message: Message, state: FSMContext):
    """Главное меню ИИ помощника"""
    try:
        user_id = message.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверить права доступа
        if user_role not in ['admin', 'super_admin']:
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "ИИ помощник доступен только администраторам.",
                parse_mode='HTML'
            )
            return
        
        # Проверить доступность Claude API
        if not ai_assistant.is_available():
            await message.answer(
                "❌ <b>ИИ помощник недоступен</b>\n\n"
                "Claude API не настроен. Обратитесь к системному администратору.",
                parse_mode='HTML'
            )
            return
        
        # Создать клавиатуру ИИ помощника
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Анализ логов", callback_data="ai_analyze_logs"),
                InlineKeyboardButton(text="📊 Аналитика", callback_data="ai_analyze_analytics")
            ],
            [
                InlineKeyboardButton(text="🔎 Поиск данных", callback_data="ai_search_data"),
                InlineKeyboardButton(text="💡 Рекомендации", callback_data="ai_recommendations")
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="ai_help"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="ai_back")
            ]
        ])
        
        await message.answer(
            "🤖 <b>ИИ Помощник</b>\n\n"
            "Добро пожаловать в интеллектуальный помощник для администраторов!\n\n"
            "🔍 <b>Доступные функции:</b>\n"
            "• Анализ системных логов\n"
            "• Аналитика пользователей\n"
            "• Интеллектуальный поиск\n"
            "• Рекомендации по улучшению\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in ai_assistant_handler: {e}")
        await message.answer("❌ Ошибка при запуске ИИ помощника")


@router.callback_query(F.data == "ai_analyze_logs")
async def analyze_logs_callback(callback: CallbackQuery, state: FSMContext):
    """Анализ системных логов"""
    try:
        await callback.message.edit_text(
            "🔍 <b>Анализ системных логов</b>\n\n"
            "Выберите период для анализа:",
            parse_mode='HTML'
        )
        
        # Создать клавиатуру выбора периода
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Последние 6 часов", callback_data="ai_logs_6h"),
                InlineKeyboardButton(text="📅 Последние 24 часа", callback_data="ai_logs_24h")
            ],
            [
                InlineKeyboardButton(text="📅 Последние 3 дня", callback_data="ai_logs_3d"),
                InlineKeyboardButton(text="📅 Последняя неделя", callback_data="ai_logs_7d")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="ai_back")
            ]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in analyze_logs_callback: {e}")
        await callback.answer("❌ Ошибка при анализе логов")


@router.callback_query(F.data.startswith("ai_logs_"))
async def process_logs_analysis(callback: CallbackQuery, state: FSMContext):
    """Обработка анализа логов"""
    try:
        # Определить период
        period_map = {
            "ai_logs_6h": 6,
            "ai_logs_24h": 24,
            "ai_logs_3d": 72,
            "ai_logs_7d": 168
        }
        
        period_hours = period_map.get(callback.data, 24)
        
        # Показать индикатор загрузки
        await callback.message.edit_text(
            f"🔍 <b>Анализ логов за последние {period_hours} часов</b>\n\n"
            "⏳ ИИ анализирует системные логи...\n"
            "Это может занять несколько секунд.",
            parse_mode='HTML'
        )
        
        # Выполнить анализ
        result = await ai_assistant.analyze_system_logs(period_hours)
        
        if "error" in result:
            await callback.message.edit_text(
                f"❌ <b>Ошибка анализа</b>\n\n{result['error']}",
                parse_mode='HTML'
            )
        else:
            # Создать клавиатуру для возврата
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад к ИИ помощнику", callback_data="ai_back")]
            ])
            
            await callback.message.edit_text(
                f"🔍 <b>Анализ логов завершен</b>\n\n"
                f"📅 Период: {period_hours} часов\n"
                f"🕐 Время анализа: {result.get('timestamp', 'Неизвестно')}\n\n"
                f"{result.get('analysis', 'Анализ недоступен')}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in process_logs_analysis: {e}")
        await callback.answer("❌ Ошибка при анализе логов")


@router.callback_query(F.data == "ai_analyze_analytics")
async def analyze_analytics_callback(callback: CallbackQuery, state: FSMContext):
    """Анализ аналитики пользователей"""
    try:
        await callback.message.edit_text(
            "📊 <b>Анализ аналитики пользователей</b>\n\n"
            "Выберите период для анализа:",
            parse_mode='HTML'
        )
        
        # Создать клавиатуру выбора периода
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Последние 3 дня", callback_data="ai_analytics_3d"),
                InlineKeyboardButton(text="📅 Последняя неделя", callback_data="ai_analytics_7d")
            ],
            [
                InlineKeyboardButton(text="📅 Последние 2 недели", callback_data="ai_analytics_14d"),
                InlineKeyboardButton(text="📅 Последний месяц", callback_data="ai_analytics_30d")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="ai_back")
            ]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in analyze_analytics_callback: {e}")
        await callback.answer("❌ Ошибка при анализе аналитики")


@router.callback_query(F.data.startswith("ai_analytics_"))
async def process_analytics_analysis(callback: CallbackQuery, state: FSMContext):
    """Обработка анализа аналитики"""
    try:
        # Определить период
        period_map = {
            "ai_analytics_3d": 3,
            "ai_analytics_7d": 7,
            "ai_analytics_14d": 14,
            "ai_analytics_30d": 30
        }
        
        period_days = period_map.get(callback.data, 7)
        
        # Показать индикатор загрузки
        await callback.message.edit_text(
            f"📊 <b>Анализ аналитики за последние {period_days} дней</b>\n\n"
            "⏳ ИИ анализирует данные пользователей...\n"
            "Это может занять несколько секунд.",
            parse_mode='HTML'
        )
        
        # Выполнить анализ
        result = await ai_assistant.analyze_user_analytics(period_days)
        
        if "error" in result:
            await callback.message.edit_text(
                f"❌ <b>Ошибка анализа</b>\n\n{result['error']}",
                parse_mode='HTML'
            )
        else:
            # Создать клавиатуру для возврата
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад к ИИ помощнику", callback_data="ai_back")]
            ])
            
            await callback.message.edit_text(
                f"📊 <b>Анализ аналитики завершен</b>\n\n"
                f"📅 Период: {period_days} дней\n"
                f"🕐 Время анализа: {result.get('timestamp', 'Неизвестно')}\n\n"
                f"{result.get('analysis', 'Анализ недоступен')}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in process_analytics_analysis: {e}")
        await callback.answer("❌ Ошибка при анализе аналитики")


@router.callback_query(F.data == "ai_search_data")
async def search_data_callback(callback: CallbackQuery, state: FSMContext):
    """Поиск данных в базе"""
    try:
        await callback.message.edit_text(
            "🔎 <b>Интеллектуальный поиск</b>\n\n"
            "Введите ваш запрос для поиска в базе данных.\n\n"
            "💡 <b>Примеры запросов:</b>\n"
            "• Пользователь с email test@example.com\n"
            "• Партнеры из категории Рестораны\n"
            "• Карточки созданные вчера\n"
            "• Пользователи с балансом больше 1000 баллов\n\n"
            "◀️ Для отмены нажмите /cancel",
            parse_mode='HTML'
        )
        
        await state.set_state(AIAssistantStates.waiting_for_query)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in search_data_callback: {e}")
        await callback.answer("❌ Ошибка при запуске поиска")


@router.message(AIAssistantStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    """Обработка поискового запроса"""
    try:
        query = message.text.strip()
        
        if not query:
            await message.answer("❌ Пустой запрос. Попробуйте еще раз.")
            return
        
        # Показать индикатор загрузки
        await message.answer(
            f"🔎 <b>Поиск: {query}</b>\n\n"
            "⏳ ИИ ищет данные в базе...\n"
            "Это может занять несколько секунд.",
            parse_mode='HTML'
        )
        
        # Выполнить поиск
        result = await ai_assistant.search_database(query, "admin_search")
        
        if "error" in result:
            await message.answer(
                f"❌ <b>Ошибка поиска</b>\n\n{result['error']}",
                parse_mode='HTML'
            )
        else:
            # Создать клавиатуру для возврата
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад к ИИ помощнику", callback_data="ai_back")]
            ])
            
            await message.answer(
                f"🔎 <b>Результаты поиска</b>\n\n"
                f"📝 Запрос: {query}\n"
                f"🕐 Время поиска: {result.get('timestamp', 'Неизвестно')}\n\n"
                f"{result.get('results', 'Результаты недоступны')}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_search_query: {e}")
        await message.answer("❌ Ошибка при обработке поискового запроса")


@router.callback_query(F.data == "ai_recommendations")
async def get_recommendations_callback(callback: CallbackQuery, state: FSMContext):
    """Получение рекомендаций по системе"""
    try:
        # Показать индикатор загрузки
        await callback.message.edit_text(
            "💡 <b>Анализ системы и рекомендации</b>\n\n"
            "⏳ ИИ анализирует состояние системы...\n"
            "Это может занять несколько секунд.",
            parse_mode='HTML'
        )
        
        # Получить рекомендации
        result = await ai_assistant.get_system_recommendations()
        
        if "error" in result:
            await callback.message.edit_text(
                f"❌ <b>Ошибка получения рекомендаций</b>\n\n{result['error']}",
                parse_mode='HTML'
            )
        else:
            # Создать клавиатуру для возврата
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад к ИИ помощнику", callback_data="ai_back")]
            ])
            
            await callback.message.edit_text(
                f"💡 <b>Рекомендации по системе</b>\n\n"
                f"🕐 Время анализа: {result.get('timestamp', 'Неизвестно')}\n\n"
                f"{result.get('recommendations', 'Рекомендации недоступны')}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in get_recommendations_callback: {e}")
        await callback.answer("❌ Ошибка при получении рекомендаций")


@router.callback_query(F.data == "ai_help")
async def ai_help_callback(callback: CallbackQuery, state: FSMContext):
    """Справка по ИИ помощнику"""
    try:
        help_text = """
🤖 <b>Справка по ИИ помощнику</b>

<b>🔍 Анализ логов:</b>
• Анализирует системные логи за выбранный период
• Выявляет критические ошибки и предупреждения
• Предоставляет статистику активности

<b>📊 Аналитика:</b>
• Анализирует данные пользователей
• Показывает тренды роста/снижения
• Выделяет ключевые метрики

<b>🔎 Поиск данных:</b>
• Интеллектуальный поиск по базе данных
• Понимает естественный язык
• Предоставляет релевантные результаты

<b>💡 Рекомендации:</b>
• Анализирует состояние системы
• Предлагает улучшения
• Оптимизирует производительность

<b>💡 Советы:</b>
• Используйте конкретные запросы
• Анализируйте данные регулярно
• Следуйте рекомендациям ИИ
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="ai_back")]
        ])
        
        await callback.message.edit_text(
            help_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in ai_help_callback: {e}")
        await callback.answer("❌ Ошибка при показе справки")


@router.callback_query(F.data == "ai_back")
async def ai_back_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню ИИ помощника"""
    try:
        # Создать клавиатуру ИИ помощника
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Анализ логов", callback_data="ai_analyze_logs"),
                InlineKeyboardButton(text="📊 Аналитика", callback_data="ai_analyze_analytics")
            ],
            [
                InlineKeyboardButton(text="🔎 Поиск данных", callback_data="ai_search_data"),
                InlineKeyboardButton(text="💡 Рекомендации", callback_data="ai_recommendations")
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="ai_help"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="ai_back")
            ]
        ])
        
        await callback.message.edit_text(
            "🤖 <b>ИИ Помощник</b>\n\n"
            "Добро пожаловать в интеллектуальный помощник для администраторов!\n\n"
            "🔍 <b>Доступные функции:</b>\n"
            "• Анализ системных логов\n"
            "• Аналитика пользователей\n"
            "• Интеллектуальный поиск\n"
            "• Рекомендации по улучшению\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in ai_back_callback: {e}")
        await callback.answer("❌ Ошибка при возврате")


def get_ai_assistant_router() -> Router:
    """Получить роутер ИИ помощника"""
    return router
