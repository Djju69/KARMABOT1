"""
FSM для редактирования настроек лояльности
Состояния и обработчики для управления параметрами системы лояльности
"""
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

class LoyaltySettingsStates(StatesGroup):
    """Состояния редактирования настроек лояльности"""
    waiting_for_setting_choice = State()  # Ожидание выбора настройки
    waiting_for_redeem_rate = State()     # Ожидание курса обмена
    waiting_for_min_purchase = State()    # Ожидание минимальной покупки
    waiting_for_max_discount = State()   # Ожидание максимальной скидки
    waiting_for_max_percent_bill = State() # Ожидание границы закрытия чека
    waiting_for_bonus_points_usage = State() # Ожидание дополнительной скидки при оплате баллами
    waiting_for_confirmation = State()   # Ожидание подтверждения

async def start_loyalty_settings_edit(message: Message, state: FSMContext):
    """Начать процесс редактирования настроек лояльности"""
    try:
        logger.info(f"🔧 Starting loyalty settings edit for user {message.from_user.id}")
        await state.set_state(LoyaltySettingsStates.waiting_for_setting_choice)
        await message.answer(
            "⚙️ <b>Редактирование настроек лояльности</b>\n\n"
            "🔧 <b>Выберите параметр для изменения:</b>\n\n"
            "1️⃣ <b>Курс обмена</b> - сколько VND стоит 1 балл\n"
            "2️⃣ <b>Минимальная покупка</b> - минимальная сумма для начисления баллов\n"
            "3️⃣ <b>Максимальная скидка</b> - максимальный процент скидки за баллы\n"
            "4️⃣ <b>Граница закрытия чека</b> - максимальный процент чека, который можно закрыть баллами\n"
            "5️⃣ <b>Дополнительная скидка</b> - дополнительный процент скидки при оплате баллами\n\n"
            "Введите номер параметра (1-5) или <b>ОТМЕНА</b> для выхода:",
            parse_mode='HTML'
        )
        logger.info(f"🔧 Loyalty settings edit menu sent to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error starting loyalty settings edit: {e}")
        await message.answer("❌ Ошибка при начале редактирования настроек.")

