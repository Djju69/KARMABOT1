"""
Обработчики для личного кабинета пользователя
"""
import logging
from typing import Dict, Any, List
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.services.user_profile_service import user_profile_service
from core.services.loyalty_service import loyalty_service
from core.utils.locales import get_text
from core.keyboards.restaurant_keyboards import select_restoran
from core.logger import get_logger

logger = get_logger(__name__)
router = Router(name="user_profile_handlers")

@router.message(F.text == "👤 Личный кабинет")
async def show_user_profile(message: Message, state: FSMContext):
    """Показ личного кабинета пользователя"""
    try:
        user_id = message.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем полный профиль пользователя
        profile = await user_profile_service.get_user_profile(user_id)
        
        # Формируем текст профиля
        text = get_text(lang, "user_profile_title") or "👤 Личный кабинет"
        text += f"\n\n👋 Привет, {profile['display_name']}!"
        
        # Уровень и прогресс
        level_emoji = {
            "bronze": "🥉",
            "silver": "🥈", 
            "gold": "🥇",
            "platinum": "💎"
        }
        
        level_emoji_current = level_emoji.get(profile['level'], "🥉")
        text += f"\n\n{level_emoji_current} Уровень: {profile['level'].title()}"
        text += f"\n📊 Очки: {profile['level_points']}"
        text += f"\n📈 Прогресс: {profile['level_progress']:.1f}%"
        
        if profile['next_level']:
            text += f"\n🎯 До {profile['next_level'].title()}: {profile['level_points']} очков"
        
        # Статистика
        text += f"\n\n📊 Статистика:"
        text += f"\n• Посещений: {profile['total_visits']}"
        text += f"\n• Отзывов: {profile['total_reviews']}"
        text += f"\n• QR сканирований: {profile['total_qr_scans']}"
        text += f"\n• Покупок: {profile['total_purchases']}"
        text += f"\n• Потрачено: {profile['total_spent']:.2f} руб."
        
        # Реферальная статистика
        text += f"\n\n👥 Рефералы:"
        text += f"\n• Приглашено: {profile['total_referrals']}"
        text += f"\n• Заработано: {profile['referral_earnings']:.2f} руб."
        
        # Баланс лояльности
        text += f"\n\n💰 Баланс лояльности:"
        text += f"\n• Баллы: {profile['loyalty_points']}"
        text += f"\n• Рублей: {profile['loyalty_balance']:.2f}"
        
        # Преимущества уровня
        benefits = profile['level_benefits']
        text += f"\n\n🎁 Преимущества уровня:"
        text += f"\n• Скидка: {benefits['discount']*100:.0f}%"
        text += f"\n• Множитель очков: {benefits['points_multiplier']}x"
        
        # Клавиатура
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "profile_settings") or "⚙️ Настройки",
                    callback_data="profile_settings"
                ),
                InlineKeyboardButton(
                    text=get_text(lang, "profile_statistics") or "📊 Статистика",
                    callback_data="profile_statistics"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "profile_achievements") or "🏆 Достижения",
                    callback_data="profile_achievements"
                ),
                InlineKeyboardButton(
                    text=get_text(lang, "profile_qr_codes") or "📱 QR-коды",
                    callback_data="profile_qr_codes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_main") or "◀️ Главное меню",
                    callback_data="back_to_main"
                )
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка показа личного кабинета: {e}")
        await message.answer("❌ Ошибка загрузки личного кабинета")

