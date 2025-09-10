"""
Обработчик help с кнопкой AI-ассистента
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.ui.kb_support_ai import kb_support_ai
from core.services.user_service import get_user_role
from core.services.help_service import HelpService

logger = logging.getLogger(__name__)
router = Router()


class AIState(StatesGroup):
    waiting_question = State()


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    """Обработчик команды /help с кнопкой AI"""
    try:
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        
        # Получаем текст помощи для роли (расширенный)
        help_service = HelpService()
        base_text = await help_service.get_help_message(message.from_user.id)

        # Ролевые блоки
        extra = []
        if user_role in ["admin", "super_admin"]:
            extra.append(
                "\n\n🛡️ <b>Администраторы</b>\n"
                "• 📊 Админская панель — https://docs.karma-system.com/admin/dashboard\n"
                "• ✅ Модерация заявок — https://docs.karma-system.com/admin/moderation\n"
                "• 👥 Управление пользователями — https://docs.karma-system.com/admin/users\n"
                "• ⚙️ Системные настройки — https://docs.karma-system.com/admin/settings"
            )
        if user_role == "super_admin":
            extra.append(
                "\n\n👑 <b>Супер-администраторы</b>\n"
                "• 🖥️ Супер-админ панель — https://docs.karma-system.com/superadmin/dashboard\n"
                "• 🛡️ Управление администраторами — https://docs.karma-system.com/superadmin/admins\n"
                "• 📊 Системная аналитика — https://docs.karma-system.com/superadmin/analytics"
            )

        help_tail = (
            "\n\n💡 <b>Помощь</b>\n"
            "• ❓ FAQ — https://docs.karma-system.com/faq\n"
            "• 🛠️ Решение проблем — https://docs.karma-system.com/troubleshooting\n"
            "• 🆘 Поддержка — https://t.me/karma_system_official"
        )

        text = f"{base_text}{''.join(extra)}{help_tail}"

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
        
        # Получаем текст помощи для роли (как выше)
        help_service = HelpService()
        base_text = await help_service.get_help_message(message.from_user.id)
        extra = []
        if user_role in ["admin", "super_admin"]:
            extra.append(
                "\n\n🛡️ <b>Администраторы</b>\n"
                "• 📊 Админская панель — https://docs.karma-system.com/admin/dashboard\n"
                "• ✅ Модерация заявок — https://docs.karma-system.com/admin/moderation\n"
                "• 👥 Управление пользователями — https://docs.karma-system.com/admin/users\n"
                "• ⚙️ Системные настройки — https://docs.karma-system.com/admin/settings"
            )
        if user_role == "super_admin":
            extra.append(
                "\n\n👑 <b>Супер-администраторы</b>\n"
                "• 🖥️ Супер-админ панель — https://docs.karma-system.com/superadmin/dashboard\n"
                "• 🛡️ Управление администраторами — https://docs.karma-system.com/superadmin/admins\n"
                "• 📊 Системная аналитика — https://docs.karma-system.com/superadmin/analytics"
            )
        help_tail = (
            "\n\n💡 <b>Помощь</b>\n"
            "• ❓ FAQ — https://docs.karma-system.com/faq\n"
            "• 🛠️ Решение проблем — https://docs.karma-system.com/troubleshooting\n"
            "• 🆘 Поддержка — https://t.me/karma_system_official"
        )
        text = f"{base_text}{''.join(extra)}{help_tail}"
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
        
        # Получаем текст помощи (как выше)
        help_service = HelpService()
        base_text = await help_service.get_help_message(message.from_user.id)
        extra = []
        if user_role in ["admin", "super_admin"]:
            extra.append(
                "\n\n🛡️ <b>Администраторы</b>\n"
                "• 📊 Админская панель — https://docs.karma-system.com/admin/dashboard\n"
                "• ✅ Модерация заявок — https://docs.karma-system.com/admin/moderation\n"
                "• 👥 Управление пользователями — https://docs.karma-system.com/admin/users\n"
                "• ⚙️ Системные настройки — https://docs.karma-system.com/admin/settings"
            )
        if user_role == "super_admin":
            extra.append(
                "\n\n👑 <b>Супер-администраторы</b>\n"
                "• 🖥️ Супер-админ панель — https://docs.karma-system.com/superadmin/dashboard\n"
                "• 🛡️ Управление администраторами — https://docs.karma-system.com/superadmin/admins\n"
                "• 📊 Системная аналитика — https://docs.karma-system.com/superadmin/analytics"
            )
        help_tail = (
            "\n\n💡 <b>Помощь</b>\n"
            "• ❓ FAQ — https://docs.karma-system.com/faq\n"
            "• 🛠️ Решение проблем — https://docs.karma-system.com/troubleshooting\n"
            "• 🆘 Поддержка — https://t.me/karma_system_official"
        )
        text = f"{base_text}{''.join(extra)}{help_tail}"
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
    q = message.text
    # Простая заглушка ответа
    ai_response = f"Спасибо за ваш вопрос: ‘{q}’. Я анализирую и скоро дам ответ!"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Задать еще вопрос", callback_data="ai_agent:ask")],
        [InlineKeyboardButton(text="◀️ Назад к AI", callback_data="ai_agent:start")],
    ])
    await message.answer(f"🤖 <b>AI Агент отвечает:</b>\n\n{ai_response}", reply_markup=kb, parse_mode="HTML")
    await state.clear()
