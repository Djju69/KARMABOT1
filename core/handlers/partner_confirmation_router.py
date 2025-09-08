"""
Роутер для обработки FSM подтверждения регистрации партнеров
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from core.fsm.partner_confirmation import PartnerConfirmation, handle_confirmation_response
from core.keyboards.reply_v2 import get_user_cabinet_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(PartnerConfirmation.waiting_for_telegram_confirmation)
async def process_telegram_confirmation(message: Message, state: FSMContext):
    """Обработка подтверждения через Telegram"""
    try:
        await handle_confirmation_response(message, state)
    except Exception as e:
        logger.error(f"Error in process_telegram_confirmation: {e}")
        await message.answer("❌ Ошибка при обработке подтверждения.")

# Обработчик для администраторов для подтверждения кодов
@router.message(F.text.startswith("/confirm_partner"))
async def handle_admin_confirm_partner(message: Message, state: FSMContext):
    """Обработчик для администраторов для подтверждения кодов партнеров"""
    try:
        # Проверяем права администратора
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав. Только администраторы могут подтверждать коды.")
            return
        
        # Парсим команду: /confirm_partner <user_id> <code>
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer(
                "❌ Неверный формат команды.\n\n"
                "Использование: /confirm_partner <user_id> <code>\n"
                "Пример: /confirm_partner 123456789 123456"
            )
            return
        
        try:
            user_id = int(parts[1])
            code = parts[2]
        except ValueError:
            await message.answer("❌ Неверный формат user_id или кода.")
            return
        
        # Подтверждаем код
        from core.fsm.partner_confirmation import confirm_partner_code
        success = await confirm_partner_code(message.from_user.id, user_id, code)
        
        if success:
            await message.answer(
                f"✅ Код подтвержден для пользователя {user_id}\n\n"
                f"📱 Пользователь может завершить регистрацию партнера."
            )
        else:
            await message.answer(
                f"❌ Код не найден или неверный для пользователя {user_id}\n\n"
                f"💡 Убедитесь, что пользователь отправил код правильно."
            )
            
    except Exception as e:
        logger.error(f"Error in handle_admin_confirm_partner: {e}")
        await message.answer("❌ Ошибка при подтверждении кода.")

# Обработчик для просмотра ожидающих подтверждения
@router.message(F.text == "/pending_partners")
async def handle_pending_partners(message: Message, state: FSMContext):
    """Показать список партнеров, ожидающих подтверждения"""
    try:
        # Проверяем права администратора
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав. Только администраторы могут просматривать ожидающих.")
            return
        
        from core.fsm.partner_confirmation import confirmation_codes
        
        if not confirmation_codes:
            await message.answer("📋 Нет партнеров, ожидающих подтверждения.")
            return
        
        text = "📋 <b>Партнеры, ожидающие подтверждения:</b>\n\n"
        
        for user_id, data in confirmation_codes.items():
            partner_data = data.get('partner_data', {})
            code = data.get('code', 'N/A')
            confirmed = data.get('confirmed', False)
            
            status = "✅ Подтвержден" if confirmed else "⏳ Ожидает"
            
            text += f"🆔 <b>ID:</b> {user_id}\n"
            text += f"🏢 <b>Бизнес:</b> {partner_data.get('business_name', 'N/A')}\n"
            text += f"👤 <b>Контакт:</b> {partner_data.get('contact_name', 'N/A')}\n"
            text += f"🔑 <b>Код:</b> {code}\n"
            text += f"📊 <b>Статус:</b> {status}\n\n"
        
        text += f"💡 <b>Команды:</b>\n"
        text += f"• /confirm_partner <user_id> <code> - подтвердить код\n"
        text += f"• /pending_partners - обновить список"
        
        await message.answer(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in handle_pending_partners: {e}")
        await message.answer("❌ Ошибка при загрузке списка ожидающих.")

# Экспорт роутера
__all__ = ['router']
