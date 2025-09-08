"""
FSM для системы рассылок
Состояния и обработчики для процесса создания и отправки рассылок
"""
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

class BroadcastStates(StatesGroup):
    """Состояния системы рассылок"""
    waiting_for_message = State()      # Ожидание текста сообщения
    waiting_for_recipients = State()   # Ожидание выбора получателей
    waiting_for_confirmation = State() # Ожидание подтверждения

async def start_broadcast(message: Message, state: FSMContext):
    """Начать процесс создания рассылки"""
    try:
        await state.set_state(BroadcastStates.waiting_for_message)
        await message.answer(
            "📧 <b>Создание рассылки</b>\n\n"
            "📝 <b>Шаг 1 из 3:</b> Текст сообщения\n\n"
            "Введите текст сообщения для рассылки:\n\n"
            "💡 <b>Поддерживается:</b>\n"
            "• HTML разметка (жирный, курсив, ссылки)\n"
            "• Эмодзи и специальные символы\n"
            "• Максимум 4096 символов",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error starting broadcast: {e}")
        await message.answer("❌ Ошибка при начале создания рассылки.")

async def handle_message_text(message: Message, state: FSMContext):
    """Обработка текста сообщения"""
    try:
        message_text = message.text.strip()
        
        if len(message_text) < 10:
            await message.answer("❌ Текст сообщения должен содержать минимум 10 символов. Попробуйте снова:")
            return
        
        if len(message_text) > 4096:
            await message.answer("❌ Текст сообщения слишком длинный (максимум 4096 символов). Попробуйте снова:")
            return
        
        await state.update_data(message_text=message_text)
        await state.set_state(BroadcastStates.waiting_for_recipients)
        
        await message.answer(
            f"✅ <b>Текст сообщения сохранен</b>\n\n"
            f"📝 <b>Шаг 2 из 3:</b> Выбор получателей\n\n"
            f"Выберите группу получателей:\n\n"
            f"👥 <b>Все пользователи</b> - отправить всем зарегистрированным пользователям\n"
            f"🤝 <b>Партнеры</b> - отправить только партнерам\n"
            f"👑 <b>Админы</b> - отправить только администраторам\n"
            f"📱 <b>Активные пользователи</b> - отправить пользователям с активностью за последние 30 дней\n\n"
            f"Введите номер варианта (1-4):",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error handling message text: {e}")
        await message.answer("❌ Ошибка при обработке текста сообщения.")

async def handle_recipients_selection(message: Message, state: FSMContext):
    """Обработка выбора получателей"""
    try:
        choice = message.text.strip()
        
        recipient_types = {
            "1": "all_users",
            "2": "partners", 
            "3": "admins",
            "4": "active_users"
        }
        
        recipient_names = {
            "1": "всем пользователям",
            "2": "партнерам",
            "3": "администраторам", 
            "4": "активным пользователям"
        }
        
        if choice not in recipient_types:
            await message.answer("❌ Неверный выбор. Введите номер от 1 до 4:")
            return
        
        recipient_type = recipient_types[choice]
        recipient_name = recipient_names[choice]
        
        # Получаем количество получателей
        recipient_count = await get_recipient_count(recipient_type)
        
        await state.update_data(recipient_type=recipient_type, recipient_name=recipient_name)
        await state.set_state(BroadcastStates.waiting_for_confirmation)
        
        data = await state.get_data()
        
        await message.answer(
            f"📋 <b>Подтверждение рассылки</b>\n\n"
            f"📝 <b>Шаг 3 из 3:</b> Подтверждение\n\n"
            f"📧 <b>Текст сообщения:</b>\n{data['message_text'][:200]}{'...' if len(data['message_text']) > 200 else ''}\n\n"
            f"👥 <b>Получатели:</b> {recipient_name} ({recipient_count} человек)\n\n"
            f"⚠️ <b>Внимание:</b> Рассылка будет отправлена немедленно и не может быть отменена.\n\n"
            f"Отправьте <b>ПОДТВЕРДИТЬ</b> для отправки или <b>ОТМЕНА</b> для отмены:",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error handling recipients selection: {e}")
        await message.answer("❌ Ошибка при выборе получателей.")

async def handle_confirmation(message: Message, state: FSMContext):
    """Обработка подтверждения рассылки"""
    try:
        confirmation = message.text.strip().upper()
        
        if confirmation in ["ПОДТВЕРДИТЬ", "ДА", "YES", "OK", "SEND"]:
            # Отправляем рассылку
            data = await state.get_data()
            success_count, error_count = await send_broadcast(
                message.from_user.id,
                data['message_text'],
                data['recipient_type']
            )
            
            await message.answer(
                f"✅ <b>Рассылка отправлена!</b>\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"• ✅ Успешно отправлено: {success_count}\n"
                f"• ❌ Ошибок: {error_count}\n"
                f"• 👥 Получатели: {data['recipient_name']}\n\n"
                f"📧 Рассылка завершена.",
                parse_mode='HTML'
            )
            
        elif confirmation in ["ОТМЕНА", "НЕТ", "NO", "CANCEL"]:
            await message.answer("❌ Рассылка отменена.")
        else:
            await message.answer("❌ Неверный ответ. Отправьте <b>ПОДТВЕРДИТЬ</b> для отправки или <b>ОТМЕНА</b> для отмены:", parse_mode='HTML')
            return
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error handling confirmation: {e}")
        await message.answer("❌ Ошибка при обработке подтверждения.")

async def get_recipient_count(recipient_type: str) -> int:
    """Получить количество получателей по типу"""
    try:
        from core.database.db_v2 import get_connection
        
        with get_connection() as conn:
            if recipient_type == "all_users":
                cursor = conn.execute("SELECT COUNT(*) FROM users")
            elif recipient_type == "partners":
                cursor = conn.execute("SELECT COUNT(*) FROM partners WHERE status = 'active'")
            elif recipient_type == "admins":
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'super_admin')")
            elif recipient_type == "active_users":
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE last_activity > NOW() - INTERVAL '30 days'
                """)
            else:
                return 0
            
            result = cursor.fetchone()
            return result[0] if result else 0
            
    except Exception as e:
        logger.error(f"Error getting recipient count: {e}")
        return 0

async def send_broadcast(sender_id: int, message_text: str, recipient_type: str) -> tuple[int, int]:
    """Отправить рассылку"""
    try:
        from core.database.db_v2 import get_connection
        from aiogram import Bot
        from core.settings import BOT_TOKEN
        
        bot = Bot(token=BOT_TOKEN)
        success_count = 0
        error_count = 0
        
        with get_connection() as conn:
            # Получаем список получателей
            if recipient_type == "all_users":
                cursor = conn.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
            elif recipient_type == "partners":
                cursor = conn.execute("""
                    SELECT DISTINCT u.telegram_id FROM users u 
                    JOIN partners p ON u.partner_id = p.id 
                    WHERE p.status = 'active' AND u.telegram_id IS NOT NULL
                """)
            elif recipient_type == "admins":
                cursor = conn.execute("""
                    SELECT telegram_id FROM users 
                    WHERE role IN ('admin', 'super_admin') AND telegram_id IS NOT NULL
                """)
            elif recipient_type == "active_users":
                cursor = conn.execute("""
                    SELECT telegram_id FROM users 
                    WHERE last_activity > NOW() - INTERVAL '30 days' 
                    AND telegram_id IS NOT NULL
                """)
            else:
                return 0, 0
            
            recipients = cursor.fetchall()
            
            # Отправляем сообщения
            for recipient in recipients:
                try:
                    await bot.send_message(
                        chat_id=recipient[0],
                        text=message_text,
                        parse_mode='HTML'
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error sending to {recipient[0]}: {e}")
                    error_count += 1
            
            # Логируем рассылку
            conn.execute("""
                INSERT INTO admin_logs (admin_id, action, details, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (
                sender_id,
                'broadcast_sent',
                f"Recipients: {recipient_type}, Success: {success_count}, Errors: {error_count}"
            ))
            conn.commit()
            
        return success_count, error_count
        
    except Exception as e:
        logger.error(f"Error sending broadcast: {e}")
        return 0, 1
