"""
Inline keyboards for categories, pagination and profile actions (v2)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
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


def get_admin_cabinet_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Admin cabinet inline keyboard. Callbacks use namespace adm:*
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("admin_menu_queue", lang), callback_data="adm:queue"),
            ],
            [
                InlineKeyboardButton(text=get_text("admin_menu_search", lang), callback_data="adm:search"),
                InlineKeyboardButton(text=get_text("admin_menu_reports", lang), callback_data="adm:reports"),
            ],
            [
                InlineKeyboardButton(text=get_text("back", lang), callback_data="adm:back"),
            ],
        ]
    )


def get_webapp_inline(url: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Single-button inline keyboard that opens WebApp via WebAppInfo.
    This keeps WebApp accessible only when the /webapp command is used.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("webapp_open", lang), web_app=WebAppInfo(url=url))]
        ]
    )


def get_catalog_item_row(listing_id: int, gmaps_url: Optional[str], lang: str = "ru") -> List[InlineKeyboardButton]:
    """Row with info button and map url (if any)"""
    row = [InlineKeyboardButton(text="ℹ️", callback_data=f"act:view:{listing_id}")]
    if gmaps_url:
        row.append(InlineKeyboardButton(text=get_text("show_on_map", lang), url=gmaps_url))
    return row


def get_pagination_row(slug: str, page: int, pages: int, sub_slug: str = "all") -> List[InlineKeyboardButton]:
    """Prev/Next buttons for catalog pages. Callback: pg:<slug>:<sub_slug>:<page>"""
    buttons: List[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"pg:{slug}:{sub_slug}:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{pages}", callback_data="noop"))
    if page < pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"pg:{slug}:{sub_slug}:{page+1}"))
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
    Provides four cities: Нячанг (1), Дананг (2), Хошимин (3), Фукуок (4).
    """
    cities: List[tuple[str, int]] = [
        ("📍 Нячанг", 1),
        ("📍 Дананг", 2),
        ("📍 Хошимин", 3),
        ("📍 Фукуок", 4),
    ]

    def label(txt: str, cid: int) -> str:
        # Если город ещё не выбран, подсветим Нячанг (id=1) как дефолтный
        eff_active = active_id if active_id is not None else 1
        return ("✅ " if eff_active == cid else "") + txt

    rows: List[List[InlineKeyboardButton]] = []
    for title, cid in cities:
        rows.append([InlineKeyboardButton(text=label(title, cid), callback_data=f"city:set:{cid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_policy_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Клавиатура для принятия политики конфиденциальности
    
    Args:
        lang: Язык интерфейса (по умолчанию: "ru")
        
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками
    """
    from ..utils.locales_v2 import get_text
    from ..settings import settings
    # Telegram requires absolute URLs in inline buttons. Build from configured base.
    base = (getattr(settings, 'webapp_qr_url', '') or '').rstrip('/')
    policy_path = get_text("policy_url", lang)
    policy_url = f"{base}{policy_path}" if base and policy_path.startswith('/') else policy_path
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("policy_accept", lang),
                    callback_data="policy:accept"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("policy_view", lang),
                    url=policy_url
                )
            ]
        ]
    )