async def handle_setting_choice(message: Message, state: FSMContext):
    """Обработка выбора настройки"""
    try:
        choice = message.text.strip()
        logger.info(f"🔧 User {message.from_user.id} selected setting: {choice}")
        
        if choice.upper() in ["ОТМЕНА", "CANCEL", "НЕТ", "NO"]:
            await message.answer("❌ Редактирование настроек отменено.")
            await state.clear()
            return
        
        if choice == "1":
            await state.update_data(setting_type="redeem_rate")
            await state.set_state(LoyaltySettingsStates.waiting_for_redeem_rate)
            await message.answer(
                "💰 <b>Изменение курса обмена</b>\n\n"
                "Введите новый курс обмена (сколько VND стоит 1 балл):\n\n"
                "💡 <b>Примеры:</b>\n"
                "• 5000 - 1 балл = 5000 VND\n"
                "• 10000 - 1 балл = 10000 VND\n"
                "• 2500 - 1 балл = 2500 VND\n\n"
                "Введите число (минимум 1000, максимум 100000):",
                parse_mode='HTML'
            )
        elif choice == "2":
            await state.update_data(setting_type="min_purchase")
            await state.set_state(LoyaltySettingsStates.waiting_for_min_purchase)
            await message.answer(
                "🛒 <b>Изменение минимальной покупки</b>\n\n"
                "Введите минимальную сумму покупки для начисления баллов (в VND):\n\n"
                "💡 <b>Примеры:</b>\n"
                "• 10000 - покупки от 10,000 VND дают баллы\n"
                "• 50000 - покупки от 50,000 VND дают баллы\n"
                "• 0 - все покупки дают баллы\n\n"
                "Введите число (минимум 0, максимум 1000000):",
                parse_mode='HTML'
            )
        elif choice == "3":
            await state.update_data(setting_type="max_discount")
            await state.set_state(LoyaltySettingsStates.waiting_for_max_discount)
            await message.answer(
                "🎯 <b>Изменение максимальной скидки</b>\n\n"
                "Введите максимальный процент скидки за баллы:\n\n"
                "💡 <b>Примеры:</b>\n"
                "• 40 - максимальная скидка 40% от чека\n"
                "• 50 - максимальная скидка 50% от чека\n"
                "• 100 - можно закрыть весь чек баллами\n\n"
                "Введите число (минимум 1, максимум 100):",
                parse_mode='HTML'
            )
        elif choice == "4":
            await state.update_data(setting_type="max_percent_bill")
            await state.set_state(LoyaltySettingsStates.waiting_for_max_percent_bill)
            await message.answer(
                "📊 <b>Изменение границы закрытия чека</b>\n\n"
                "Введите максимальный процент чека, который можно закрыть баллами:\n\n"
                "💡 <b>Примеры:</b>\n"
                "• 50 - баллы могут закрыть до 50% от чека\n"
                "• 75 - баллы могут закрыть до 75% от чека\n"
                "• 100 - баллы могут закрыть весь чек\n\n"
                "Введите число (минимум 1, максимум 100):",
                parse_mode='HTML'
            )
        elif choice == "5":
            await state.update_data(setting_type="bonus_for_points_usage")
            await state.set_state(LoyaltySettingsStates.waiting_for_bonus_points_usage)
            await message.answer(
                "🎁 <b>Изменение дополнительной скидки при оплате баллами</b>\n\n"
                "Введите дополнительный процент скидки при оплате баллами:\n\n"
                "💡 <b>Примеры:</b>\n"
                "• 0.3 - дополнительная скидка 0.3% при оплате баллами\n"
                "• 0.5 - дополнительная скидка 0.5% при оплате баллами\n"
                "• 1.0 - дополнительная скидка 1.0% при оплате баллами\n\n"
                "Введите число (минимум 0.1, максимум 5.0):",
                parse_mode='HTML'
            )
        else:
            await message.answer("❌ Неверный выбор. Введите номер от 1 до 5 или <b>ОТМЕНА</b>:", parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Error handling setting choice: {e}")
        await message.answer("❌ Ошибка при обработке выбора настройки.")

async def handle_redeem_rate(message: Message, state: FSMContext):
    """Обработка курса обмена"""
    try:
        try:
            redeem_rate = float(message.text.strip())
            if redeem_rate < 1000 or redeem_rate > 100000:
                await message.answer("❌ Курс обмена должен быть от 1000 до 100000. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("❌ Неверный формат числа. Введите число (например: 5000):")
            return
        
        await state.update_data(new_value=redeem_rate)
        await show_confirmation(message, state, "курс обмена", f"{redeem_rate:,.0f} VND за 1 балл")
        
    except Exception as e:
        logger.error(f"Error handling redeem rate: {e}")
        await message.answer("❌ Ошибка при обработке курса обмена.")

async def handle_min_purchase(message: Message, state: FSMContext):
    """Обработка минимальной покупки"""
    try:
        try:
            min_purchase = int(message.text.strip())
            if min_purchase < 0 or min_purchase > 1000000:
                await message.answer("❌ Минимальная покупка должна быть от 0 до 1000000. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("❌ Неверный формат числа. Введите целое число (например: 10000):")
            return
        
        await state.update_data(new_value=min_purchase)
        await show_confirmation(message, state, "минимальную покупку", f"{min_purchase:,.0f} VND")
        
    except Exception as e:
        logger.error(f"Error handling min purchase: {e}")
        await message.answer("❌ Ошибка при обработке минимальной покупки.")

async def handle_max_discount(message: Message, state: FSMContext):
    """Обработка максимальной скидки"""
    try:
        try:
            max_discount = float(message.text.strip())
            if max_discount < 1 or max_discount > 100:
                await message.answer("❌ Максимальная скидка должна быть от 1 до 100. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("❌ Неверный формат числа. Введите число (например: 40):")
            return
        
        await state.update_data(new_value=max_discount)
        await show_confirmation(message, state, "максимальную скидку", f"{max_discount}%")
        
    except Exception as e:
        logger.error(f"Error handling max discount: {e}")
        await message.answer("❌ Ошибка при обработке максимальной скидки.")

async def handle_max_percent_bill(message: Message, state: FSMContext):
    """Обработка границы закрытия чека"""
    try:
        try:
            max_percent_bill = float(message.text.strip())
            if max_percent_bill < 1 or max_percent_bill > 100:
                await message.answer("❌ Граница закрытия чека должна быть от 1 до 100. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("❌ Неверный формат числа. Введите число (например: 50):")
            return
        
        await state.update_data(new_value=max_percent_bill)
        await show_confirmation(message, state, "границу закрытия чека", f"{max_percent_bill}%")
        
    except Exception as e:
        logger.error(f"Error handling max percent bill: {e}")
        await message.answer("❌ Ошибка при обработке границы закрытия чека.")

async def handle_bonus_points_usage(message: Message, state: FSMContext):
    """Обработка дополнительной скидки при оплате баллами"""
    try:
        try:
            bonus_points_usage = float(message.text.strip())
            if bonus_points_usage < 0.1 or bonus_points_usage > 5.0:
                await message.answer("❌ Дополнительная скидка должна быть от 0.1 до 5.0. Попробуйте снова:")
                return
        except ValueError:
            await message.answer("❌ Неверный формат числа. Введите число (например: 0.3):")
            return
        
        await state.update_data(new_value=bonus_points_usage)
        await show_confirmation(message, state, "дополнительную скидку при оплате баллами", f"{bonus_points_usage}%")
        
    except Exception as e:
        logger.error(f"Error handling bonus points usage: {e}")
        await message.answer("❌ Ошибка при обработке дополнительной скидки.")

async def show_confirmation(message: Message, state: FSMContext, setting_name: str, new_value: str):
    """Показать подтверждение изменения"""
    try:
        data = await state.get_data()
        setting_type = data['setting_type']
        
        # Получаем текущее значение
        current_value = await get_current_setting_value(setting_type)
        
        await state.set_state(LoyaltySettingsStates.waiting_for_confirmation)
        await message.answer(
            f"📋 <b>Подтверждение изменения</b>\n\n"
            f"⚙️ <b>Параметр:</b> {setting_name}\n"
            f"📊 <b>Текущее значение:</b> {current_value}\n"
            f"🆕 <b>Новое значение:</b> {new_value}\n\n"
            f"⚠️ <b>Внимание:</b> Изменение настроек лояльности повлияет на всех пользователей.\n\n"
            f"Отправьте <b>ПОДТВЕРДИТЬ</b> для сохранения или <b>ОТМЕНА</b> для отмены:",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error showing confirmation: {e}")
        await message.answer("❌ Ошибка при показе подтверждения.")

async def handle_confirmation(message: Message, state: FSMContext):
    """Обработка подтверждения изменения"""
    try:
        confirmation = message.text.strip().upper()
        
        if confirmation in ["ПОДТВЕРДИТЬ", "ДА", "YES", "OK", "SAVE"]:
            # Сохраняем изменение
            data = await state.get_data()
            success = await save_loyalty_setting(
                data['setting_type'],
                data['new_value'],
                message.from_user.id
            )
            
            if success:
                await message.answer(
                    f"✅ <b>Настройка успешно изменена!</b>\n\n"
                    f"⚙️ Изменение применено ко всей системе лояльности.\n"
                    f"📊 Новые параметры вступят в силу немедленно.",
                    parse_mode='HTML'
                )
            else:
                await message.answer(
                    "❌ Ошибка при сохранении настройки. Попробуйте позже.",
                    parse_mode='HTML'
                )
                
        elif confirmation in ["ОТМЕНА", "НЕТ", "NO", "CANCEL"]:
            await message.answer("❌ Изменение настройки отменено.")
        else:
            await message.answer("❌ Неверный ответ. Отправьте <b>ПОДТВЕРДИТЬ</b> для сохранения или <b>ОТМЕНА</b> для отмены:", parse_mode='HTML')
            return
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error handling confirmation: {e}")
        await message.answer("❌ Ошибка при обработке подтверждения.")

async def get_current_setting_value(setting_type: str) -> str:
    """Получить текущее значение настройки"""
    try:
        from core.database.db_adapter import db_v2
        
        query = """
            SELECT redeem_rate, min_purchase_for_points, max_discount_percent, max_percent_per_bill, bonus_for_points_usage
            FROM platform_loyalty_config 
            ORDER BY id DESC LIMIT 1
        """
        result = db_v2.fetch_one(query, ())
        
        if result:
            redeem_rate, min_purchase, max_discount, max_percent_bill, bonus_for_points_usage = result
            
            if setting_type == "redeem_rate":
                return f"{redeem_rate:,.0f} VND за 1 балл"
            elif setting_type == "min_purchase":
                return f"{min_purchase:,.0f} VND"
            elif setting_type == "max_discount":
                return f"{max_discount}%"
            elif setting_type == "max_percent_bill":
                return f"{max_percent_bill}%"
            elif setting_type == "bonus_for_points_usage":
                return f"{bonus_for_points_usage}%"
        
        return "Не установлено"
            
    except Exception as e:
        logger.error(f"Error getting current setting value: {e}")
        return "Ошибка загрузки"

async def save_loyalty_setting(setting_type: str, new_value: float, admin_id: int) -> bool:
    """Сохранить изменение настройки лояльности"""
    try:
        from core.database.db_adapter import db_v2
        
        # Обновляем настройку
        if setting_type == "redeem_rate":
            query = """
                UPDATE platform_loyalty_config 
                SET redeem_rate = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = (SELECT id FROM platform_loyalty_config ORDER BY id DESC LIMIT 1)
            """
            db_v2.execute(query, (new_value, admin_id))
        elif setting_type == "min_purchase":
            query = """
                UPDATE platform_loyalty_config 
                SET min_purchase_for_points = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = (SELECT id FROM platform_loyalty_config ORDER BY id DESC LIMIT 1)
            """
            db_v2.execute(query, (new_value, admin_id))
        elif setting_type == "max_discount":
            query = """
                UPDATE platform_loyalty_config 
                SET max_discount_percent = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = (SELECT id FROM platform_loyalty_config ORDER BY id DESC LIMIT 1)
            """
            db_v2.execute(query, (new_value, admin_id))
        elif setting_type == "max_percent_bill":
            query = """
                UPDATE platform_loyalty_config 
                SET max_percent_per_bill = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = (SELECT id FROM platform_loyalty_config ORDER BY id DESC LIMIT 1)
            """
            db_v2.execute(query, (new_value, admin_id))
        elif setting_type == "bonus_for_points_usage":
            query = """
                UPDATE platform_loyalty_config 
                SET bonus_for_points_usage = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = (SELECT id FROM platform_loyalty_config ORDER BY id DESC LIMIT 1)
            """
            db_v2.execute(query, (new_value, admin_id))
        
        # Логируем изменение
        log_query = """
            INSERT INTO admin_logs (admin_id, action, details, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """
        db_v2.execute(log_query, (
            admin_id,
            'loyalty_setting_changed',
            f"Setting: {setting_type}, New value: {new_value}"
        ))
        
        return True
            
    except Exception as e:
        logger.error(f"Error saving loyalty setting: {e}")
        return False
