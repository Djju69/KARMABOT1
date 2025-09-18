"""
FSM для регистрации партнеров
Состояния и обработчики для процесса регистрации партнера
"""
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import F
import logging

logger = logging.getLogger(__name__)

class PartnerRegistrationStates(StatesGroup):
    """Состояния регистрации партнера"""
    waiting_for_business_name = State()  # Ожидание названия бизнеса
    waiting_for_contact_name = State()   # Ожидание имени контакта
    waiting_for_contact_phone = State() # Ожидание телефона
    waiting_for_contact_email = State() # Ожидание email
    waiting_for_legal_info = State()    # Ожидание юридической информации
    waiting_for_confirmation = State()   # Ожидание подтверждения

async def start_partner_registration(message: Message, state: FSMContext):
    """Начать процесс регистрации партнера"""
    try:
        await state.set_state(PartnerRegistrationStates.waiting_for_business_name)
        await message.answer(
            "🤝 <b>Регистрация партнера</b>\n\n"
            "Добро пожаловать в нашу партнерскую программу!\n\n"
            "📝 <b>Шаг 1 из 6:</b> Название бизнеса\n\n"
            "Пожалуйста, введите название вашего бизнеса или организации:",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error starting partner registration: {e}")
        await message.answer("❌ Ошибка при начале регистрации. Попробуйте позже.")

async def handle_business_name(message: Message, state: FSMContext):
    """Обработка названия бизнеса"""
    try:
        business_name = message.text.strip()
        if len(business_name) < 2:
            await message.answer("❌ Название бизнеса должно содержать минимум 2 символа. Попробуйте снова:")
            return
        
        await state.update_data(business_name=business_name)
        await state.set_state(PartnerRegistrationStates.waiting_for_contact_name)
        
        await message.answer(
            f"✅ Название бизнеса: <b>{business_name}</b>\n\n"
            "📝 <b>Шаг 2 из 6:</b> Контактное лицо\n\n"
            "Введите имя и фамилию контактного лица:",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error handling business name: {e}")
        await message.answer("❌ Ошибка при обработке названия бизнеса. Попробуйте снова:")

async def handle_contact_name(message: Message, state: FSMContext):
    """Обработка имени контакта"""
    try:
        contact_name = message.text.strip()
        if len(contact_name) < 2:
            await message.answer("❌ Имя контакта должно содержать минимум 2 символа. Попробуйте снова:")
            return
        
        await state.update_data(contact_name=contact_name)
        await state.set_state(PartnerRegistrationStates.waiting_for_contact_phone)
        
        await message.answer(
            f"✅ Контактное лицо: <b>{contact_name}</b>\n\n"
            "📝 <b>Шаг 3 из 6:</b> Телефон\n\n"
            "Введите номер телефона для связи (например: +7 999 123 45 67):",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error handling contact name: {e}")
        await message.answer("❌ Ошибка при обработке имени контакта. Попробуйте снова:")

async def handle_contact_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    try:
        phone = message.text.strip()
        # Простая валидация телефона
        if len(phone) < 10:
            await message.answer("❌ Номер телефона слишком короткий. Попробуйте снова:")
            return
        
        await state.update_data(contact_phone=phone)
        await state.set_state(PartnerRegistrationStates.waiting_for_contact_email)
        
        await message.answer(
            f"✅ Телефон: <b>{phone}</b>\n\n"
            "📝 <b>Шаг 4 из 6:</b> Email\n\n"
            "Введите email адрес (например: contact@company.com):",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error handling contact phone: {e}")
        await message.answer("❌ Ошибка при обработке телефона. Попробуйте снова:")

async def handle_contact_email(message: Message, state: FSMContext):
    """Обработка email"""
    try:
        email = message.text.strip()
        # Простая валидация email
        if "@" not in email or "." not in email:
            await message.answer("❌ Неверный формат email. Попробуйте снова:")
            return
        
        await state.update_data(contact_email=email)
        await state.set_state(PartnerRegistrationStates.waiting_for_legal_info)
        
        await message.answer(
            f"✅ Email: <b>{email}</b>\n\n"
            "📝 <b>Шаг 5 из 6:</b> Юридическая информация\n\n"
            "Введите юридическую информацию (название организации, ИНН, адрес и т.д.):",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error handling contact email: {e}")
        await message.answer("❌ Ошибка при обработке email. Попробуйте снова:")

async def handle_legal_info(message: Message, state: FSMContext):
    """Обработка юридической информации"""
    try:
        legal_info = message.text.strip()
        if len(legal_info) < 10:
            await message.answer("❌ Юридическая информация должна содержать минимум 10 символов. Попробуйте снова:")
            return
        
        await state.update_data(legal_info=legal_info)
        await state.set_state(PartnerRegistrationStates.waiting_for_confirmation)
        
        # Получаем все данные для подтверждения
        data = await state.get_data()
        
        await message.answer(
            f"📋 <b>Подтверждение данных партнера</b>\n\n"
            f"🏢 <b>Название бизнеса:</b> {data['business_name']}\n"
            f"👤 <b>Контактное лицо:</b> {data['contact_name']}\n"
            f"📞 <b>Телефон:</b> {data['contact_phone']}\n"
            f"📧 <b>Email:</b> {data['contact_email']}\n"
            f"📄 <b>Юридическая информация:</b> {data['legal_info']}\n\n"
            "📝 <b>Шаг 6 из 6:</b> Подтверждение\n\n"
            "Все данные корректны? Отправьте <b>ДА</b> для подтверждения или <b>НЕТ</b> для отмены:",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error handling legal info: {e}")
        await message.answer("❌ Ошибка при обработке юридической информации. Попробуйте снова:")

async def handle_confirmation(message: Message, state: FSMContext):
    """Обработка подтверждения"""
    try:
        confirmation = message.text.strip().upper()
        
        if confirmation in ["ДА", "YES", "Y", "OK", "ПОДТВЕРЖДАЮ"]:
            # Сохраняем данные партнера
            data = await state.get_data()
            success = await save_partner_data(message.from_user.id, data)
            
            if success:
                await message.answer(
                    "✅ <b>Заявка на партнерство отправлена!</b>\n\n"
                    "📋 Ваша заявка будет рассмотрена администратором в течение 24 часов.\n"
                    "📧 Мы свяжемся с вами по указанному email для дальнейших шагов.\n\n"
                    "🤝 Спасибо за интерес к нашей партнерской программе!",
                    parse_mode='HTML'
                )
            else:
                await message.answer(
                    "❌ Ошибка при сохранении заявки. Попробуйте позже или обратитесь в поддержку.",
                    parse_mode='HTML'
                )
        elif confirmation in ["НЕТ", "NO", "N", "ОТМЕНА", "CANCEL"]:
            await message.answer(
                "❌ Регистрация партнера отменена.",
                parse_mode='HTML'
            )
        else:
            await message.answer(
                "❌ Неверный ответ. Отправьте <b>ДА</b> для подтверждения или <b>НЕТ</b> для отмены:",
                parse_mode='HTML'
            )
            return
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error handling confirmation: {e}")
        await message.answer("❌ Ошибка при обработке подтверждения. Попробуйте снова:")

async def save_partner_data(user_id: int, data: dict) -> bool:
    """Сохранение данных партнера в базу данных"""
    try:
        from core.database.db_v2 import get_connection
        from datetime import datetime
        
        with get_connection() as conn:
            # Генерируем уникальный код партнера
            partner_code = f"PARTNER_{user_id}_{int(datetime.now().timestamp())}"
            
            conn.execute("""
                INSERT INTO partners (
                    code, title, status, contact_name, contact_telegram, 
                    contact_phone, contact_email, legal_info, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                partner_code,
                data['business_name'],
                'pending',
                data['contact_name'],
                user_id,
                data['contact_phone'],
                data['contact_email'],
                data['legal_info'],
                datetime.now().isoformat()
            ))
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error saving partner data: {e}")
        return False
