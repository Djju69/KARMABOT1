"""
Inline keyboards for categories, pagination and profile actions (v2)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

CATEGORIES = [
    ("🍽 Рестораны и кафе", "restaurants"),
    ("🧖‍♀️ SPA и массаж", "spa"),
    ("🚗 Аренда транспорта", "transport"),
    ("🏨 Отели", "hotels"),
    ("🚶‍♂️ Экскурсии", "tours"),
]


def get_categories_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Five fixed inline categories. Callbacks: pg:<slug>:1"""
    rows: List[List[InlineKeyboardButton]] = []
    for title, slug in CATEGORIES:
        rows.append([InlineKeyboardButton(text=title, callback_data=f"pg:{slug}:1")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_restaurant_filters_inline(active: Optional[str] = None) -> InlineKeyboardMarkup:
    """Restaurant filters block for category restaurants.
    Callbacks: filt:restaurants:(asia|europe|street|vege|all)
    """
    def label(txt: str, key: str) -> str:
        return ("✅ " if active == key else "") + txt

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=label("🥢 Азиатская", "asia"), callback_data="filt:restaurants:asia"),
                InlineKeyboardButton(text=label("🍝 Европейская", "europe"), callback_data="filt:restaurants:europe"),
            ],
            [
                InlineKeyboardButton(text=label("🌭 Стрит-фуд", "street"), callback_data="filt:restaurants:street"),
                InlineKeyboardButton(text=label("🥗 Вегетарианская", "vege"), callback_data="filt:restaurants:vege"),
            ],
            [InlineKeyboardButton(text=label("🔎 Показать все", "all"), callback_data="filt:restaurants:all")],
        ]
    )


def get_catalog_item_row(listing_id: int, gmaps_url: Optional[str]) -> List[InlineKeyboardButton]:
    """Row with info button and map url (if any)"""
    row = [InlineKeyboardButton(text="ℹ️", callback_data=f"act:view:{listing_id}")]
    if gmaps_url:
        row.append(InlineKeyboardButton(text="Показать на карте", url=gmaps_url))
    return row


def get_pagination_row(slug: str, page: int, pages: int) -> List[InlineKeyboardButton]:
    """Prev/Next buttons for catalog pages"""
    buttons: List[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"pg:{slug}:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{pages}", callback_data="noop"))
    if page < pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"pg:{slug}:{page+1}"))
    return buttons


def get_language_inline(active: Optional[str] = None) -> InlineKeyboardMarkup:
    """Language selection keyboard. Callbacks: lang:set:(ru|en|vi|ko)"""
    langs: List[tuple[str, str]] = [
        ("🇷🇺 Русский", "ru"),
        ("🇺🇸 English", "en"),
        ("🇻🇳 Tiếng Việt", "vi"),
        ("🇰🇷 한국어", "ko"),
    ]

    def label(txt: str, code: str) -> str:
        return ("✅ " if active == code else "") + txt

    rows: List[List[InlineKeyboardButton]] = []
    for title, code in langs:
        rows.append([InlineKeyboardButton(text=label(title, code), callback_data=f"lang:set:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