@router.callback_query(F.data == "profile_settings")
async def show_profile_settings(callback: CallbackQuery, state: FSMContext):
    """Показ настроек профиля"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем профиль
        profile = await user_profile_service.get_user_profile(user_id)
        
        text = get_text(lang, "profile_settings_title") or "⚙️ Настройки профиля"
        text += f"\n\n👤 Основная информация:"
        text += f"\n• Имя: {profile['full_name'] or 'Не указано'}"
        text += f"\n• Username: @{profile['username'] or 'Не указан'}"
        text += f"\n• Телефон: {profile['phone'] or 'Не указан'}"
        text += f"\n• Email: {profile['email'] or 'Не указан'}"
        
        text += f"\n\n🔔 Уведомления:"
        text += f"\n• Общие: {'✅' if profile['notifications_enabled'] else '❌'}"
        text += f"\n• Email: {'✅' if profile['email_notifications'] else '❌'}"
        text += f"\n• Push: {'✅' if profile['push_notifications'] else '❌'}"
        
        text += f"\n\n🌐 Язык и регион:"
        text += f"\n• Язык: {profile['language'].upper()}"
        text += f"\n• Часовой пояс: {profile['timezone']}"
        
        text += f"\n\n🔒 Приватность:"
        text += f"\n• Уровень: {profile['privacy_level']}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "edit_profile") or "✏️ Редактировать",
                    callback_data="edit_profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "notification_settings") or "🔔 Уведомления",
                    callback_data="notification_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_profile") or "◀️ К профилю",
                    callback_data="back_to_profile"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа настроек профиля: {e}")
        await callback.answer("❌ Ошибка загрузки настроек")

@router.callback_query(F.data == "profile_statistics")
async def show_profile_statistics(callback: CallbackQuery, state: FSMContext):
    """Показ детальной статистики профиля"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем статистику за 30 дней
        stats = await user_profile_service.get_user_statistics(user_id, days=30)
        
        text = get_text(lang, "profile_statistics_title") or "📊 Статистика профиля"
        text += f"\n\n📅 За последние {stats['period_days']} дней:"
        
        # Статистика активности
        if stats['activity_stats']:
            text += f"\n\n🎯 Активность:"
            for activity in stats['activity_stats']:
                text += f"\n• {activity['type']}: {activity['count']} раз"
                if activity['points'] > 0:
                    text += f" (+{activity['points']} очков)"
        
        # Статистика транзакций
        if stats['transaction_stats']:
            text += f"\n\n💰 Транзакции:"
            for transaction in stats['transaction_stats']:
                text += f"\n• {transaction['type']}: {transaction['count']} раз"
                if transaction['points'] > 0:
                    text += f" ({transaction['points']} очков)"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_profile") or "◀️ К профилю",
                    callback_data="back_to_profile"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа статистики профиля: {e}")
        await callback.answer("❌ Ошибка загрузки статистики")

@router.callback_query(F.data == "profile_achievements")
async def show_profile_achievements(callback: CallbackQuery, state: FSMContext):
    """Показ достижений пользователя"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем профиль с достижениями
        profile = await user_profile_service.get_user_profile(user_id)
        
        text = get_text(lang, "profile_achievements_title") or "🏆 Достижения"
        
        if profile['recent_achievements']:
            text += f"\n\n🎖️ Последние достижения:"
            for achievement in profile['recent_achievements']:
                text += f"\n\n🏅 {achievement['name']}"
                if achievement['description']:
                    text += f"\n   {achievement['description']}"
                if achievement['points'] > 0:
                    text += f"\n   💰 +{achievement['points']} очков"
        else:
            text += f"\n\n📭 Пока нет достижений"
            text += f"\n\n💡 Выполняйте задания и получайте награды!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_profile") or "◀️ К профилю",
                    callback_data="back_to_profile"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа достижений: {e}")
        await callback.answer("❌ Ошибка загрузки достижений")

@router.callback_query(F.data == "profile_qr_codes")
async def show_profile_qr_codes(callback: CallbackQuery, state: FSMContext):
    """Показ QR-кодов пользователя"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем профиль
        profile = await user_profile_service.get_user_profile(user_id)
        
        text = get_text(lang, "profile_qr_codes_title") or "📱 QR-коды и скидки"
        text += f"\n\n📊 Статистика QR-кодов:"
        text += f"\n• Всего сканирований: {profile['total_qr_scans']}"
        
        # Показываем доступные скидки по уровню
        benefits = profile['level_benefits']
        text += f"\n\n🎫 Доступные скидки:"
        text += f"\n• Скидка уровня: {benefits['discount']*100:.0f}%"
        text += f"\n• Множитель очков: {benefits['points_multiplier']}x"
        
        text += f"\n\n💡 Как использовать:"
        text += f"\n1. Найдите QR-код в заведении"
        text += f"\n2. Отсканируйте через бота"
        text += f"\n3. Получите скидку и очки!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "scan_qr_code") or "📱 Сканировать QR",
                    callback_data="scan_qr_code"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_profile") or "◀️ К профилю",
                    callback_data="back_to_profile"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа QR-кодов: {e}")
        await callback.answer("❌ Ошибка загрузки QR-кодов")

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    """Возврат к профилю"""
    await show_user_profile(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "scan_qr_code")
