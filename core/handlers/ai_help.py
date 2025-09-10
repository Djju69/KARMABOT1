"""
AI Help Handler - Интерактивный помощник для Karma System
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from core.utils.locales_v2 import get_text, get_all_texts
from core.database.db_v2 import db_v2
from core.keyboards.inline_v2 import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from core.keyboards.reply_v2 import get_main_menu_reply

logger = logging.getLogger(__name__)

# FSM состояния для AI чата
class AIHelpStates(StatesGroup):
    waiting_question = State()
    in_chat = State()

# Создаем роутер
ai_help_router = Router(name="ai_help")

# Ключевые слова для умных ответов (fallback)
KEYWORD_RESPONSES = {
    "скидк": {
        "keywords": ["скидк", "discount", "процент", "выгод", "экономи"],
        "response": "💰 В Karma System вы получаете скидки от 5% до 30% в ресторанах, SPA, отелях и других заведениях. Просто покажите QR-код из бота при оплате. Чем больше карма - тем выше скидка!"
    },
    "карма": {
        "keywords": ["карма", "karma", "баллы", "очки", "рейтинг"],
        "response": "⭐ Карма - это ваш рейтинг в системе. Зарабатывайте карму за активность: приглашайте друзей (+50), используйте QR-коды (+10), добавляйте заведения (+30). Высокая карма = больше привилегий!"
    },
    "регистрац": {
        "keywords": ["регистрац", "начать", "start", "присоедин", "вступ"],
        "response": "🚀 Регистрация автоматическая! Просто используйте команду /start. Затем найдите заведение в категориях, получите QR-код и покажите при оплате для скидки."
    },
    "партнер": {
        "keywords": ["партнер", "partner", "заведен", "бизнес", "сотрудничеств"],
        "response": "🤝 Хотите стать партнером? Нажмите '🤝 Стать партнером' в главном меню. Добавьте свое заведение и привлекайте новых клиентов через нашу систему скидок!"
    },
    "qr": {
        "keywords": ["qr", "код", "куар", "сканир"],
        "response": "📱 QR-код - ваш билет к скидкам! Найдите заведение в каталоге, нажмите 'Получить QR', покажите код при оплате. Один QR = одна скидка. Используйте с умом!"
    },
    "друз": {
        "keywords": ["друз", "друг", "пригласи", "реферал", "ссылк"],
        "response": "👥 Приглашайте друзей и получайте +50 кармы за каждого! Нажмите '👥 Пригласить друзей' в главном меню, скопируйте вашу уникальную ссылку и поделитесь."
    },
    "категор": {
        "keywords": ["категор", "раздел", "рестора", "spa", "отел", "магазин"],
        "response": "🗂️ У нас есть категории: Рестораны 🍽️, SPA и Красота 💆, Отели 🏨, Магазины 🛍️, Развлечения 🎭, Спорт ⚽, Авто 🚗, Другое 📦. Выберите нужную в главном меню!"
    },
    "поддержк": {
        "keywords": ["поддержк", "support", "помощ", "проблем", "ошибк", "баг"],
        "response": "📞 Нужна помощь? Опишите вашу проблему подробно, и я постараюсь помочь. Для связи с живой поддержкой используйте @karma_support"
    }
}

def create_help_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Создает клавиатуру меню помощи"""
    builder = InlineKeyboardBuilder()
    
    # Получаем тексты
    texts = get_all_texts(lang)
    
    # Кнопки меню помощи
    builder.row(
        InlineKeyboardButton(
            text=texts.get('btn.ai_assistant', '🤖 AI Помощник'),
            callback_data="help:ai_assistant"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=texts.get('btn.faq', '📋 FAQ'),
            callback_data="help:faq"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=texts.get('btn.contact_support', '📞 Поддержка'),
            callback_data="help:contact_support"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=texts.get('btn.back', '◀️ Назад'),
            callback_data="help:back"
        )
    )
    
    return builder.as_markup()

