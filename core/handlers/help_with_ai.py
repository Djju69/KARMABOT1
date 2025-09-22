"""
Обработчик help с кнопкой AI-ассистента
"""
import logging
from aiogram import Router, F
from typing import Dict
import time
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.ui.kb_support_ai import kb_support_ai
from core.services.user_service import get_user_role
from core.services.help_service import HelpService
from core.utils.locales_v2 import get_text

logger = logging.getLogger(__name__)
router = Router()


class AIState(StatesGroup):
    waiting_question = State()

# 60-секундное окно AI-сессии без удержания FSM
SESSION_TTL_SEC = 60
AI_SESSIONS: Dict[int, int] = {}
MENU_TEXTS = {
    "❓ Помощь",
    "🗂️ Категории",
    "◀️ Назад",
    "👤 Личный кабинет",
    "⭐ Избранные",
    "👥 Пригласить друзей",
    "⬅️ К категориям",
}

def _generate_ai_response_text(q: str) -> str:
    text = (q or "").strip().lower()
    if any(k in text for k in ["привет", "здравствуйте", "hi", "hello", "hey", "йоу", "хаи"]):
        return (
            "Привет! Я AI агент Karma System. Помогу со скидками, QR и кармой. "
            "Спросите, например: почему не работает карта лояльности; как начислить баллы; где получить QR."
        )
    if ("карта" in text or "лояльн" in text):
        if any(k in text for k in ["не работает", "сломал", "неактив", "не создается", "не создаётся", "ошиб"]):
            return (
                "Проверим карту лояльности: убедитесь, что вы вошли в меню и приняли политику. "
                "Если карта не создаётся — попробуйте ещё раз через раздел Личный кабинет или /start. "
                "Сообщите мне точный текст ошибки или пришлите скрин — подскажу дальше."
            )
        return (
            "Карта лояльности генерируется в личном кабинете. "
            "Откройте раздел и следуйте подсказкам — после создания получите номер и QR. "
            "Если появится ошибка — напишите её сюда, помогу решить."
        )
    if any(k in text for k in ["балл", "очки", "карм", "начисл", "получить балл", "начислить"]):
        return (
            "Баллы/карма начисляются за использование QR, приглашения и активности. "
            "Попросите партнёра отсканировать ваш QR при оплате — система начислит автоматически. "
            "Если баллы не пришли — уточните время и заведение, проверим начисление."
        )
    if any(k in text for k in ["скид", "qr", "куаркод", "кьюар", "код"]):
        return (
            "Скидки активируются через QR в партнёрских заведениях. "
            "Откройте нужную категорию, получите QR и покажите его сотруднику при оплате. "
            "Каждый QR разовый. Если не сработал — запросите новый и проверьте интернет."
        )
    if any(k in text for k in ["партнер", "партнёр", "бизнес", "заведен", "подключ", "владелец"]):
        return (
            "Для подключения бизнеса откройте раздел для партнёров и отправьте заявку. "
            "После модерации получите доступ к аналитике и QR-продаже. "
            "Если нужна помощь с онбордингом — напишите контакт и город, передам менеджеру."
        )
    return (
        f"Спасибо за вопрос: ‘{q}’. "
        "Я могу помочь со скидками, QR, кармой и подключением партнёров. "
        "Опишите задачу чуть конкретнее — дам точный алгоритм."
    )


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    """Обработчик команды /help с кнопкой AI"""
    try:
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        
        # Получаем текст помощи для роли (расширенный)
        help_service = HelpService()
        base_text = await help_service.get_help_message(message.from_user.id)

        # Используем только ролевой текст из HelpService (содержит корректные ссылки /static/docs)
        text = base_text

        # Кнопка AI агента
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🤖 Спросить AI агента", callback_data="ai_agent:start")]])
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении справки. Попробуйте позже.",
            reply_markup=kb_support_ai()
        )


