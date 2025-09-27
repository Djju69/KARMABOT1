"""
Обработчики команд тарифов для всех пользователей
"""
import logging
from typing import List, Dict, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from core.services.tariff_service import tariff_service
from core.models.tariff_models import TariffType
from core.security.roles import get_user_role
from core.database.db_adapter import db_v2
from core.utils.locales_v2 import get_text

logger = logging.getLogger(__name__)
router = Router(name="tariffs_user_router")

@router.message(Command("tariffs"))
async def handle_tariffs_command(message: Message, state: FSMContext):
    """Команда /tariffs - показать все доступные тарифы для пользователей"""
    try:
        user_id = message.from_user.id
        
        # Получаем язык пользователя
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Получаем все тарифы
        tariffs = tariff_service.get_all_tariffs()
        
        if not tariffs:
            await message.answer(get_text('tariffs.no_tariffs', lang))
            return
        
        # Проверяем роль пользователя
        user_role = await get_user_role(user_id)
        is_partner = hasattr(user_role, 'name') and user_role.name in ['partner', 'admin', 'super_admin']
        
        # Получаем текущий тариф партнера
        current_tariff = None
        if is_partner:
            try:
                current_tariff = tariff_service.get_partner_current_tariff(user_id)
            except:
                pass
        
        # Формируем сообщение
        text = get_text("tariffs.title", lang) + "\n\n"
        
        if is_partner:
            text += get_text("tariffs.for_partners", lang) + "\n\n"
        else:
            text += get_text("tariffs.for_users", lang) + "\n\n"
        
        # Показываем все тарифы
        for tariff in tariffs:
            text += f"📋 <b>{tariff.name}</b>\n"
            
            # Цена
            if tariff.price_vnd > 0:
                text += f"💵 {get_text('tariffs.price', lang)}: {tariff.price_vnd:,} VND/{get_text('tariffs.month', lang)}\n"
            else:
                text += f"💵 {get_text('tariffs.price', lang)}: {get_text('tariffs.free', lang)}\n"
            
            # Лимит транзакций
            if tariff.features.max_transactions_per_month == -1:
                text += f"📊 {get_text('tariffs.transactions_limit', lang)}: {get_text('tariffs.unlimited', lang)}\n"
            else:
                text += f"📊 {get_text('tariffs.transactions_limit', lang)}: {tariff.features.max_transactions_per_month} {get_text('tariffs.per_month', lang)}\n"
            
            # Комиссия
            text += f"💸 {get_text('tariffs.commission', lang)}: {tariff.features.commission_rate * 100:.1f}%\n"
            
            # Функции
            features = []
            if tariff.features.analytics_enabled:
                features.append(get_text('tariffs.analytics', lang))
            if tariff.features.priority_support:
                features.append(get_text('tariffs.priority_support', lang))
            if tariff.features.api_access:
                features.append(get_text('tariffs.api_access', lang))
            if tariff.features.custom_integrations:
                features.append(get_text('tariffs.custom_integrations', lang))
            if tariff.features.dedicated_manager:
                features.append(get_text('tariffs.dedicated_manager', lang))
            
            if features:
                text += f"✨ {get_text('tariffs.description', lang)}: {', '.join(features)}\n"
            
            # Отмечаем текущий тариф
            if current_tariff and current_tariff.tariff_type == tariff.tariff_type:
                text += f"✅ <b>{get_text('tariffs.current_tariff', lang)}</b>\n"
            
            text += f"📝 {tariff.description}\n\n"
        
        # Добавляем информацию для обычных пользователей
        if not is_partner:
            text += f"🤝 <b>{get_text('tariffs.become_partner', lang)}</b>\n"
            text += f"{get_text('tariffs.become_partner_text', lang)}\n\n"
            text += f"📝 {get_text('tariffs.apply_instruction', lang)}"
        
        # Создаем клавиатуру только для партнеров
        if is_partner:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            
            for tariff in tariffs:
                # Определяем текст кнопки
                price_text = f"{tariff.price_vnd:,} VND/{get_text('tariffs.month', lang)}" if tariff.price_vnd > 0 else get_text('tariffs.free', lang)
                button_text = f"{tariff.name} - {price_text}"
                
                # Добавляем отметку текущего тарифа
                if current_tariff and current_tariff.tariff_type == tariff.tariff_type:
                    button_text += f" ✅"
                
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"tariff_info:{tariff.tariff_type.value}"
                    )
                ])
            
            # Добавляем кнопку помощи
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=get_text('tariffs.help_button', lang), callback_data="tariff_help")
            ])
            
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Для обычных пользователей - только текст без кнопок
            await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in tariffs command: {e}")
        await message.answer(get_text('tariffs.error_no_id', lang))

