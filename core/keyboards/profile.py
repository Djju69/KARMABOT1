from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура личного кабинета"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💳 Баланс",
            callback_data="loyalty_balance"
        ),
        InlineKeyboardButton(
            text="📊 История операций",
            callback_data="loyalty_history"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🎟️ Мои QR-коды",
            callback_data="my_qr_codes"
        ),
        InlineKeyboardButton(
            text="👥 Рефералы",
            callback_data="referral_info"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настройки",
            callback_data="profile_settings"
        ),
        InlineKeyboardButton(
            text="❓ Помощь",
            callback_data="help_profile"
        )
    )
    
    return builder.as_markup()

def get_back_to_profile_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в профиль"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔙 В профиль",
        callback_data="profile"
    )
    return builder.as_markup()
