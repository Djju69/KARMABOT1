from datetime import datetime
from io import BytesIO
from typing import Dict, Any

from aiogram import F, Router, html
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.services.loyalty_service import loyalty_service
from core.services.referral_service import referral_service
from core.services.profile_service import profile_service
from core.services.qr_code_service import qr_code_service
from core.keyboards.profile import (
    get_profile_keyboard,
    get_back_to_profile_keyboard,
    get_qr_codes_keyboard
)
from core.database.db_v2 import db_v2

import logging

logger = logging.getLogger(__name__)
router = Router()

class QRCodeStates(StatesGroup):
    """States for QR code generation flow."""
    waiting_for_points = State()
    confirming_qr_creation = State()

@router.message(Command("profile"))
@router.callback_query(F.data == "profile")
async def show_profile(update: Message | CallbackQuery, state: FSMContext):
    """Показать личный кабинет пользователя"""
    try:
        # Сбрасываем состояние
        await state.clear()
        
        user = update.from_user
        user_id = str(user.id)
        
        # Получаем данные из сервисов
        try:
            # Получаем полный профиль пользователя
            profile_data = await profile_service.get_user_profile(user_id)
            
            # Получаем статистику лояльности
            loyalty_stats = await loyalty_service.get_user_stats(user_id)
            
            # Получаем статистику рефералов
            referral_stats = await referral_service.get_referral_stats(user_id)
            
            # Формируем сообщение
            balance = loyalty_stats.get('balance', {})
            total_points = balance.get('total_points', 0)
            available_points = balance.get('available_points', 0)
            
            text = (
                f"👤 <b>Личный кабинет</b>\n"
                f"➖➖➖➖➖➖➖➖➖\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"👤 {html.escape(user.full_name)}\n"
                f"💎 Баланс: <b>{total_points} баллов</b>\n"
                f"💰 Доступно: <b>{available_points} баллов</b>\n"
                f"👥 Рефералов: <b>{referral_stats.get('total_referrals', 0)}</b>\n"
                f"💰 Заработано: <b>{referral_stats.get('total_earned', 0)} баллов</b>\n"
                f"🔗 Реф. ссылка: <code>{referral_stats.get('referral_link', '')}</code>\n"
                f"📊 Уровень: <b>{loyalty_stats.get('level', 1)}</b>"
            )
            
            # Создаем клавиатуру
            keyboard = get_profile_keyboard()
            
            # Отправляем или обновляем сообщение
            if isinstance(update, CallbackQuery):
                await update.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            else:
                await update.answer(
                    text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
                
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            error_msg = "❌ Произошла ошибка при загрузке данных. Пожалуйста, попробуйте позже."
            if isinstance(update, CallbackQuery):
                await update.answer(error_msg, show_alert=True)
            else:
                await update.answer(error_msg)
                
    except Exception as e:
        logger.error(f"Error in show_profile: {e}")
        if isinstance(update, CallbackQuery):
            await update.answer("❌ Произошла ошибка. Пожалуйста, попробуйте снова.", show_alert=True)
        else:
            await update.answer("❌ Произошла ошибка. Пожалуйста, попробуйте снова.")

@router.callback_query(F.data == "loyalty_history")
async def show_loyalty_history(callback: CallbackQuery):
    """Показать историю операций с баллами"""
    try:
        user_id = str(callback.from_user.id)
        
        # Получаем историю транзакций через сервис
        transactions = await loyalty_service.get_user_transactions(
            user_id=user_id,
            limit=10
        )
        
        if not transactions:
            await callback.answer("📭 У вас пока нет операций с баллами")
            return
        
        # Формируем историю операций
        history = ["📊 <b>История операций:</b>\n"]
        for tx in transactions:
            points = tx.get('points', 0)
            sign = "➕" if points > 0 else "➖"
            created_at = tx.get('created_at', datetime.utcnow())
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            history.append(
                f"<b>{created_at.strftime('%d.%m.%Y %H:%M')}</b> | "
                f"{sign} {abs(points)} баллов\n"
                f"<i>{tx.get('description', 'Операция')}</i>\n"
                f"{'-'*20}"
            )
        
        # Добавляем кнопку "Назад"
        keyboard = get_back_to_profile_keyboard()
        
        # Отправляем историю
        await callback.message.edit_text(
            "\n".join(history),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing loyalty history: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке истории операций")

@router.callback_query(F.data == "referrals")
async def show_referrals(callback: CallbackQuery):
    """Показать информацию о рефералах"""
    try:
        user_id = str(callback.from_user.id)
        
        # Получаем статистику рефералов
        ref_stats = await referral_service.get_referral_stats(user_id)
        
        # Формируем сообщение
        text = (
            f"👥 <b>Реферальная программа</b>\n"
            f"➖➖➖➖➖➖➖➖➖\n"
            f"🔗 Ваша ссылка:\n"
            f"<code>{ref_stats.get('referral_link', '')}</code>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"👥 Всего рефералов: <b>{ref_stats.get('total_referrals', 0)}</b>\n"
            f"💰 Заработано: <b>{ref_stats.get('total_earned', 0)} баллов</b>\n"
            f"🎁 Бонус за приглашение: <b>{ref_stats.get('referrer_bonus', 100)} баллов</b>\n"
            f"🎁 Бонус новому пользователю: <b>{ref_stats.get('referee_bonus', 50)} баллов</b>\n\n"
            f"💡 <i>Приглашайте друзей и получайте бонусы!</i>"
        )
        
        # Добавляем кнопку "Назад"
        keyboard = get_back_to_profile_keyboard()
        
        # Отправляем информацию
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing referrals: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке информации о рефералах")

@router.callback_query(F.data == "notifications")
async def show_notifications(callback: CallbackQuery):
    """Показать уведомления пользователя"""
    try:
        user_id = str(callback.from_user.id)
        
        # Получаем уведомления
        notifications = await profile_service.get_user_notifications(
            user_id=user_id,
            limit=10,
            unread_only=False
        )
        
        if not notifications:
            text = "📭 У вас пока нет уведомлений"
        else:
            text = "🔔 <b>Ваши уведомления:</b>\n\n"
            for notif in notifications:
                status = "🔴" if not notif.get('is_read', False) else "🟢"
                created_at = notif.get('created_at', datetime.utcnow())
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                text += (
                    f"{status} <b>{notif.get('title', 'Уведомление')}</b>\n"
                    f"<i>{notif.get('message', '')}</i>\n"
                    f"<small>{created_at.strftime('%d.%m.%Y %H:%M')}</small>\n"
                    f"{'-'*20}\n"
                )
        
        # Добавляем кнопку "Назад"
        keyboard = get_back_to_profile_keyboard()
        
        # Отправляем уведомления
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing notifications: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке уведомлений")

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Показать настройки пользователя"""
    try:
        user_id = str(callback.from_user.id)
        
        # Получаем настройки
        settings = await profile_service.get_user_settings(user_id)
        
        # Формируем сообщение
        text = (
            f"⚙️ <b>Настройки</b>\n"
            f"➖➖➖➖➖➖➖➖➖\n"
            f"🌐 Язык: <b>{settings.get('language', 'ru')}</b>\n"
            f"🎨 Тема: <b>{settings.get('preferences', {}).get('theme', 'light')}</b>\n"
            f"🕐 Часовой пояс: <b>{settings.get('preferences', {}).get('timezone', 'UTC+7')}</b>\n"
            f"💰 Валюта: <b>{settings.get('preferences', {}).get('currency', 'VND')}</b>\n\n"
            f"🔔 <b>Уведомления:</b>\n"
            f"📧 Email: {'✅' if settings.get('notifications', {}).get('email', True) else '❌'}\n"
            f"📱 Push: {'✅' if settings.get('notifications', {}).get('push', True) else '❌'}\n"
            f"📱 SMS: {'✅' if settings.get('notifications', {}).get('sms', False) else '❌'}\n\n"
            f"🔒 <b>Приватность:</b>\n"
            f"👤 Показывать профиль: {'✅' if settings.get('privacy', {}).get('show_profile', True) else '❌'}\n"
            f"📊 Показывать активности: {'✅' if settings.get('privacy', {}).get('show_activities', False) else '❌'}\n"
            f"💬 Разрешить сообщения: {'✅' if settings.get('privacy', {}).get('allow_messages', True) else '❌'}\n\n"
            f"💡 <i>Настройки можно изменить в веб-версии</i>"
        )
        
        # Добавляем кнопку "Назад"
        keyboard = get_back_to_profile_keyboard()
        
        # Отправляем настройки
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing settings: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке настроек")