@router.message(F.text.casefold() == "помощь")
async def txt_help(message: Message, state: FSMContext):
    """Обработчик текста 'помощь' с кнопкой AI"""
    try:
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        
        # Получаем текст помощи для роли
        help_service = HelpService()
        base_text = await help_service.get_help_message(message.from_user.id)
        text = base_text
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🤖 Спросить AI агента", callback_data="ai_agent:start")]])
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in help text: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении справки. Попробуйте позже.",
            reply_markup=kb_support_ai()
        )


@router.message(F.text == "❓ Помощь")
async def txt_help_button(message: Message, state: FSMContext):
    """Обработчик кнопки '❓ Помощь' с кнопкой AI"""
    try:
        logger.info(f"🔍 Help button pressed by user {message.from_user.id}")
        
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        logger.info(f"🔍 User role: {user_role}")
        
        # Получаем текст помощи
        help_service = HelpService()
        base_text = await help_service.get_help_message(message.from_user.id)
        text = base_text
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🤖 Спросить AI агента", callback_data="ai_agent:start")]])
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        logger.info("✅ Help message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in help button: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при получении справки. Попробуйте позже.",
            reply_markup=kb_support_ai()
        )


# AI agent callbacks
@router.callback_query(F.data.startswith("ai_agent:"))
async def ai_agent_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    action = callback.data.split(":", 1)[1]
    if action == "start":
        ai_text = (
            "🤖 <b>AI Агент Karma System</b>\n\n"
            "Я помогу с:\n"
            "• 🎯 Поиском скидок\n"
            "• 📍 Рекомендациями заведений\n"
            "• 💰 Советами по карме\n"
            "• 🏪 Вопросами о партнёрстве\n\n"
            "Напишите вопрос или выберите действие."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Задать вопрос", callback_data="ai_agent:ask")],
            [InlineKeyboardButton(text="🏪 Найти заведения", callback_data="ai_agent:find_places")],
            [InlineKeyboardButton(text="💰 Советы по karma", callback_data="ai_agent:karma_tips")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="help:back_to_menu")],
        ])
        await callback.message.edit_text(ai_text, reply_markup=kb, parse_mode="HTML")
    elif action == "ask":
        await state.set_state(AIState.waiting_question)
        # Стартуем 60-секундное окно AI-сессии
        AI_SESSIONS[user_id] = int(time.time()) + SESSION_TTL_SEC
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к AI", callback_data="ai_agent:start")]])
        await callback.message.edit_text("💬 Напишите ваш вопрос в чат, и я отвечу!", reply_markup=kb)
    elif action == "find_places":
        places_text = (
            "🏪 <b>Поиск заведений</b>\n\n"
            "Выберите категорию:\n"
            "• 🍽️ Рестораны\n• 🧖‍♀️ SPA\n• 🏍️ Байки\n• 🏨 Отели\n• 🚶‍♂️ Экскурсии\n• 🛍️ Магазины"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к AI", callback_data="ai_agent:start")]])
        await callback.message.edit_text(places_text, reply_markup=kb, parse_mode="HTML")
    elif action == "karma_tips":
        tips = (
            "💰 <b>Советы по накоплению Karma</b>\n\n"
            "• Ежедневный вход: +5\n• Привязка карты: +25\n• Приглашение друга: +50\n• QR-коды: +1–10\n"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад к AI", callback_data="ai_agent:start")]])
        await callback.message.edit_text(tips, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.message(AIState.waiting_question)
async def process_ai_question(message: Message, state: FSMContext):
    q = (message.text or "").strip()

    # Если пользователь ввёл команду или нажал явные кнопки меню — завершаем AI-режим и не отвечаем
    if q.startswith('/') or q in {"❓ Помощь", "🗂️ Категории", "◀️ Назад", "👤 Профиль"}:
        await state.clear()
        return

    # Простые умные ответы (русский), 3-4 предложения максимум
    text = q.lower()
    response = None

    # Приветствия
    if any(k in text for k in ["привет", "здравствуйте", "hi", "hello", "hey", "йоу", "хаи"]):
        response = (
            "Привет! Я AI агент Karma System. Помогу со скидками, QR и кармой. "
            "Спросите, например: почему не работает карта лояльности; как начислить баллы; где получить QR."
        )

    # Проблемы с картой лояльности
    if response is None and ("карта" in text or "лояльн" in text):
        if any(k in text for k in ["не работает", "сломал", "неактив", "не создается", "не создаётся", "ошиб"]):
            response = (
                "Проверим карту лояльности: убедитесь, что вы вошли в меню и приняли политику. "
                "Если карта не создаётся — попробуйте ещё раз через раздел Личный кабинет или /start. "
                "Сообщите мне точный текст ошибки или пришлите скрин — подскажу дальше."
            )
        else:
            response = (
                "Карта лояльности генерируется в личном кабинете. "
                "Откройте раздел и следуйте подсказкам — после создания получите номер и QR. "
                "Если появится ошибка — напишите её сюда, помогу решить."
            )

    # Начисление баллов/кармы
    if response is None and any(k in text for k in ["балл", "очки", "карм", "начисл", "получить балл", "начислить"]):
        response = (
            "Баллы/карма начисляются за использование QR, приглашения и активности. "
            "Попросите партнёра отсканировать ваш QR при оплате — система начислит автоматически. "
            "Если баллы не пришли — уточните время и заведение, проверим начисление."
        )

    # Скидки и QR
    if response is None and any(k in text for k in ["скид", "qr", "куаркод", "кьюар", "код"]):
        response = (
            "Скидки активируются через QR в партнёрских заведениях. "
            "Откройте нужную категорию, получите QR и покажите его сотруднику при оплате. "
            "Каждый QR разовый. Если не сработал — запросите новый и проверьте интернет."
        )

    # Партнёрская программа
    if response is None and any(k in text for k in ["партнер", "партнёр", "бизнес", "заведен", "подключ", "владелец"]):
        response = (
            "Для подключения бизнеса откройте раздел для партнёров и отправьте заявку. "
            "После модерации получите доступ к аналитике и QR-продаже. "
            "Если нужна помощь с онбордингом — напишите контакт и город, передам менеджеру."
        )

    # По умолчанию
    if response is None:
        response = (
            f"Спасибо за вопрос: ‘{q}’. "
            "Я могу помочь со скидками, QR, кармой и подключением партнёров. "
            "Опишите задачу чуть конкретнее — дам точный алгоритм."
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Задать еще вопрос", callback_data="ai_agent:ask")],
            [InlineKeyboardButton(text="◀️ Назад к AI", callback_data="ai_agent:start")],
        ]
    )
    await message.answer(f"🤖 <b>AI Агент отвечает:</b>\n\n{response}", reply_markup=kb, parse_mode="HTML")
    # Продлеваем окно и очищаем состояние — меню остаётся полностью рабочим
    AI_SESSIONS[message.from_user.id] = int(time.time()) + SESSION_TTL_SEC
    await state.clear()


# Follow-up: любые обычные тексты (не команды и не кнопки меню) в окне AI-сессии
@router.message(
F.text,
lambda message: (
    AI_SESSIONS.get(message.from_user.id, 0) > int(time.time())
    and not ((message.text or "").startswith("/") or (message.text or "") in MENU_TEXTS)
),
)
async def ai_followup_session(message: Message, state: FSMContext):
    try:
        text = (message.text or "")
        # Отдаём управление обычным хендлерам для команд и главных кнопок меню
        if text.startswith('/') or text in MENU_TEXTS:
            return
        exp = AI_SESSIONS.get(message.from_user.id, 0)
        if int(time.time()) > int(exp or 0):
            return  # окно не активно — пусть обрабатывают другие хендлеры
        response = _generate_ai_response_text(text)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Задать еще вопрос", callback_data="ai_agent:ask")],
                [InlineKeyboardButton(text="◀️ Назад к AI", callback_data="ai_agent:start")],
            ]
        )
        await message.answer(f"🤖 <b>AI Агент отвечает:</b>\n\n{response}", reply_markup=kb, parse_mode="HTML")
        # Продлеваем окно ещё на TTL
        AI_SESSIONS[message.from_user.id] = int(time.time()) + SESSION_TTL_SEC
    except Exception as e:
        logger.error(f"AI follow-up error: {e}", exc_info=True)
