"""
Админ-интерфейс для управления тарифной системой партнеров
"""
import logging
from typing import List, Dict, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.services.tariff_service import tariff_service
from core.models.tariff_models import TariffType
from core.security.roles import get_user_role

logger = logging.getLogger(__name__)
router = Router(name="tariff_admin_router")

@router.message(F.text == "💰 Управление тарифами")
async def handle_tariff_management(message: Message, state: FSMContext):
    """Обработчик кнопки управления тарифами (только для админов)"""
    try:
        # Проверяем права доступа
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав для управления тарифами")
            return
        
        # Получаем все тарифы
        tariffs = await tariff_service.get_all_tariffs()
        
        if not tariffs:
            await message.answer("❌ Тарифы не найдены")
            return
        
        # Создаем клавиатуру с тарифами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for tariff in tariffs:
            price_text = f"{tariff.price_vnd:,} VND/мес" if tariff.price_vnd > 0 else "Бесплатно"
            button_text = f"{tariff.name} - {price_text}"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"tariff_view:{tariff.tariff_type.value}"
                )
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="📊 Статистика тарифов", callback_data="tariff_stats"),
            InlineKeyboardButton(text="➕ Создать тариф", callback_data="tariff_create")
        ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад в админ-панель", callback_data="admin_panel")
        ])
        
        text = "💰 <b>Управление тарифной системой</b>\n\n"
        text += "Выберите тариф для просмотра или управления:"
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in tariff management: {e}")
        await message.answer("❌ Ошибка при загрузке тарифов")

@router.callback_query(F.data.startswith("tariff_view:"))
async def handle_tariff_view(callback: CallbackQuery, state: FSMContext):
    """Просмотр детальной информации о тарифе"""
    try:
        tariff_type_str = callback.data.split(":")[1]
        tariff_type = TariffType(tariff_type_str)
        
        tariff = await tariff_service.get_tariff_by_type(tariff_type)
        if not tariff:
            await callback.answer("❌ Тариф не найден")
            return
        
        # Формируем детальную информацию
        text = f"💰 <b>{tariff.name}</b>\n\n"
        text += f"📋 <b>Тип:</b> {tariff.tariff_type.value}\n"
        text += f"💵 <b>Цена:</b> {tariff.price_vnd:,} VND/месяц\n" if tariff.price_vnd > 0 else "💵 <b>Цена:</b> Бесплатно\n"
        text += f"📊 <b>Лимит транзакций:</b> {tariff.features.max_transactions_per_month} в месяц\n" if tariff.features.max_transactions_per_month != -1 else "📊 <b>Лимит транзакций:</b> Безлимит\n"
        text += f"💸 <b>Комиссия:</b> {tariff.features.commission_rate * 100:.1f}%\n"
        text += f"📈 <b>Аналитика:</b> {'✅ Включена' if tariff.features.analytics_enabled else '❌ Отключена'}\n"
        text += f"🎯 <b>Приоритетная поддержка:</b> {'✅ Включена' if tariff.features.priority_support else '❌ Отключена'}\n"
        text += f"🔌 <b>API доступ:</b> {'✅ Включен' if tariff.features.api_access else '❌ Отключен'}\n"
        text += f"🛠️ <b>Кастомные интеграции:</b> {'✅ Включены' if tariff.features.custom_integrations else '❌ Отключены'}\n"
        text += f"👨‍💼 <b>Выделенный менеджер:</b> {'✅ Включен' if tariff.features.dedicated_manager else '❌ Отключен'}\n\n"
        text += f"📝 <b>Описание:</b> {tariff.description}\n"
        
        # Клавиатура управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"tariff_edit:{tariff_type.value}"),
                InlineKeyboardButton(text="📊 Подписчики", callback_data=f"tariff_subscribers:{tariff_type.value}")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад к тарифам", callback_data="tariff_management")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing tariff: {e}")
        await callback.answer("❌ Ошибка при просмотре тарифа")

@router.callback_query(F.data.startswith("tariff_subscribers:"))
async def handle_tariff_subscribers(callback: CallbackQuery, state: FSMContext):
    """Просмотр подписчиков тарифа"""
    try:
        tariff_type_str = callback.data.split(":")[1]
        tariff_type = TariffType(tariff_type_str)
        
        tariff = await tariff_service.get_tariff_by_type(tariff_type)
        if not tariff:
            await callback.answer("❌ Тариф не найден")
            return
        
        # Получаем подписчиков (заглушка - нужно реализовать в TariffService)
        text = f"📊 <b>Подписчики тарифа {tariff.name}</b>\n\n"
        text += "🔍 Функция в разработке...\n"
        text += "Здесь будет отображаться список партнеров, использующих данный тариф."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к тарифу", callback_data=f"tariff_view:{tariff_type.value}")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing tariff subscribers: {e}")
        await callback.answer("❌ Ошибка при просмотре подписчиков")

@router.callback_query(F.data == "tariff_stats")
async def handle_tariff_stats(callback: CallbackQuery, state: FSMContext):
    """Статистика по тарифам"""
    try:
        # Получаем все тарифы
        tariffs = await tariff_service.get_all_tariffs()
        
        text = "📊 <b>Статистика тарифной системы</b>\n\n"
        
        total_revenue = 0
        for tariff in tariffs:
            # Заглушка - нужно реализовать подсчет подписчиков
            subscribers_count = 0  # await tariff_service.get_subscribers_count(tariff.tariff_type)
            monthly_revenue = tariff.price_vnd * subscribers_count
            total_revenue += monthly_revenue
            
            text += f"💰 <b>{tariff.name}</b>\n"
            text += f"   👥 Подписчики: {subscribers_count}\n"
            text += f"   💵 Доход/месяц: {monthly_revenue:,} VND\n\n"
        
        text += f"📈 <b>Общий доход:</b> {total_revenue:,} VND/месяц\n"
        text += f"📊 <b>Всего тарифов:</b> {len(tariffs)}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к тарифам", callback_data="tariff_management")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing tariff stats: {e}")
        await callback.answer("❌ Ошибка при загрузке статистики")

@router.callback_query(F.data == "tariff_management")
async def handle_tariff_management_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback для управления тарифами"""
    try:
        # Получаем все тарифы
        tariffs = await tariff_service.get_all_tariffs()
        
        if not tariffs:
            await callback.answer("❌ Тарифы не найдены")
            return
        
        # Создаем клавиатуру с тарифами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for tariff in tariffs:
            price_text = f"{tariff.price_vnd:,} VND/мес" if tariff.price_vnd > 0 else "Бесплатно"
            button_text = f"{tariff.name} - {price_text}"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"tariff_view:{tariff.tariff_type.value}"
                )
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="📊 Статистика тарифов", callback_data="tariff_stats"),
            InlineKeyboardButton(text="➕ Создать тариф", callback_data="tariff_create")
        ])
        
        text = "💰 <b>Управление тарифной системой</b>\n\n"
        text += "Выберите тариф для просмотра или управления:"
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in tariff management callback: {e}")
        await callback.answer("❌ Ошибка при загрузке тарифов")
