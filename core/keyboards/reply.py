"""
Reply keyboard layouts following the v4.1 specification.
Centralized keyboard builder for all reply keyboards in the application.
"""
import logging
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
    
    # Main menu screen (v4.2.4 – exactly 5 buttons, 3 rows)
    if screen == SCREEN_MAIN:
        def label(primary_key: str, fallback_key: str) -> str:
            try:
                text = get_text(primary_key, lang)
                return text if text and not text.startswith("[") else get_text(fallback_key, lang)
            except Exception:
                return get_text(fallback_key, lang)

        row1 = [
            KeyboardButton(text=label("menu.categories", "keyboard.categories")),
            KeyboardButton(text=label("menu.invite_friends", "keyboard.referral_program")),
        ]
        row2 = [
            KeyboardButton(text=label("menu.become_partner", "keyboard.become_partner")),
            KeyboardButton(text=label("menu.help", "keyboard.help")),
        ]
        row3 = [
            KeyboardButton(text=label("menu.profile", "keyboard.profile")),
        ]
        kb = [row1, row2, row3]
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
    Generate main menu reply keyboard with fallbacks for missing translations.
    
    Args:
        lang: Language code (default: 'ru')
        
    Returns:
        ReplyKeyboardMarkup: Configured reply keyboard with fallback values
    """
    logger = logging.getLogger(__name__)
    
    # Emergency fallback keyboard
    emergency_keyboard = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="🗂️ Категории"),
            KeyboardButton(text="📍 Ближайшие")
        ], [
            KeyboardButton(text="❓ Помощь"),
            KeyboardButton(text="🌐 Язык")
        ]],
        resize_keyboard=True
    )
    
    # Default fallback values
    default_buttons = {
        'keyboard.categories': '🗂️ Категории',
        'keyboard.nearest': '📍 Ближайшие',
        'keyboard.help': '❓ Помощь',
        'keyboard.choose_language': '🌐 Сменить язык'
    }
    
    def safe_get_text(key: str, lang: str) -> str:
        """Safely get translated text with fallback to defaults"""
        try:
            text = get_text(key, lang)
            if not text:
                logger.warning(f"Empty text for key '{key}'")
                return default_buttons.get(key, key)
            return text
        except Exception as e:
            logger.warning(f"Failed to get text for key '{key}': {str(e)}")
            return default_buttons.get(key, key)
    
    try:
        logger.info(f"[MENU] Generating menu for lang: {lang}")
        keyboard = []
        
        # Row 1: Categories and Nearest
        try:
            categories = safe_get_text("keyboard.categories", lang)
            nearest = safe_get_text("keyboard.nearest", lang)
            
            if not categories or not nearest:
                logger.error(f"[MENU] Invalid button text: categories='{categories}', nearest='{nearest}'")
                return emergency_keyboard
                
            row1 = [
                KeyboardButton(text=categories),
                KeyboardButton(text=nearest)
            ]
            keyboard.append(row1)
            logger.debug("[MENU] Added first row")
            
        except Exception as e:
            logger.error(f"[MENU] Failed to create first row: {str(e)}", exc_info=True)
            return emergency_keyboard
            
        # Row 2: Profile and QR Codes
        try:
            profile = safe_get_text("keyboard.profile", lang)
            qr_codes = "🎫 QR-коды"  # Hardcoded for now
            
            row2 = [
                KeyboardButton(text=profile),
                KeyboardButton(text=qr_codes)
            ]
            keyboard.append(row2)
            logger.debug("[MENU] Added second row")
            
        except Exception as e:
            logger.error(f"[MENU] Failed to create first row: {str(e)}", exc_info=True)
            return emergency_keyboard
            
        # Row 3: Help and Language
        try:
            row3 = [
                KeyboardButton(text=safe_get_text("keyboard.help", lang)),
                KeyboardButton(text=safe_get_text("keyboard.choose_language", lang))
            ]
            keyboard.append(row3)
        except Exception as e:
            logger.error(f"Failed to create third row: {str(e)}")
            # If we can't create the third row, at least return the first two
            if not keyboard:
                raise
                
        logger.debug(f"Created menu keyboard with {len(keyboard)} rows")
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
    except Exception as e:
        logger.critical(f"Critical error in get_main_menu_reply: {str(e)}", exc_info=True)
        # Return a minimal working keyboard as fallback
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Главное меню")]],
            resize_keyboard=True
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
        resize_keyboard=True
    )


def get_user_profile_keyboard(user: dict) -> ReplyKeyboardMarkup:
    """
    Generate user profile keyboard with dynamic language support.
    
    Args:
        user: User dictionary containing at least 'lang' key
        
    Returns:
        ReplyKeyboardMarkup: Configured keyboard for user profile
    """
    lang = user.get('lang', 'ru')
    
    keyboard = [
        [
            KeyboardButton(text=get_text("keyboard.points", lang)),
            KeyboardButton(text=get_text("keyboard.history", lang)),
            KeyboardButton(text=get_text("keyboard.spend", lang))
        ],
        [
            KeyboardButton(text=get_text("keyboard.report", lang)),
            KeyboardButton(text=get_text("keyboard.card", lang)),
            KeyboardButton(text=get_text("keyboard.settings", lang))
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_user_points_keyboard(user: dict) -> ReplyKeyboardMarkup:
    """
    Generate keyboard for user points screen.
    
    Args:
        user: User dictionary containing at least 'lang' key
        
    Returns:
        ReplyKeyboardMarkup: Configured keyboard for points screen
    """
    lang = user.get('lang', 'ru')
    
    keyboard = [
        [
            KeyboardButton(text=get_text("keyboard.spend", lang)),
            KeyboardButton(text=get_text("keyboard.history", lang)),
            KeyboardButton(text=get_text("keyboard.back", lang))
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_user_settings_keyboard(user: dict) -> ReplyKeyboardMarkup:
    """
    Generate keyboard for user settings screen.
    
    Args:
        user: User dictionary containing at least 'lang' key
        
    Returns:
        ReplyKeyboardMarkup: Configured keyboard for settings screen
    """
    lang = user.get('lang', 'ru')
    
    keyboard = [
        [
            KeyboardButton(text=get_text("keyboard.city", lang)),
            KeyboardButton(text=get_text("keyboard.language", lang)),
            KeyboardButton(text=get_text("keyboard.notifications", lang))
        ],
        [
            KeyboardButton(text=get_text("keyboard.policy", lang)),
            KeyboardButton(text=get_text("keyboard.become_partner", lang)),
            KeyboardButton(text=get_text("keyboard.back", lang))
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_partner_profile_keyboard(user: dict, has_approved_cards: bool = False) -> ReplyKeyboardMarkup:
    """
    Generate partner profile keyboard with dynamic language support.
    
    Args:
        user: User dictionary containing at least 'lang' key
        has_approved_cards: Whether the partner has any approved cards
        
    Returns:
        ReplyKeyboardMarkup: Configured keyboard for partner profile
    """
    lang = user.get('lang', 'ru')
    keyboard = []
    
    # Add QR scan button if partner has approved cards
    if has_approved_cards:
        keyboard.append([
            KeyboardButton(text=get_text("keyboard.scan_qr", lang))
        ])
    
    # Add main buttons
    keyboard.extend([
        [
            KeyboardButton(text=get_text("keyboard.my_cards", lang)),
            KeyboardButton(text=get_text("keyboard.report", lang)),
            KeyboardButton(text=get_text("keyboard.settings", lang))
        ],
        [
            KeyboardButton(text=get_text("keyboard.statistics", lang)),
            KeyboardButton(text=get_text("keyboard.support", lang)),
            KeyboardButton(text=get_text("keyboard.back", lang))
        ]
    ])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_partner_cards_keyboard(user: dict) -> ReplyKeyboardMarkup:
    """
    Generate keyboard for partner cards screen.
    
    Args:
        user: User dictionary containing at least 'lang' key
        
    Returns:
        ReplyKeyboardMarkup: Configured keyboard for partner cards screen
    """
    lang = user.get('lang', 'ru')
    
    keyboard = [
        [
            KeyboardButton(text=get_text("keyboard.add_card", lang)),
            KeyboardButton(text=get_text("keyboard.back", lang))
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_confirmation_keyboard(user: dict) -> ReplyKeyboardMarkup:
    """
    Generate confirmation/cancel keyboard.
    
    Args:
        user: User dictionary containing at least 'lang' key
        
    Returns:
        ReplyKeyboardMarkup: Confirmation keyboard
    """
    lang = user.get('lang', 'ru')
    
    keyboard = [
        [
            KeyboardButton(text=get_text("keyboard.confirm", lang)),
            KeyboardButton(text=get_text("keyboard.cancel", lang))
        ]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

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