@router.callback_query(F.data.startswith("tariff_info:"))
async def handle_tariff_info(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию о тарифе (только для партнеров)"""
    try:
        user_id = callback.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверяем что пользователь партнер
        if not (hasattr(user_role, 'name') and user_role.name in ['partner', 'admin', 'super_admin']):
            await callback.answer("❌ Только партнеры могут управлять тарифами")
            return
        
        tariff_type_str = callback.data.split(":")[1]
        tariff_type = TariffType(tariff_type_str)
        
        tariff = tariff_service.get_tariff_by_type(tariff_type)
        if not tariff:
            await callback.answer("❌ Тариф не найден")
            return
        
        # Проверяем текущий тариф пользователя
        current_tariff = None
        try:
            current_tariff = await tariff_service.get_partner_current_tariff(user_id)
        except:
            pass
        
        # Формируем детальную информацию
        text = f"💰 <b>{tariff.name}</b>\n\n"
        
        # Цена
        if tariff.price_vnd > 0:
            text += f"💵 <b>Цена:</b> {tariff.price_vnd:,} VND/месяц\n"
        else:
            text += f"💵 <b>Цена:</b> Бесплатно\n"
        
        # Лимит транзакций
        if tariff.features.max_transactions_per_month == -1:
            text += f"📊 <b>Транзакции:</b> Безлимит\n"
        else:
            text += f"📊 <b>Транзакции:</b> {tariff.features.max_transactions_per_month} в месяц\n"
        
        # Комиссия
        text += f"💸 <b>Комиссия:</b> {tariff.features.commission_rate * 100:.1f}%\n\n"
        
        # Функции
        text += f"📈 <b>Аналитика:</b> {'✅ Включена' if tariff.features.analytics_enabled else '❌ Отключена'}\n"
        text += f"🎯 <b>Приоритетная поддержка:</b> {'✅ Включена' if tariff.features.priority_support else '❌ Отключена'}\n"
        text += f"🔌 <b>API доступ:</b> {'✅ Включен' if tariff.features.api_access else '❌ Отключен'}\n"
        text += f"🛠️ <b>Кастомные интеграции:</b> {'✅ Включены' if tariff.features.custom_integrations else '❌ Отключены'}\n"
        text += f"👨‍💼 <b>Выделенный менеджер:</b> {'✅ Включен' if tariff.features.dedicated_manager else '❌ Отключен'}\n\n"
        
        # Описание
        text += f"📝 <b>Описание:</b> {tariff.description}\n\n"
        
        # Статус текущего тарифа
        if current_tariff and current_tariff.tariff_type == tariff.tariff_type:
            text += "✅ <b>Это ваш текущий тариф</b>\n"
        elif current_tariff:
            text += f"ℹ️ <b>Ваш текущий тариф:</b> {current_tariff.name}\n"
        
        # Создаем клавиатуру действий (только для партнеров)
        keyboard_buttons = []
        
        if current_tariff and current_tariff.tariff_type == tariff.tariff_type:
            # Текущий тариф - показываем только информацию
            keyboard_buttons.append([
                InlineKeyboardButton(text="ℹ️ Это ваш тариф", callback_data="no_action")
            ])
        else:
            # Другой тариф - предлагаем переключиться
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔄 Переключиться на этот тариф", callback_data=f"tariff_apply:{tariff_type.value}")
            ])
        
        # Кнопки навигации
        keyboard_buttons.append([
            InlineKeyboardButton(text="◀️ Назад к тарифам", callback_data="back_to_tariffs"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="tariff_help")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing tariff info: {e}")
        await callback.answer("❌ Ошибка при просмотре тарифа")

@router.callback_query(F.data.startswith("tariff_apply:"))
async def handle_tariff_apply(callback: CallbackQuery, state: FSMContext):
    """Применить тариф (переключиться на него) - только для партнеров"""
    try:
        user_id = callback.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверяем что пользователь партнер
        if not (hasattr(user_role, 'name') and user_role.name in ['partner', 'admin', 'super_admin']):
            await callback.answer("❌ Только партнеры могут менять тарифы")
            return
        
        tariff_type_str = callback.data.split(":")[1]
        tariff_type = TariffType(tariff_type_str)
        
        # Получаем тариф
        tariff = tariff_service.get_tariff_by_type(tariff_type)
        if not tariff:
            await callback.answer("❌ Тариф не найден")
            return
        
        # Подтверждение смены тарифа
        text = f"🔄 <b>Подтверждение смены тарифа</b>\n\n"
        text += f"Вы хотите переключиться на тариф <b>{tariff.name}</b>?\n\n"
        
        if tariff.price_vnd > 0:
            text += f"💵 <b>Цена:</b> {tariff.price_vnd:,} VND/месяц\n"
        else:
            text += f"💵 <b>Цена:</b> Бесплатно\n"
        
        text += f"💸 <b>Комиссия:</b> {tariff.features.commission_rate * 100:.1f}%\n"
        
        if tariff.features.max_transactions_per_month == -1:
            text += f"📊 <b>Транзакции:</b> Безлимит\n"
        else:
            text += f"📊 <b>Транзакции:</b> {tariff.features.max_transactions_per_month} в месяц\n\n"
        
        text += "⚠️ <b>Внимание:</b> Смена тарифа вступит в силу немедленно.\n"
        text += "Если у вас есть активные транзакции, они будут учтены в новом тарифе."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"tariff_confirm:{tariff_type.value}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"tariff_info:{tariff_type.value}")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error applying tariff: {e}")
        await callback.answer("❌ Ошибка при применении тарифа")

@router.callback_query(F.data.startswith("tariff_confirm:"))
async def handle_tariff_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение смены тарифа - только для партнеров"""
    try:
        user_id = callback.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверяем что пользователь партнер
        if not (hasattr(user_role, 'name') and user_role.name in ['partner', 'admin', 'super_admin']):
            await callback.answer("❌ Только партнеры могут менять тарифы")
            return
        
        tariff_type_str = callback.data.split(":")[1]
        tariff_type = TariffType(tariff_type_str)
        
        # Получаем тариф
        tariff = tariff_service.get_tariff_by_type(tariff_type)
        if not tariff:
            await callback.answer("❌ Тариф не найден")
            return
        
        # Применяем тариф
        success = tariff_service.subscribe_partner_to_tariff(user_id, tariff_type)
        
        if success:
            text = f"✅ <b>Тариф успешно изменен!</b>\n\n"
            text += f"Ваш новый тариф: <b>{tariff.name}</b>\n\n"
            
            if tariff.price_vnd > 0:
                text += f"💵 Цена: {tariff.price_vnd:,} VND/месяц\n"
            else:
                text += f"💵 Цена: Бесплатно\n"
            
            text += f"💸 Комиссия: {tariff.features.commission_rate * 100:.1f}%\n"
            
            if tariff.features.max_transactions_per_month == -1:
                text += f"📊 Транзакции: Безлимит\n"
            else:
                text += f"📊 Транзакции: {tariff.features.max_transactions_per_month} в месяц\n\n"
            
            text += "🎉 Тариф активирован и готов к использованию!"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
            ])
            
        else:
            text = "❌ <b>Ошибка при смене тарифа</b>\n\n"
            text += "Не удалось применить выбранный тариф.\n"
            text += "Попробуйте позже или обратитесь в поддержку."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Попробовать снова", callback_data="back_to_tariffs")]
            ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error confirming tariff: {e}")
        await callback.answer("❌ Ошибка при подтверждении тарифа")

