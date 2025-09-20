"""
Restaurant selection keyboards for KARMABOT.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any


def select_restoran(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Main restaurant selection keyboard.
    """
    texts = {
        "ru": {
            "choose_district": "🏘️ Выбрать район",
            "rest_near_me": "📍 Рестораны рядом",
            "language": "🌐 Язык",
            "back_to_main": "◀️ Главное меню"
        },
        "en": {
            "choose_district": "🏘️ Choose District", 
            "rest_near_me": "📍 Restaurants Nearby",
            "language": "🌐 Language",
            "back_to_main": "◀️ Main Menu"
        },
        "ko": {
            "choose_district": "🏘️ 지역 선택",
            "rest_near_me": "📍 근처 레스토랑",
            "language": "🌐 언어",
            "back_to_main": "◀️ 메인 메뉴"
        }
    }
    
    text = texts.get(lang, texts["ru"])
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=text["choose_district"],
                callback_data="choose_district"
            )
        ],
        [
            InlineKeyboardButton(
                text=text["rest_near_me"],
                callback_data="rest_near_me"
            )
        ],
        [
            InlineKeyboardButton(
                text=text["language"],
                callback_data="change_language"
            ),
            InlineKeyboardButton(
                text=text["back_to_main"],
                callback_data="back_to_main"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def regional_restoran(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Regional restaurant selection keyboard.
    """
    texts = {
        "ru": {
            "district_1": "🏙️ Центр",
            "district_2": "🏖️ Пляжная зона", 
            "district_3": "🏘️ Жилой район",
            "district_4": "🏢 Деловой район",
            "back": "◀️ Назад"
        },
        "en": {
            "district_1": "🏙️ Downtown",
            "district_2": "🏖️ Beach Area",
            "district_3": "🏘️ Residential",
            "district_4": "🏢 Business District", 
            "back": "◀️ Back"
        },
        "ko": {
            "district_1": "🏙️ 시내",
            "district_2": "🏖️ 해변 지역",
            "district_3": "🏘️ 주거 지역",
            "district_4": "🏢 비즈니스 지역",
            "back": "◀️ 뒤로"
        }
    }
    
    text = texts.get(lang, texts["ru"])
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=text["district_1"],
                callback_data="district_1"
            ),
            InlineKeyboardButton(
                text=text["district_2"],
                callback_data="district_2"
            )
        ],
        [
            InlineKeyboardButton(
                text=text["district_3"],
                callback_data="district_3"
            ),
            InlineKeyboardButton(
                text=text["district_4"],
                callback_data="district_4"
            )
        ],
        [
            InlineKeyboardButton(
                text=text["back"],
                callback_data="back_to_restaurants"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def kitchen_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Kitchen type selection keyboard.
    """
    texts = {
        "ru": {
            "asian": "🍜 Азиатская",
            "european": "🍽️ Европейская",
            "local": "🏠 Местная",
            "fast_food": "🍔 Фастфуд",
            "back": "◀️ Назад"
        },
        "en": {
            "asian": "🍜 Asian",
            "european": "🍽️ European", 
            "local": "🏠 Local",
            "fast_food": "🍔 Fast Food",
            "back": "◀️ Back"
        },
        "ko": {
            "asian": "🍜 아시아",
            "european": "🍽️ 유럽",
            "local": "🏠 현지",
            "fast_food": "🍔 패스트푸드",
            "back": "◀️ 뒤로"
        }
    }
    
    text = texts.get(lang, texts["ru"])
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=text["asian"],
                callback_data="kitchen_asian"
            ),
            InlineKeyboardButton(
                text=text["european"],
                callback_data="kitchen_european"
            )
        ],
        [
            InlineKeyboardButton(
                text=text["local"],
                callback_data="kitchen_local"
            ),
            InlineKeyboardButton(
                text=text["fast_food"],
                callback_data="kitchen_fast_food"
            )
        ],
        [
            InlineKeyboardButton(
                text=text["back"],
                callback_data="back_to_districts"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
