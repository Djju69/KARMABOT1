from aiogram import F, Router, html
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.services.loyalty import loyalty_service
from core.services.referral_service import referral_service
from core.services.qr_code_service import QRCodeService
from core.keyboards.profile import get_profile_keyboard, get_back_to_profile_keyboard

import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("profile"))
@router.callback_query(F.data == "profile")
async def show_profile(update: Message | CallbackQuery, state: FSMContext):
    """Показать личный кабинет пользователя"""
    try:
        user = update.from_user
        user_id = user.id
        
        # Получаем данные из сервисов
        try:
            balance = await loyalty_service.get_balance(user_id)
            ref_stats = await referral_service.get_referral_stats(user_id)
            
            # Формируем сообщение
            text = (
                f"👤 <b>Личный кабинет</b>\n"
                f"➖➖➖➖➖➖➖➖➖\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"👤 {html.escape(user.full_name)}\n"
                f"💎 Баланс: <b>{balance} баллов</b>\n"
                f"👥 Рефералов: <b>{ref_stats.get('total_referrals', 0)}</b>\n"
                f"💰 Заработано: <b>{ref_stats.get('total_earned', 0)} баллов</b>\n"
                f"🔗 Реф. ссылка: <code>{ref_stats.get('referral_link', '')}</code>"
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
            logger.error(f"Error loading profile data: {e}", exc_info=True)
            error_text = "❌ Произошла ошибка при загрузке данных профиля. Пожалуйста, попробуйте позже."
            if isinstance(update, CallbackQuery):
                await update.message.answer(error_text)
            else:
                await update.answer(error_text)
                
    except Exception as e:
        logger.error(f"Unexpected error in show_profile: {e}", exc_info=True)

@router.callback_query(F.data == "loyalty_history")
async def show_loyalty_history(callback: CallbackQuery):
    """Показать историю операций с баллами"""
    try:
        user_id = callback.from_user.id
        
        # Получаем историю транзакций
        with db_v2.get_connection() as conn:
            transactions = conn.execute(
                """
                SELECT amount, description, created_at 
                FROM loyalty_transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
                """,
                (user_id,)
            ).fetchall()
        
        if not transactions:
            await callback.answer("📭 У вас пока нет операций с баллами")
            return
        
        # Формируем историю операций
        history = ["📊 <b>История операций:</b>\n"]
        for tx in transactions:
            amount = tx['amount']
            sign = "➕" if amount > 0 else "➖"
            history.append(
                f"<b>{tx['created_at'].strftime('%d.%m.%Y %H:%M')}</b> | "
                f"{sign} {abs(amount)} баллов\n"
                f"<i>{tx['description']}</i>\n"
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
