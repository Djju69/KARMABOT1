from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура личного кабинета"""
    builder = InlineKeyboardBuilder()
    
    # First row: Balance and History
    builder.row(
        InlineKeyboardButton(
            text="💳 Баланс",
            callback_data="loyalty_balance"
        ),
        InlineKeyboardButton(
            text="📊 История операций",
            callback_data="loyalty_history"
        ),
        width=2
    )
    
    # Second row: QR Codes and Referrals
    builder.row(
        InlineKeyboardButton(
            text="🎟️ Мои QR-коды",
            callback_data="my_qr_codes"
        ),
        InlineKeyboardButton(
            text="👥 Рефералы",
            callback_data="referral_info"
        ),
        width=2
    )
    
    # Third row: Settings and Help
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настройки",
            callback_data="profile_settings"
        ),
        InlineKeyboardButton(
            text="❓ Помощь",
            callback_data="help_profile"
        ),
        width=2
    )
    
    return builder.as_markup()

def get_qr_codes_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления QR-кодами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Создать QR-код",
            callback_data="create_qr_code"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить список",
            callback_data="my_qr_codes"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 В профиль",
            callback_data="profile"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_back_to_profile_keyboard(extra_button: tuple[str, str] = None) -> InlineKeyboardMarkup:
    """Кнопка возврата в профиль с опциональной дополнительной кнопкой
    
    Args:
        extra_button: Tuple of (text, callback_data) for additional button
    """
    builder = InlineKeyboardBuilder()
    
    if extra_button:
        builder.row(
            InlineKeyboardButton(
                text=extra_button[0],
                callback_data=extra_button[1]
            ),
            width=1
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 В профиль",
            callback_data="profile"
        ),
        width=1
    )
    
    return builder.as_markup()