def create_ai_chat_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Создает клавиатуру для AI чата"""
    builder = InlineKeyboardBuilder()
    texts = get_all_texts(lang)
    
    builder.row(
        InlineKeyboardButton(
            text=texts.get('btn.ask_another', '❓ Еще вопрос'),
            callback_data="ai:ask_another"
        ),
        InlineKeyboardButton(
            text=texts.get('btn.end_chat', '❌ Завершить'),
            callback_data="ai:end_chat"
        )
    )
    
    return builder.as_markup()

async def get_user_lang(user_id: int) -> str:
    """Получает язык пользователя"""
    try:
        result = await db_v2.execute_query(
            "SELECT language_code FROM users WHERE telegram_id = %s",
            (user_id,)
        )
        if result and len(result) > 0:
            return result[0]['language_code'] or 'ru'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
    return 'ru'

def find_smart_response(text: str) -> Optional[str]:
    """Находит умный ответ по ключевым словам"""
    text_lower = text.lower()
    
    for category, data in KEYWORD_RESPONSES.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                return data["response"]
    
    return None

async def generate_ai_response(question: str, context: Dict = None) -> str:
    """Генерирует ответ AI (с fallback на умные ответы)"""
    # Сначала пробуем умные ответы по ключевым словам
    smart_response = find_smart_response(question)
    if smart_response:
        return smart_response
    
    # TODO: Здесь можно добавить интеграцию с OpenAI API
    # if settings.openai_api_key:
    #     return await get_openai_response(question, context)
    
    # Дефолтный ответ если ничего не найдено
    return (
        "🤔 Хм, интересный вопрос! Пока я учусь и могу ответить только на основные темы:\n"
        "• Скидки и QR-коды\n"
        "• Карма и баллы\n"
        "• Регистрация и партнерство\n"
        "• Категории заведений\n\n"
        "Попробуйте переформулировать вопрос или обратитесь в поддержку @karma_support"
    )

# Обработчик кнопки "❓ Помощь"
@ai_help_router.message(F.text == "❓ Помощь")
async def help_button_handler(message: Message, state: FSMContext):
    """Обработчик кнопки помощи"""
    try:
        await state.clear()
        user_id = message.from_user.id
        lang = await get_user_lang(user_id)
        texts = get_all_texts(lang)
        
        help_text = texts.get('help.main_menu', 
            "🆘 **Центр помощи Karma System**\n\n"
            "Выберите, чем могу помочь:\n\n"
            "🤖 **AI Помощник** - мгновенные ответы на ваши вопросы\n"
            "📋 **FAQ** - ответы на популярные вопросы\n"
            "📞 **Поддержка** - связь с нашей командой"
        )
        
        await message.answer(
            help_text,
            reply_markup=create_help_menu_keyboard(lang),
            parse_mode="HTML"
        )
        
        logger.info(f"Help menu shown to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in help handler: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

# Обработчик команды /help
@ai_help_router.message(Command("help"))
async def help_command_handler(message: Message, state: FSMContext):
    """Обработчик команды /help"""
    await help_button_handler(message, state)

# Обработчик выбора AI Помощника
@ai_help_router.callback_query(F.data == "help:ai_assistant")
async def ai_assistant_handler(callback: CallbackQuery, state: FSMContext):
    """Запускает AI помощника"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)
        texts = get_all_texts(lang)
        
        intro_text = texts.get('ai.intro_message',
            "🤖 Привет! Я AI помощник Karma System.\n\n"
            "Я могу ответить на вопросы о:\n"
            "• Скидках и QR-кодах\n"
            "• Системе кармы и баллов\n"
            "• Регистрации и партнерстве\n"
            "• Категориях заведений\n\n"
            "Задайте ваш вопрос:"
        )
        
        await callback.message.edit_text(intro_text)
        await state.set_state(AIHelpStates.waiting_question)
        
        # Сохраняем контекст
        await state.update_data(
            chat_history=[],
            start_time=datetime.now().isoformat(),
            language=lang
        )
        
        logger.info(f"AI chat started for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error starting AI chat: {e}", exc_info=True)
        await callback.answer("❌ Ошибка запуска AI помощника", show_alert=True)