async def scan_qr_code(callback: CallbackQuery, state: FSMContext):
    """Обработка сканирования QR-кода"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем профиль для показа уровня и преимуществ
        profile = await user_profile_service.get_user_profile(user_id)
        
        text = get_text(lang, "qr_scan_instruction") or "📱 Сканирование QR-кода"
        text += f"\n\n👤 Ваш уровень: {profile['level'].title()}"
        text += f"\n🎫 Ваша скидка: {profile['level_benefits']['discount']*100:.0f}%"
        text += f"\n⭐ Множитель очков: {profile['level_benefits']['points_multiplier']}x"
        
        text += f"\n\n📋 Как использовать:"
        text += f"\n1. Нажмите 'Открыть WebApp'"
        text += f"\n2. Наведите камеру на QR-код"
        text += f"\n3. Получите скидку и очки!"
        
        text += f"\n\n⚠️ Внимание:"
        text += f"\n• QR-код должен быть от партнера KARMABOT1"
        text += f"\n• Один QR-код можно использовать только один раз"
        text += f"\n• Скидка применяется автоматически"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "open_webapp") or "🌐 Открыть WebApp",
                    web_app={"url": f"https://your-domain.com/api/qr/scanner"}
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "generate_qr") or "🎫 Создать QR",
                    callback_data="generate_qr_code"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_qr_codes") or "◀️ К QR-кодам",
                    callback_data="profile_qr_codes"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа инструкции QR: {e}")
        await callback.answer("❌ Ошибка загрузки инструкции")

@router.callback_query(F.data == "generate_qr_code")
async def generate_qr_code(callback: CallbackQuery, state: FSMContext):
    """Генерация QR-кода для пользователя"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем профиль
        profile = await user_profile_service.get_user_profile(user_id)
        
        text = get_text(lang, "generate_qr_title") or "🎫 Создание QR-кода"
        text += f"\n\n👤 Ваш уровень: {profile['level'].title()}"
        text += f"\n🎁 Преимущества уровня:"
        text += f"\n• Скидка: {profile['level_benefits']['discount']*100:.0f}%"
        text += f"\n• Множитель очков: {profile['level_benefits']['points_multiplier']}x"
        
        text += f"\n\n💡 Выберите тип скидки:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 100 очков лояльности",
                    callback_data="qr_type_loyalty_points_100"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 200 очков лояльности",
                    callback_data="qr_type_loyalty_points_200"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 5% скидка",
                    callback_data="qr_type_percentage_5"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 10% скидка",
                    callback_data="qr_type_percentage_10"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_qr_codes") or "◀️ К QR-кодам",
                    callback_data="profile_qr_codes"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка генерации QR-кода: {e}")
        await callback.answer("❌ Ошибка создания QR-кода")

@router.callback_query(F.data.startswith("qr_type_"))
async def process_qr_type_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа QR-кода"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Парсим тип и значение из callback_data
        data_parts = callback.data.split("_")
        discount_type = data_parts[2] + "_" + data_parts[3]  # loyalty_points или percentage
        discount_value = int(data_parts[4])
        
        # Получаем профиль для применения множителя уровня
        profile = await user_profile_service.get_user_profile(user_id)
        level_multiplier = profile['level_benefits']['points_multiplier']
        final_value = int(discount_value * level_multiplier)
        
        # Создаем QR-код через WebApp API
        from core.services.qr_code_service import QRCodeService
        from core.database import get_db
        
        async with get_db() as db:
            qr_service = QRCodeService(db)
            
            qr_result = await qr_service.generate_qr_code(
                user_id=user_id,
                discount_type=discount_type,
                discount_value=final_value,
                expires_in_hours=24,
                description=f"Скидка {final_value} {'очков' if discount_type == 'loyalty_points' else '%'}"
            )
        
        # Логируем активность
        await user_profile_service.log_user_activity(
            user_id=user_id,
            activity_type="qr_generate",
            points_earned=5,
            activity_data={"qr_id": qr_result["qr_id"], "discount_type": discount_type}
        )
        
        text = get_text(lang, "qr_generated_success") or "✅ QR-код создан успешно!"
        text += f"\n\n🎫 Тип: {discount_type.replace('_', ' ').title()}"
        text += f"\n💰 Значение: {final_value}"
        text += f"\n⭐ С учетом уровня: {level_multiplier}x"
        text += f"\n⏰ Действителен: 24 часа"
        text += f"\n\n📱 ID QR-кода: `{qr_result['qr_id']}`"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_qr_codes") or "◀️ К QR-кодам",
                    callback_data="profile_qr_codes"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки выбора QR-типа: {e}")
        await callback.answer("❌ Ошибка создания QR-кода")
