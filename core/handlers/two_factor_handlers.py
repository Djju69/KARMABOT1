"""
Обработчики для работы с двухфакторной аутентификацией.
"""
import logging
from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from core.security import two_factor_auth, require_permission, get_user_role
from core.security.roles import Permission, Role
from core.database import role_repository

logger = logging.getLogger(__name__)
router = Router()

class TwoFactorStates(StatesGroup):
    """Состояния для настройки 2FA."""
    waiting_for_enable_confirmation = State()
    waiting_for_code = State()

@router.message(Command("2fa"))
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def cmd_2fa_settings(message: types.Message, state: FSMContext):
    """Обработчик команды настройки 2FA."""
    user_id = message.from_user.id
    
    # Проверяем, включена ли уже 2FA
    is_enabled = await two_factor_auth.is_2fa_enabled(user_id)
    
    if is_enabled:
        # Если 2FA уже включена, предлагаем отключить
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отключить 2FA", callback_data="2fa_disable")],
            [types.InlineKeyboardButton(text="🔄 Сгенерировать новый ключ", callback_data="2fa_reset")]
        ])
        await message.answer(
            "🔐 Двухфакторная аутентификация включена.\n\n"
            "Вы можете отключить её или сгенерировать новый ключ.",
            reply_markup=keyboard
        )
    else:
        # Если 2FA отключена, предлагаем включить
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Включить 2FA", callback_data="2fa_enable")]
        ])
        await message.answer(
            "🔓 Двухфакторная аутентификация отключена.\n\n"
            "Рекомендуем включить её для дополнительной безопасности.",
            reply_markup=keyboard
        )

@router.callback_query(F.data == "2fa_enable")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def enable_2fa_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса включения 2FA."""
    user_id = callback.from_user.id
    
    # Генерируем новый секретный ключ
    secret_key = two_factor_auth.generate_secret_key()
    
    # Сохраняем ключ в состоянии
    await state.update_data(secret_key=secret_key)
    
    # Генерируем URI для настройки в приложении аутентификаторе
    uri = two_factor_auth.get_totp_uri(callback.from_user.username or str(user_id), secret_key)
    
    # Генерируем QR-код
    qr_code = two_factor_auth.generate_qr_code(uri)
    
    # Отправляем QR-код и инструкции
    await callback.message.answer_photo(
        types.BufferedInputFile(qr_code, filename="2fa_qr.png"),
        caption="🔐 Настройте двухфакторную аутентификацию\n\n"
               "1. Откройте приложение аутентификатора (Google Authenticator, Microsoft Authenticator и т.д.)\n"
               "2. Отсканируйте QR-код или введите ключ вручную:\n"
               f"<code>{secret_key}</code>\n\n"
               "3. Введите 6-значный код из приложения",
        parse_mode="HTML"
    )
    
    # Переходим в состояние ожидания кода
    await state.set_state(TwoFactorStates.waiting_for_code)
    await callback.answer()

@router.message(TwoFactorStates.waiting_for_code, F.text.isdigit())
async def process_2fa_code(message: types.Message, state: FSMContext):
    """Обработка введенного кода подтверждения 2FA."""
    user_id = message.from_user.id
    code = message.text.strip()
    
    # Получаем сохраненный секретный ключ
    state_data = await state.get_data()
    secret_key = state_data.get('secret_key')
    
    if not secret_key:
        await message.answer("❌ Ошибка: не найден секретный ключ. Пожалуйста, начните процесс заново.")
        await state.clear()
        return
    
    # Проверяем код
    if await two_factor_auth.verify_code(user_id, code):
        # Код верный, сохраняем настройки
        await two_factor_auth.enable_2fa(user_id, secret_key)
        
        # Обновляем состояние пользователя
        await state.update_data(_2fa_verified=True)
        
        await message.answer(
            "✅ Двухфакторная аутентификация успешно включена!\n\n"
            "Теперь при каждом входе с нового устройства вам нужно будет вводить код из приложения аутентификатора.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Логирование
        await role_repository.log_audit_event(
            user_id=user_id,
            action="2FA_ENABLED_SUCCESS",
            entity_type="user",
            entity_id=user_id
        )
    else:
        # Неверный код
        await message.answer("❌ Неверный код подтверждения. Пожалуйста, попробуйте еще раз.")
        
        # Логируем попытку
        await role_repository.log_audit_event(
            user_id=user_id,
            action="2FA_INVALID_CODE",
            entity_type="user",
            entity_id=user_id
        )
        return
    
    # Очищаем состояние
    await state.clear()

@router.callback_query(F.data == "2fa_disable")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def disable_2fa(callback: types.CallbackQuery, state: FSMContext):
    """Отключение 2FA."""
    user_id = callback.from_user.id
    
    # Создаем клавиатуру с подтверждением
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Да, отключить", callback_data="2fa_confirm_disable")],
        [types.InlineKeyboardButton(text="❌ Нет, оставить", callback_data="2fa_cancel_disable")]
    ])
    
    await callback.message.answer(
        "⚠️ Вы уверены, что хотите отключить двухфакторную аутентификацию?\n\n"
        "Это снизит безопасность вашего аккаунта.",
        reply_markup=keyboard
    )
    
    await callback.answer()

@router.callback_query(F.data == "2fa_confirm_disable")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def confirm_disable_2fa(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение отключения 2FA."""
    user_id = callback.from_user.id
    
    # Отключаем 2FA
    await two_factor_auth.disable_2fa(user_id)
    
    # Очищаем состояние аутентификации
    await state.update_data(_2fa_verified=False)
    
    await callback.message.answer(
        "🔓 Двухфакторная аутентификация отключена.\n\n"
        "Вы можете снова включить её в любое время через команду /2fa"
    )
    
    # Логируем событие
    await role_repository.log_audit_event(
        user_id=user_id,
        action="2FA_DISABLED_SUCCESS",
        entity_type="user",
        entity_id=user_id
    )
    
    await callback.answer()

