"""
Обработчики для управления языками
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.services.translation_service import translation_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["🌐 Язык", "🌐 Language", "🌐 Ngôn Ngữ", "🌐 언어"]))
async def handle_language_selection(message: Message):
    """Показать выбор языка"""
    try:
        user_id = message.from_user.id
        current_lang = translation_service.get_user_language(user_id)
        
        # Создаем клавиатуру с языками
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for lang_code, lang_info in translation_service.get_supported_languages().items():
            flag = lang_info['flag']
            name = lang_info['name']
            
            # Отмечаем текущий язык
            if lang_code == current_lang:
                text = f"{flag} {name} ✅"
            else:
                text = f"{flag} {name}"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"lang_{lang_code}"
                )
            ])
        
        # Добавляем кнопку "Назад"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=translation_service.get_text("back", current_lang),
                callback_data="back_to_menu"
            )
        ])
        
        response_text = translation_service.get_text(
            "language_selection",
            current_lang,
            current_language=translation_service.get_language_name(current_lang)
        )
        
        await message.answer(response_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in handle_language_selection: {e}")
        await message.answer("❌ Ошибка при выборе языка")

@router.callback_query(F.data.startswith("lang_"))
async def handle_language_change(callback: CallbackQuery):
    """Обработать смену языка"""
    try:
        user_id = callback.from_user.id
        lang_code = callback.data.split("_")[1]
        
        # Проверяем, поддерживается ли язык
        if not translation_service.is_language_supported(lang_code):
            await callback.answer("❌ Язык не поддерживается")
            return
        
        # Устанавливаем новый язык
        success = translation_service.set_user_language(user_id, lang_code)
        
        if success:
            # Отвечаем на callback
            await callback.answer(
                translation_service.get_text("language_changed", lang_code),
                show_alert=True
            )
            
            # Обновляем сообщение
            await callback.message.edit_text(
                translation_service.get_text("language_selection", lang_code),
                reply_markup=callback.message.reply_markup
            )
            
            logger.info(f"User {user_id} changed language to {lang_code}")
        else:
            await callback.answer("❌ Ошибка при смене языка")
            
    except Exception as e:
        logger.error(f"Error in handle_language_change: {e}")
        await callback.answer("❌ Ошибка при смене языка")

@router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    try:
        user_id = callback.from_user.id
        current_lang = translation_service.get_user_language(user_id)
        
        # Импортируем главное меню
        from core.keyboards.reply_v2 import get_main_menu_keyboard
        
        keyboard = get_main_menu_keyboard()
        
        welcome_text = translation_service.get_text(
            "welcome_back",
            current_lang,
            user_name=callback.from_user.first_name or "Пользователь"
        )
        
        await callback.message.edit_text(welcome_text)
        await callback.message.answer(
            translation_service.get_text("main_menu", current_lang),
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in handle_back_to_menu: {e}")
        await callback.answer("❌ Ошибка")

@router.message(F.text.in_(["🌐 Настройки языка", "🌐 Language Settings", "🌐 Cài Đặt Ngôn Ngữ", "🌐 언어 설정"]))
async def handle_language_settings(message: Message):
    """Показать настройки языка для админов"""
    try:
        user_id = message.from_user.id
        current_lang = translation_service.get_user_language(user_id)
        
        # Проверяем права админа
        from core.services.user_service import user_service
        user_role = await user_service.get_user_role(user_id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer(
                translation_service.get_text("access_denied", current_lang)
            )
            return
        
        # Получаем статистику переводов
        stats = translation_service.get_translation_stats()
        
        response = translation_service.get_text("language_settings_title", current_lang) + "\n\n"
        
        for lang_code, stat in stats.items():
            lang_name = translation_service.get_language_name(lang_code)
            response += f"{lang_name}:\n"
            response += f"  📊 Переводов: {stat['translated_keys']}/{stat['total_keys']}\n"
            response += f"  📈 Покрытие: {stat['coverage_percent']:.1f}%\n\n"
        
        # Добавляем кнопки управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=translation_service.get_text("refresh_stats", current_lang),
                    callback_data="refresh_language_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text=translation_service.get_text("back", current_lang),
                    callback_data="back_to_admin_menu"
                )
            ]
        ])
        
        await message.answer(response, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in handle_language_settings: {e}")
        await message.answer("❌ Ошибка при загрузке настроек языка")

@router.callback_query(F.data == "refresh_language_stats")
async def handle_refresh_language_stats(callback: CallbackQuery):
    """Обновить статистику переводов"""
    try:
        user_id = callback.from_user.id
        current_lang = translation_service.get_user_language(user_id)
        
        # Перезагружаем переводы
        translation_service._load_translations()
        
        # Получаем обновленную статистику
        stats = translation_service.get_translation_stats()
        
        response = translation_service.get_text("language_settings_title", current_lang) + "\n\n"
        
        for lang_code, stat in stats.items():
            lang_name = translation_service.get_language_name(lang_code)
            response += f"{lang_name}:\n"
            response += f"  📊 Переводов: {stat['translated_keys']}/{stat['total_keys']}\n"
            response += f"  📈 Покрытие: {stat['coverage_percent']:.1f}%\n\n"
        
        await callback.message.edit_text(response, reply_markup=callback.message.reply_markup)
        await callback.answer(translation_service.get_text("stats_refreshed", current_lang))
        
    except Exception as e:
        logger.error(f"Error in handle_refresh_language_stats: {e}")
        await callback.answer("❌ Ошибка при обновлении статистики")
