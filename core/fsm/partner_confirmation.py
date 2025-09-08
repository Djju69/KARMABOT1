"""
FSM для подтверждения регистрации партнера через код в Telegram
"""
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from core.utils.texts import get_text
import logging
import random
import string

logger = logging.getLogger(__name__)

class PartnerConfirmation(StatesGroup):
    waiting_for_confirmation_code = State()
    waiting_for_telegram_confirmation = State()

# Хранилище кодов подтверждения (в продакшене использовать Redis)
confirmation_codes = {}

def generate_confirmation_code() -> str:
    """Генерирует код подтверждения из 6 цифр"""
    return ''.join(random.choices(string.digits, k=6))

async def start_partner_confirmation(message: Message, state: FSMContext):
    """Начать процесс подтверждения регистрации партнера"""
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'ru')
        
        # Генерируем код подтверждения
        confirmation_code = generate_confirmation_code()
        user_id = message.from_user.id
        
        # Сохраняем код в памяти (в продакшене - в Redis)
        confirmation_codes[user_id] = {
            'code': confirmation_code,
            'partner_data': user_data.get('partner_data', {}),
            'created_at': message.date
        }
        
        await message.answer(
            f"🔐 <b>Подтверждение регистрации партнера</b>\n\n"
            f"📱 Для завершения регистрации необходимо подтвердить ваш Telegram аккаунт.\n\n"
            f"🔑 <b>Код подтверждения:</b> <code>{confirmation_code}</code>\n\n"
            f"📋 <b>Инструкция:</b>\n"
            f"1. Скопируйте код выше\n"
            f"2. Отправьте его в личные сообщения боту @KarmaBotSupport\n"
            f"3. Дождитесь подтверждения от администратора\n"
            f"4. Вернитесь сюда и нажмите '✅ Подтверждено'\n\n"
            f"⏰ Код действителен в течение 10 минут\n"
            f"🔄 Если код истек, нажмите '🔄 Получить новый код'",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        
        await state.set_state(PartnerConfirmation.waiting_for_telegram_confirmation)
        
    except Exception as e:
        logger.error(f"Error in start_partner_confirmation: {e}")
        await message.answer("❌ Ошибка при генерации кода подтверждения.")

async def handle_confirmation_response(message: Message, state: FSMContext):
    """Обработка ответа пользователя на подтверждение"""
    try:
        user_id = message.from_user.id
        
        if message.text == "✅ Подтверждено":
            # Проверяем, подтвержден ли код администратором
            if user_id in confirmation_codes:
                code_data = confirmation_codes[user_id]
                
                if code_data.get('confirmed', False):
                    # Код подтвержден, завершаем регистрацию
                    await complete_partner_registration(message, state, code_data['partner_data'])
                else:
                    await message.answer(
                        "⏳ Код еще не подтвержден администратором.\n\n"
                        "📱 Убедитесь, что вы отправили код в @KarmaBotSupport\n"
                        "⏰ Дождитесь подтверждения или получите новый код"
                    )
            else:
                await message.answer("❌ Код подтверждения не найден. Начните регистрацию заново.")
                
        elif message.text == "🔄 Получить новый код":
            # Генерируем новый код
            await start_partner_confirmation(message, state)
            
        elif message.text == "❌ Отмена":
            # Отменяем регистрацию
            await cancel_partner_registration(message, state)
            
        else:
            await message.answer(
                "❓ Неизвестная команда.\n\n"
                "Доступные действия:\n"
                "• ✅ Подтверждено - если код подтвержден\n"
                "• 🔄 Получить новый код - если нужен новый код\n"
                "• ❌ Отмена - отменить регистрацию"
            )
            
    except Exception as e:
        logger.error(f"Error in handle_confirmation_response: {e}")
        await message.answer("❌ Ошибка при обработке подтверждения.")

async def complete_partner_registration(message: Message, state: FSMContext, partner_data: dict):
    """Завершить регистрацию партнера"""
    try:
        from core.database.db_v2 import get_connection
        from core.keyboards.reply_v2 import get_user_cabinet_keyboard
        
        user_id = message.from_user.id
        
        # Сохраняем данные партнера в БД
        with get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO partners (
                    code, title, status, base_discount_pct, contact_name, 
                    contact_telegram, contact_phone, contact_email, legal_info, 
                    created_at, approved_by, approved_at
                ) VALUES (?, ?, 'approved', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                partner_data.get('business_name', '')[:50],  # code
                partner_data.get('business_name', ''),
                partner_data.get('base_discount_pct', 0.0),
                partner_data.get('contact_name', ''),
                user_id,
                partner_data.get('contact_phone', ''),
                partner_data.get('contact_email', ''),
                partner_data.get('legal_info', ''),
                message.date.isoformat(),
                user_id,  # approved_by (самоподтверждение через код)
                message.date.isoformat()
            ))
            
            partner_id = cursor.lastrowid
            
            # Обновляем статус пользователя
            conn.execute(
                "UPDATE users SET partner_id = ?, role = 'partner' WHERE telegram_id = ?",
                (partner_id, user_id)
            )
            
            conn.commit()
        
        # Очищаем временные данные
        if user_id in confirmation_codes:
            del confirmation_codes[user_id]
        
        await state.clear()
        
        await message.answer(
            f"🎉 <b>Регистрация партнера завершена!</b>\n\n"
            f"✅ Ваша заявка одобрена\n"
            f"🏢 Название: {partner_data.get('business_name', '')}\n"
            f"👤 Контакт: {partner_data.get('contact_name', '')}\n"
            f"📞 Телефон: {partner_data.get('contact_phone', '')}\n"
            f"📧 Email: {partner_data.get('contact_email', '')}\n\n"
            f"💡 <b>Что дальше:</b>\n"
            f"• Добавьте ваши заведения через кабинет партнера\n"
            f"• Настройте скидки и условия лояльности\n"
            f"• Получайте уведомления о новых заказах\n\n"
            f"🚀 Добро пожаловать в партнерскую программу!",
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in complete_partner_registration: {e}")
        await message.answer("❌ Ошибка при завершении регистрации.")

async def cancel_partner_registration(message: Message, state: FSMContext):
    """Отменить регистрацию партнера"""
    try:
        user_id = message.from_user.id
        
        # Очищаем временные данные
        if user_id in confirmation_codes:
            del confirmation_codes[user_id]
        
        await state.clear()
        
        from core.keyboards.reply_v2 import get_user_cabinet_keyboard
        
        await message.answer(
            "❌ Регистрация партнера отменена.\n\n"
            "💡 Вы можете начать регистрацию заново в любое время через кнопку '🤝 Стать партнером'",
            reply_markup=get_user_cabinet_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in cancel_partner_registration: {e}")
        await message.answer("❌ Ошибка при отмене регистрации.")

# Функция для администраторов для подтверждения кодов
async def confirm_partner_code(admin_id: int, user_id: int, code: str) -> bool:
    """Подтвердить код партнера (вызывается администратором)"""
    try:
        if user_id in confirmation_codes:
            stored_code = confirmation_codes[user_id]['code']
            if stored_code == code:
                confirmation_codes[user_id]['confirmed'] = True
                confirmation_codes[user_id]['confirmed_by'] = admin_id
                return True
        return False
    except Exception as e:
        logger.error(f"Error in confirm_partner_code: {e}")
        return False