@router.callback_query(F.data == "back_to_tariffs")
async def handle_back_to_tariffs(callback: CallbackQuery, state: FSMContext):
    """Вернуться к списку тарифов - только для партнеров"""
    try:
        user_id = callback.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверяем что пользователь партнер
        if not (hasattr(user_role, 'name') and user_role.name in ['partner', 'admin', 'super_admin']):
            await callback.answer("❌ Только партнеры могут управлять тарифами")
            return
        
        # Получаем все тарифы
        tariffs = tariff_service.get_all_tariffs()
        
        if not tariffs:
            await callback.answer("❌ Тарифы временно недоступны")
            return
        
        # Формируем сообщение
        text = "💰 <b>Доступные тарифы партнерства</b>\n\n"
        text += "Выберите подходящий тариф для вашего бизнеса:\n\n"
        
        # Создаем клавиатуру с тарифами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for tariff in tariffs:
            price_text = f"{tariff.price_vnd:,} VND/мес" if tariff.price_vnd > 0 else "Бесплатно"
            button_text = f"{tariff.name} - {price_text}"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"tariff_info:{tariff.tariff_type.value}"
                )
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="❓ Помощь по тарифам", callback_data="tariff_help")
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error going back to tariffs: {e}")
        await callback.answer("❌ Ошибка при возврате к тарифам")