# Обработчик вопросов в AI чате
@ai_help_router.message(AIHelpStates.waiting_question)
async def process_ai_question(message: Message, state: FSMContext):
    """Обрабатывает вопросы пользователя"""
    try:
        user_id = message.from_user.id
        question = message.text
        
        # Получаем данные состояния
        data = await state.get_data()
        lang = data.get('language', 'ru')
        chat_history = data.get('chat_history', [])
        
        # Генерируем ответ
        response = await generate_ai_response(question, context={"history": chat_history})
        
        # Добавляем в историю
        chat_history.append({
            "question": question,
            "answer": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Обновляем состояние
        await state.update_data(chat_history=chat_history)
        await state.set_state(AIHelpStates.in_chat)
        
        # Отправляем ответ
        await message.answer(
            response,
            reply_markup=create_ai_chat_keyboard(lang),
            parse_mode="HTML"
        )
        
        # Логируем
        logger.info(f"AI answered question from user {user_id}: {question[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing AI question: {e}", exc_info=True)
        await message.answer(
            "❌ Не удалось обработать ваш вопрос. Попробуйте еще раз.",
            reply_markup=create_ai_chat_keyboard('ru')
        )

# Обработчик "Еще вопрос"
@ai_help_router.callback_query(F.data == "ai:ask_another")
async def ask_another_handler(callback: CallbackQuery, state: FSMContext):
    """Позволяет задать еще вопрос"""
    try:
        await callback.answer()
        data = await state.get_data()
        lang = data.get('language', 'ru')
        texts = get_all_texts(lang)
        
        await callback.message.answer(
            texts.get('ai.ask_question', "❓ Задайте ваш вопрос:")
        )
        await state.set_state(AIHelpStates.waiting_question)
        
    except Exception as e:
        logger.error(f"Error in ask another: {e}", exc_info=True)

# Обработчик завершения чата
@ai_help_router.callback_query(F.data == "ai:end_chat")
async def end_chat_handler(callback: CallbackQuery, state: FSMContext):
    """Завершает AI чат"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)
        texts = get_all_texts(lang)
        
        # Логируем завершение чата
        data = await state.get_data()
        chat_history = data.get('chat_history', [])
        logger.info(f"AI chat ended for user {user_id}, questions asked: {len(chat_history)}")
        
        # Очищаем состояние
        await state.clear()
        
        # Отправляем прощальное сообщение
        await callback.message.edit_text(
            texts.get('ai.goodbye', 
                "👋 Спасибо за использование AI помощника!\n"
                "Буду рад помочь снова. Хорошего дня!"
            ),
            reply_markup=None
        )
        
        # Возвращаем главное меню
        await callback.message.answer(
            texts.get('main.menu_restored', "Главное меню восстановлено"),
            reply_markup=get_main_menu_reply(lang)
        )
        
    except Exception as e:
        logger.error(f"Error ending chat: {e}", exc_info=True)

# Обработчик FAQ
@ai_help_router.callback_query(F.data == "help:faq")
async def faq_handler(callback: CallbackQuery):
    """Показывает FAQ"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)
        
        faq_text = """
📋 <b>Часто задаваемые вопросы</b>

<b>❓ Как получить скидку?</b>
Найдите заведение в каталоге → Получите QR-код → Покажите при оплате

<b>❓ Что такое карма?</b>
Карма - ваш рейтинг. Чем выше карма, тем больше привилегий и скидок.

<b>❓ Как заработать карму?</b>
• Приглашайте друзей: +50 кармы
• Используйте QR-коды: +10 кармы
• Добавляйте заведения: +30 кармы

<b>❓ Как стать партнером?</b>
Нажмите "🤝 Стать партнером" в главном меню и следуйте инструкциям.

<b>❓ Сколько раз можно использовать QR?</b>
Каждый QR-код можно использовать один раз. После использования получите новый.

<b>❓ В каких городах работает?</b>
Система работает по всему миру. Партнеры есть в крупных городах СНГ и Азии.
"""
        
        # Кнопка назад
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="help:back_to_menu"
            )
        )
        
        await callback.message.edit_text(
            faq_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing FAQ: {e}", exc_info=True)

# Обработчик поддержки
@ai_help_router.callback_query(F.data == "help:contact_support")
async def contact_support_handler(callback: CallbackQuery):
    """Показывает контакты поддержки"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)
        
        support_text = """
📞 <b>Связь с поддержкой</b>

<b>Telegram:</b> @karma_support
<b>Email:</b> support@karmasystem.app

<b>Время работы:</b>
Пн-Пт: 9:00 - 21:00
Сб-Вс: 10:00 - 18:00

💬 Для быстрого решения опишите проблему максимально подробно и приложите скриншоты.
"""
        
        # Кнопка назад
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="💬 Написать в поддержку",
                url="https://t.me/karma_support"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="help:back_to_menu"
            )
        )
        
        await callback.message.edit_text(
            support_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing support: {e}", exc_info=True)

# Обработчик кнопки "Назад"
@ai_help_router.callback_query(F.data.in_(["help:back", "help:back_to_menu"]))
async def back_to_help_menu(callback: CallbackQuery, state: FSMContext):
    """Возвращает в меню помощи"""
    try:
        await callback.answer()
        await state.clear()
        
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)
        texts = get_all_texts(lang)
        
        help_text = texts.get('help.main_menu', 
            "🆘 **Центр помощи Karma System**\n\n"
            "Выберите, чем могу помочь:\n\n"
            "🤖 **AI Помощник** - мгновенные ответы на ваши вопросы\n"
            "📋 **FAQ** - ответы на популярные вопросы\n"
            "📞 **Поддержка** - связь с нашей командой"
        )
        
        await callback.message.edit_text(
            help_text,
            reply_markup=create_help_menu_keyboard(lang),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error going back: {e}", exc_info=True)

# Обработчик любых сообщений в состоянии in_chat
@ai_help_router.message(AIHelpStates.in_chat)
async def handle_chat_message(message: Message, state: FSMContext):
    """Обрабатывает сообщения в активном чате"""
    # Перенаправляем на обработку вопроса
    await state.set_state(AIHelpStates.waiting_question)
    await process_ai_question(message, state)

logger.info("AI Help router loaded successfully")
