"""
Inline keyboards for categories, pagination and profile actions (v2)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from ..utils.locales_v2 import get_text

CATEGORY_SLUGS = [
    ("restaurants", "🍽"),
    ("spa", "🧖‍♀️"),
    ("transport", "🚗"),
    ("hotels", "🏨"),
    ("tours", "🚶‍♂️"),
]


def get_categories_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Five fixed inline categories. Callbacks: pg:<slug>:1"""
    rows: List[List[InlineKeyboardButton]] = []
    for slug, emoji in CATEGORY_SLUGS:
        key = f"category_{slug}"
        label = f"{emoji} {get_text(key, lang)}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pg:{slug}:1")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_restaurant_filters_inline(active: Optional[str] = None, lang: str = "ru") -> InlineKeyboardMarkup:
    """Restaurant filters block for category restaurants.
    Callbacks: filt:restaurants:(asia|europe|street|vege|all)
    """
    def label(txt: str, key: str) -> str:
        return ("✅ " if active == key else "") + txt

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=label("🥢 " + get_text("filter_asia", lang), "asia"), callback_data="filt:restaurants:asia"),
                InlineKeyboardButton(text=label("🍝 " + get_text("filter_europe", lang), "europe"), callback_data="filt:restaurants:europe"),
            ],
            [
                InlineKeyboardButton(text=label("🌭 " + get_text("filter_street", lang), "street"), callback_data="filt:restaurants:street"),
                InlineKeyboardButton(text=label("🥗 " + get_text("filter_vege", lang), "vege"), callback_data="filt:restaurants:vege"),
            ],
            [InlineKeyboardButton(text=label("🔎 " + get_text("filter_all", lang), "all"), callback_data="filt:restaurants:all")],
        ]
    )


def get_catalog_item_row(listing_id: int, gmaps_url: Optional[str], lang: str = "ru") -> List[InlineKeyboardButton]:
    """Row with info button and map url (if any)"""
    row = [InlineKeyboardButton(text="ℹ️", callback_data=f"act:view:{listing_id}")]
    if gmaps_url:
        row.append(InlineKeyboardButton(text=get_text("show_on_map", lang), url=gmaps_url))
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


def get_cities_inline(active_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """City selection keyboard. Callback: city:set:<id>
    Uses a small default list; replace with DB-driven list in Phase 1 final.
    """
    cities: List[tuple[str, int]] = [
        ("📍 Центр", 1),
        ("📍 Нячанг-Север", 2),
        ("📍 Нячанг-Юг", 3),
        ("📍 Камрань", 4),
        ("📍 Другой", 5),
    ]

    def label(txt: str, cid: int) -> str:
        return ("✅ " if active_id == cid else "") + txt

    rows: List[List[InlineKeyboardButton]] = []
    for title, cid in cities:
        rows.append([InlineKeyboardButton(text=label(title, cid), callback_data=f"city:set:{cid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_policy_inline() -> InlineKeyboardMarkup:
    """Policy acceptance keyboard. Callback: policy:accept"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принимаю", callback_data="policy:accept")]
        ]
    )
