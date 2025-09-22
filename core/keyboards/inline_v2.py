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
    ("shops", "🛍️"),
]


def get_categories_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Six fixed inline categories. Callbacks: pg:<slug>:all:1
    Labels exactly match reply menu texts (i18n), without adding extra emojis.
    """
    rows: List[List[InlineKeyboardButton]] = []
    for slug, _emoji in CATEGORY_SLUGS:
        key = "category_shops_services" if slug == "shops" else f"category_{slug}"
        label = get_text(key, lang)
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pg:{slug}:all:1")])
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


def get_activity_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Activity screen inline keyboard.
    Callbacks:
      - actv:checkin
      - actv:profile
      - actv:bindcard
      - actv:geocheckin
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🎯 {get_text('actv_checkin', lang)}", callback_data="actv:checkin")],
            [InlineKeyboardButton(text=f"🧩 {get_text('actv_profile', lang)}", callback_data="actv:profile")],
            [InlineKeyboardButton(text=f"🪪 {get_text('actv_bindcard', lang)}", callback_data="actv:bindcard")],
            [InlineKeyboardButton(text=f"📍 {get_text('actv_geocheckin', lang)}", callback_data="actv:geocheckin")],
        ]
    )


def get_add_card_choice_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline-меню: выбор действия для кнопки «➕ Добавить карточку».
    Callbacks:
      - act:add_partner_card — запустить мастер добавления партнёрской карточки
      - act:bind_plastic     — привязать пластиковую карту лояльности
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧑‍💼 Карточка партнёра", callback_data="act:add_partner_card")],
            [InlineKeyboardButton(text="🪪 Привязать пластиковую карту", callback_data="act:bind_plastic")],
        ]
    )

def get_admin_cabinet_inline(lang: str = "ru", is_superadmin: bool = False) -> InlineKeyboardMarkup:
    """
    Admin cabinet inline keyboard. Callbacks use namespace adm:*
    """
    rows = [
        [InlineKeyboardButton(text=get_text("admin_menu_queue", lang), callback_data="adm:queue")],
        [
            InlineKeyboardButton(text=get_text("admin_menu_search", lang), callback_data="adm:search"),
            InlineKeyboardButton(text=get_text("admin_menu_reports", lang), callback_data="adm:reports"),
        ],
    ]
    if is_superadmin:
        rows.insert(0, [InlineKeyboardButton(text="👑 Суперадмин", callback_data="adm:su")])
    rows.append([InlineKeyboardButton(text=get_text("back", lang), callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_superadmin_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Superadmin submenu inline keyboard. Callbacks: adm:su:*"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Бан", callback_data="adm:su:ban"), InlineKeyboardButton(text="✅ Разбан", callback_data="adm:su:unban")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data="adm:su:del")],
            [InlineKeyboardButton(text="🗑 Удалить пользователя", callback_data="adm:su:deluser")],
            [InlineKeyboardButton(text="➕ Добавить карточку", callback_data="adm:su:addcard")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:queue")],
        ]
    )

def get_superadmin_delete_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Delete submenu for superadmin. Callbacks: adm:su:del*"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Выбрать все", callback_data="adm:su:delallcards")],
            [InlineKeyboardButton(text="🗑 Удалить карточку", callback_data="adm:su:delcard")],
            [InlineKeyboardButton(text="🗑 Все карточки партнёра", callback_data="adm:su:delcards_by_tg")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:su")],
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
        row.append(InlineKeyboardButton(text="🗺️", url=gmaps_url))
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


def get_catalog_card_actions(card_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline-кнопки для детального вида карточки каталога.
    Ряды:
      [📱 QR] [📷 Фото] [⭐ Избранное]
      [◀️ Назад]

    Примечания:
    - QR: используем существующий поток создания QR (callback "qr_create").
    - Фото: gallery:<id> для просмотра фотографий
    - Избранное: favorite:<id> для добавления в избранное
    - Назад: catalog:back (возврат к списку из state)
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 QR", callback_data=f"qr_create:{card_id}"),
                InlineKeyboardButton(text="📷 Фото", callback_data=f"gallery:{card_id}"),
                InlineKeyboardButton(text="⭐", callback_data=f"favorite:{card_id}"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="catalog:back")],
        ]
    )


def get_favorites_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for favorites management"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="favorites_refresh"),
                InlineKeyboardButton(text="🗑️ Очистить все", callback_data="favorites_clear")
            ],
            [
                InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")
            ]
        ]
    )

def get_language_inline(active: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Language selection inline keyboard with flags in 2 rows.
    
    Args:
        active: Active language code to mark as selected (optional)
        
    Returns:
        InlineKeyboardMarkup with language selection buttons
        
    Callback format: lang:set:(ru|en|vi|ko)
    """
    languages = [
        ("🇷🇺 Русский", "ru"),
        ("🇺🇸 English", "en"),
        ("🇻🇳 Tiếng Việt", "vi"),
        ("🇰🇷 한국어", "ko"),
    ]
    
    # Create buttons in 2 rows (2 languages per row)
    buttons = []
    for i in range(0, len(languages), 2):
        row = []
        for j in range(2):
            if i + j < len(languages):
                text, code = languages[i + j]
                # Don't filter out current language - show all options
                row.append(InlineKeyboardButton(text=text, callback_data=f"lang:set:{code}"))
        buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cities_inline(active_id: Optional[int] = None, cb_prefix: str = "city:set") -> InlineKeyboardMarkup:
    """City selection keyboard. Callback: <cb_prefix>:<id>
    Provides four cities: Нячанг (1), Дананг (2), Хошимин (3), Фукуок (4).
    cb_prefix defaults to "city:set" for backward compatibility.
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
        rows.append([InlineKeyboardButton(text=label(title, cid), callback_data=f"{cb_prefix}:{cid}")])
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
                    callback_data="policy:view"
                )
            ]
        ]
    )
