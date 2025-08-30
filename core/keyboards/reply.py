"""
Reply keyboard layouts following the v4.1 specification.
Centralized keyboard builder for all reply keyboards in the application.
"""
from typing import Optional, List, Dict, Any, Callable, Union
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from core.utils.locales_v2 import get_text, get_all_texts

# Screen names for reference
SCREEN_MAIN = "main"
SCREEN_PROFILE = "profile"
SCREEN_POINTS = "points"
SCREEN_HISTORY = "history"
SCREEN_SPEND = "spend"
SCREEN_CONFIRM = "confirm"
SCREEN_SETTINGS = "settings"
SCREEN_PARTNER_CABINET = "partner_cabinet"

def get_reply_keyboard(user: Optional[Dict[str, Any]] = None, screen: str = SCREEN_MAIN) -> ReplyKeyboardMarkup:
    """
    Centralized reply keyboard builder following v4.1 specification.
    
    Args:
        user: User object with properties like role, lang, has_partner_cards
        screen: Current screen/context (use SCREEN_* constants)
    """
    if user is None:
        user = {"role": "user", "lang": "ru", "has_partner_cards": False}
        
    lang = user.get("lang", "ru")
    is_partner = user.get("role") == "partner"
    
    def row(*keys: str) -> List[KeyboardButton]:
        """Create a row of buttons from i18n keys."""
        return [KeyboardButton(text=get_text(key, lang)) for key in keys]
    
    # Main menu screen
    if screen == SCREEN_MAIN:
        kb = [
            row("keyboard.categories", "keyboard.profile", "keyboard.by_districts", "keyboard.help"),
        ]
        
        # Dynamic QR scan button for partners with cards
        if is_partner and user.get("has_partner_cards", False):
            kb.append(row("keyboard.scan_qr"))
            
        # Language selector row (emoji flags with language codes)
        kb.append([
            KeyboardButton(text="🇷🇺 RU"),
            KeyboardButton(text="🇬🇧 EN"),
            KeyboardButton(text="🇻🇳 VI"),
            KeyboardButton(text="🇰🇷 KO")
        ])
        
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Profile screen
    elif screen == SCREEN_PROFILE:
        kb = [
            row("keyboard.points"),
            row("keyboard.history", "keyboard.spend"),
            row("keyboard.report", "keyboard.card"),
            row("keyboard.settings"),
            row("keyboard.back")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Points screen
    elif screen == SCREEN_POINTS:
        kb = [
            row("keyboard.spend"),
            row("keyboard.history"),
            row("keyboard.back")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # History screen with pagination
    elif screen == SCREEN_HISTORY:
        kb = [
            row("keyboard.prev_page", "keyboard.next_page"),
            row("keyboard.back")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Spend points flow
    elif screen == SCREEN_SPEND:
        kb = [
            row("keyboard.enter_amount"),
            row("keyboard.cancel")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Confirmation screen
    elif screen == SCREEN_CONFIRM:
        kb = [
            row("keyboard.confirm", "keyboard.cancel"),
            row("keyboard.back")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Settings screen
    elif screen == SCREEN_SETTINGS:
        kb = [
            row("keyboard.city"),
            row("keyboard.lang", "keyboard.notifications"),
            row("keyboard.policy"),
            row("keyboard.become_partner") if not is_partner else row("keyboard.partner_cabinet"),
            row("keyboard.back")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        
    # Partner cabinet screen
    elif screen == SCREEN_PARTNER_CABINET:
        kb = [
            row("keyboard.my_restaurants", "keyboard.my_spa"),
            row("keyboard.my_cars", "keyboard.my_hotels"),
            row("keyboard.my_tours", "keyboard.stats"),
            row("keyboard.scan_qr", "keyboard.settings"),
            row("keyboard.back")
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    # Default to main menu
    return get_reply_keyboard(user, SCREEN_MAIN)

def get_main_menu_reply(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Generate main menu reply keyboard.
    
    Args:
        lang: Language code (default: 'ru')
        
    Returns:
        ReplyKeyboardMarkup: Configured reply keyboard
    """
    keyboard = [
        [
            KeyboardButton(text=get_text("keyboard.categories", lang)),
            KeyboardButton(text=get_text("keyboard.nearest", lang))
        ],
        [
            KeyboardButton(text=get_text("keyboard.help", lang)),
            KeyboardButton(text=get_text("keyboard.choose_language", lang))
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_return_to_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Return to main menu button with proper localization."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text("keyboard.back_to_main", lang))]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_cancel_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Cancel operation button with proper localization."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text('keyboard.cancel', lang))]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_test_restoran(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Главное меню с ресторанами, районами, категориями и сменой языка."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Hải sản Mộc quán Nha Trang🦞')],
            [KeyboardButton(text=get_text('choose_district', lang))],
            [KeyboardButton(text=get_text('choose_category', lang))],
            [KeyboardButton(text=get_text('show_nearest', lang))],
            [KeyboardButton(text=get_text('keyboard.lang', lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора языка."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇷🇺 Русский"),
                KeyboardButton(text="🇬🇧 English"),
                KeyboardButton(text="🇰🇷 한국어")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# --- compatibility alias for test_restoran ---
def _resolve_test_restoran() -> Callable[..., Any]:
    g = globals()

    # 1) Явные кандидаты по распространённым именам
    preferred = [
        "test_restoran",
        "test_restoran_kb",
        "build_test_restoran",
        "build_restoran_menu",
        "build_restaurants_menu",
        "restaurants_menu",
        "restoran_menu",
        "get_restoran_kb",
        "get_restaurants_kb",
        "restaurant_menu",
        "build_restaurant_kb",
        "build_restaurants_kb",
        "get_test_restoran",  # текущая реализация в файле
    ]
    for name in preferred:
        fn = g.get(name)
        if callable(fn):
            return fn

    # 2) Эвристика: любая функция с ключевыми словами
    for name, fn in g.items():
        if callable(fn) and hasattr(fn, '__code__'):
            n = name.lower()
            if ("restoran" in n or "restaurant" in n) and ("kb" in n or "menu" in n):
                return fn

    # 3) Безопасный фоллбэк: пустая клавиатура/ничего
    def _noop(*args: Any, **kwargs: Any) -> ReplyKeyboardRemove:
        return ReplyKeyboardRemove()
    
    return _noop

# Экспортируем совместимое имя, если его не было
if "test_restoran" not in globals():
    test_restoran = _resolve_test_restoran()  # type: ignore