@router.callback_query(F.data == "tariff_help")
async def handle_tariff_help(callback: CallbackQuery, state: FSMContext):
    """Помощь по тарифам - только для партнеров"""
    try:
        user_id = callback.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверяем что пользователь партнер
        if not (hasattr(user_role, 'name') and user_role.name in ['partner', 'admin', 'super_admin']):
            await callback.answer("❌ Только партнеры могут управлять тарифами")
            return
        
        text = "❓ <b>Помощь по тарифам</b>\n\n"
        text += "💰 <b>FREE STARTER</b> - Бесплатный тариф для начала работы\n"
        text += "• 15 транзакций в месяц\n"
        text += "• Комиссия 12%\n"
        text += "• Базовые функции\n\n"
        
        text += "💼 <b>BUSINESS</b> - Для растущего бизнеса\n"
        text += "• 100 транзакций в месяц\n"
        text += "• Комиссия 6%\n"
        text += "• Аналитика + приоритетная поддержка\n\n"
        
        text += "🏢 <b>ENTERPRISE</b> - Для крупного бизнеса\n"
        text += "• Безлимит транзакций\n"
        text += "• Комиссия 4%\n"
        text += "• Все функции: API, интеграции, менеджер\n\n"
        
        text += "💡 <b>Как сменить тариф:</b>\n"
        text += "1. Выберите подходящий тариф\n"
        text += "2. Нажмите 'Переключиться на этот тариф'\n"
        text += "3. Подтвердите смену\n\n"
        
        text += "❓ <b>Нужна помощь?</b> Обратитесь в поддержку!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к тарифам", callback_data="back_to_tariffs")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing tariff help: {e}")
        await callback.answer("❌ Ошибка при показе помощи")

# Убрали обработчики для обычных пользователей - они не должны иметь доступ к кнопкам

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    await callback.message.delete()
    await callback.answer("🏠 Возвращаемся в главное меню")