@router.callback_query(F.data == "2fa_cancel_disable")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def cancel_disable_2fa(callback: types.CallbackQuery, state: FSMContext):
    """Отмена отключения 2FA."""
    await callback.message.answer("✅ Двухфакторная аутентификация остается включенной.")
    await callback.answer()

@router.callback_query(F.data == "2fa_reset")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def reset_2fa(callback: types.CallbackQuery, state: FSMContext):
    """Сброс ключа 2FA."""
    user_id = callback.from_user.id
    
    # Создаем клавиатуру с подтверждением
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Да, сгенерировать новый", callback_data="2fa_confirm_reset")],
        [types.InlineKeyboardButton(text="❌ Нет, оставить текущий", callback_data="2fa_cancel_reset")]
    ])
    
    await callback.message.answer(
        "⚠️ Вы уверены, что хотите сгенерировать новый ключ 2FA?\n\n"
        "Это приведет к неработоспособности старого ключа, и вам нужно будет заново настроить приложение аутентификатора.",
        reply_markup=keyboard
    )
    
    await callback.answer()

@router.callback_query(F.data == "2fa_confirm_reset")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def confirm_reset_2fa(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение сброса 2FA."""
    user_id = callback.from_user.id
    
    # Генерируем новый секретный ключ
    secret_key = two_factor_auth.generate_secret_key()
    
    # Сохраняем ключ в состоянии
    await state.update_data(secret_key=secret_key)
    
    # Генерируем URI для настройки в приложении аутентификаторе
    uri = two_factor_auth.get_totp_uri(callback.from_user.username or str(user_id), secret_key)
    
    # Генерируем QR-код
    qr_code = two_factor_auth.generate_qr_code(uri)
    
    # Отправляем QR-код и инструкции
    await callback.message.answer_photo(
        types.BufferedInputFile(qr_code, filename="2fa_qr.png"),
        caption="🔄 Сгенерирован новый ключ 2FA\n\n"
               "1. Откройте приложение аутентификатора\n"
               "2. Удалите старую запись для этого сервиса\n"
               "3. Отсканируйте новый QR-код или введите ключ вручную:\n"
               f"<code>{secret_key}</code>\n\n"
               "4. Введите 6-значный код из приложения",
        parse_mode="HTML"
    )
    
    # Переходим в состояние ожидания кода
    await state.set_state(TwoFactorStates.waiting_for_code)
    await callback.answer()

@router.callback_query(F.data == "2fa_cancel_reset")
@require_permission(Permission.MANAGE_OWN_PROFILE)
async def cancel_reset_2fa(callback: types.CallbackQuery, state: FSMContext):
    """Отмена сброса 2FA."""
    await callback.message.answer("✅ Ключ 2FA не был изменен.")
    await callback.answer()

# Регистрируем обработчики
handlers = [router]
