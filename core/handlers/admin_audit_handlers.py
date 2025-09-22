"""
Обработчики для работы с аудит-логом администратора.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.security.roles import require_permission, Permission, Role
from core.database import role_repository

logger = logging.getLogger(__name__)
router = Router()

class AuditLogStates(StatesGroup):
    """Состояния для работы с аудит-логом."""
    waiting_for_date_range = State()
    waiting_for_action = State()

@router.message(Command("audit_log"))
@require_permission(Permission.VIEW_AUDIT_LOG)
async def cmd_audit_log(message: types.Message, state: FSMContext):
    """Обработчик команды просмотра аудит-лога."""
    user_id = message.from_user.id
    
    # Создаем клавиатуру с вариантами периода
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕒 Последний час", callback_data="audit_last_hour")],
        [InlineKeyboardButton(text="📅 Сегодня", callback_data="audit_today")],
        [InlineKeyboardButton(text="📆 Вчера", callback_data="audit_yesterday")],
        [InlineKeyboardButton(text="📊 Задать период", callback_data="audit_custom")]
    ])
    
    await message.answer(
        "📋 <b>Аудит-лог системы</b>\n\n"
        "Выберите период для отображения записей:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("audit_"))
@require_permission(Permission.VIEW_AUDIT_LOG)
async def process_audit_period(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора периода для аудит-лога."""
    period = callback.data.replace("audit_", "")
    now = datetime.utcnow()
    
    if period == "last_hour":
        start_date = now - timedelta(hours=1)
        await show_audit_log(callback, start_date, now, "за последний час")
    elif period == "today":
        start_date = datetime(now.year, now.month, now.day)
        await show_audit_log(callback, start_date, now, "за сегодня")
    elif period == "yesterday":
        end_date = datetime(now.year, now.month, now.day)
        start_date = end_date - timedelta(days=1)
        await show_audit_log(callback, start_date, end_date, "за вчера")
    elif period == "custom":
        await callback.message.answer(
            "📅 Введите период в формате:\n"
            "<code>ДД.ММ.ГГГГ - ДД.ММ.ГГГГ</code>\n\n"
            "Например: 01.09.2023 - 15.09.2023",
            parse_mode="HTML"
        )
        await state.set_state(AuditLogStates.waiting_for_date_range)
    
    await callback.answer()

@router.message(AuditLogStates.waiting_for_date_range)
@require_permission(Permission.VIEW_AUDIT_LOG)
async def process_custom_date_range(message: types.Message, state: FSMContext):
    """Обработка введенного пользовательского периода."""
    try:
        date_range = message.text.split(" - ")
        if len(date_range) != 2:
            raise ValueError("Неверный формат даты")
            
        start_date = datetime.strptime(date_range[0].strip(), "%d.%m.%Y")
        end_date = datetime.strptime(date_range[1].strip(), "%d.%m.%Y") + timedelta(days=1)  # До конца дня
        
        if start_date >= end_date:
            raise ValueError("Начальная дата должна быть раньше конечной")
            
        period_text = f"с {date_range[0]} по {date_range[1]}"
        await show_audit_log(message, start_date, end_date, period_text)
        await state.clear()
        
    except ValueError as e:
        await message.answer(
            "❌ Неверный формат даты. Пожалуйста, введите даты в формате:\n"
            "<code>ДД.ММ.ГГГГ - ДД.ММ.ГГГ</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error processing custom date range: {e}")
        await message.answer("❌ Произошла ошибка при обработке даты. Пожалуйста, попробуйте снова.")

async def show_audit_log(
    message_or_callback: types.Message | types.CallbackQuery,
    start_date: datetime,
    end_date: datetime,
    period_text: str
):
    """Отображает записи аудит-лога за указанный период."""
    try:
        # Получаем записи из аудит-лога
        logs = await role_repository.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=20  # Ограничиваем количество записей для предотвращения перегрузки
        )
        
        if not logs:
            text = f"📭 Нет записей в аудит-логе {period_text}."
        else:
            text = f"📋 <b>Аудит-лог {period_text}</b>\n\n"
            
            for log in logs:
                # Форматируем дату и время
                log_time = log['created_at'].strftime("%d.%m.%Y %H:%M:%S")
                
                # Получаем имя пользователя
                username = log.get('username')
                first_name = log.get('first_name', 'Неизвестно')
                last_name = log.get('last_name', '')
                user_info = f"{first_name} {last_name}".strip()
                if username:
                    user_info += f" (@{username})"
                
                # Формируем текст записи
                text += (
                    f"🕒 <b>{log_time}</b>\n"
                    f"👤 <b>Пользователь:</b> {user_info}\n"
                    f"🔧 <b>Действие:</b> {log['action']}\n"
                )
                
                # Добавляем информацию о сущности, если есть
                if log['entity_type'] and log['entity_id']:
                    text += f"📌 <b>Объект:</b> {log['entity_type']} (ID: {log['entity_id']})\n"
                text += "\n" + "─" * 30 + "\n\n"
            
            # Добавляем информацию о количестве записей
            text += f"\nВсего записей: {len(logs)}"
        
        # Отправляем сообщение
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.message.answer(text, parse_mode="HTML")
        else:
            await message_or_callback.answer(text, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Error showing audit log: {e}", exc_info=True)
        error_msg = "❌ Произошла ошибка при получении записей аудит-лога."
        
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.message.answer(error_msg)
        else:
            await message_or_callback.answer(error_msg)

# Регистрируем обработчики
handlers = [router]
