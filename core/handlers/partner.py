"""
Модуль обработчиков для партнерского кабинета.
Включает управление заведениями и статистикой.
"""
from typing import Union, Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import re

from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, InputMediaPhoto, FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter

from core.settings import settings
from core.keyboards.reply import get_reply_keyboard
from core.database import db
from core.utils.locales_v2 import get_text as _

logger = logging.getLogger(__name__)

# Роутер для обработчиков партнерского кабинета
partner_router = Router()

# Константы
MAX_ESTABLISHMENTS = 10  # Максимальное количество заведений у партнера
ITEMS_PER_PAGE = 5  # Количество элементов на странице

from ..settings import settings
from ..services.profile import profile_service
from ..keyboards.reply_v2 import (
    get_partner_keyboard,
    get_main_menu_reply,
    get_profile_keyboard,
)
from ..keyboards.inline_v2 import get_cities_inline
from ..database.db_v2 import db_v2, Card
from ..utils.locales_v2 import translations, get_text

logger = logging.getLogger(__name__)

# --- Simple dictionaries for Areas per City and Subcategories per Category ---
# Area IDs are composed as city_id * 100 + local_id to keep them unique.
AREAS_BY_CITY: dict[int, list[tuple[str, int]]] = {
    1: [("🏙 Центр", 101), ("🌊 Север", 102), ("🏝 Юг", 103)],           # Нячанг
    2: [("🏙 Центр", 201), ("🏖️ Побережье", 202), ("🏞 Окрестности", 203)],  # Дананг
    3: [("🏙 Центр", 301), ("📈 Район 1", 302), ("📉 Район 2", 303)],       # Хошимин (примерно)
    4: [("🏝 Дуонг Донг", 401), ("🏖️ Бай Сао", 402), ("🏝 Онга Ланг", 403)], # Фукуок
}

# Subcategories per category slug. Use small numeric codes.
SUBCATS_BY_CATEGORY: dict[str, list[tuple[str, int]]] = {
    "restaurants": [
        ("🥢 Азия", 1101), ("🍝 Европа", 1102), ("🌭 Стритфуд", 1103), ("🥗 Вегетарианское", 1104)
    ],
    "transport": [
        ("🏍 Мото/Байк", 1201), ("🚗 Авто", 1202), ("🚲 Велосипед", 1203)
    ],
    "hotels": [
        ("🏨 Отель", 1301), ("🏡 Гестхаус", 1302), ("🏘 Апартаменты", 1303)
    ],
    "tours": [
        ("🤿 Снорк/Дайв", 1401), ("🚤 Морские", 1402), ("🚌 Наземные", 1403)
    ],
    "spa": [
        ("💆‍♀️ Массаж", 1501), ("🧖‍♀️ Спа-комплекс", 1502)
    ],
}

def get_areas_inline(city_id: int, active_id: int | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for title, aid in AREAS_BY_CITY.get(city_id, []):
        label = ("✅ " if active_id == aid else "") + title
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pfsm:area:{aid}")])
    # Always provide skip and cancel
    rows.append([InlineKeyboardButton(text="⏭️ Пропустить", callback_data="pfsm:area:skip")])
    rows.append([InlineKeyboardButton(text="❌ Отменить", callback_data="partner_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_subcategories_inline(category_slug: str, active_id: int | None = None) -> InlineKeyboardMarkup | None:
    items = SUBCATS_BY_CATEGORY.get(category_slug)
    if not items:
        return None
    rows: list[list[InlineKeyboardButton]] = []
    for title, scid in items:
        label = ("✅ " if active_id == scid else "") + title
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pfsm:subcat:{scid}")])
    rows.append([InlineKeyboardButton(text="⏭️ Пропустить", callback_data="pfsm:subcat:skip")])
    rows.append([InlineKeyboardButton(text="❌ Отменить", callback_data="partner_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _is_valid_gmaps(url: str) -> bool:
    """Проверка, что ссылка похожа на Google Maps."""
    if not url:
        return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    return any(h in url for h in ("google.com/maps", "goo.gl/maps", "maps.app.goo.gl", "g.page"))

# FSM States for adding cards
class AddCardStates(StatesGroup):
    choose_city = State()
    choose_area = State()
    choose_category = State()
    choose_subcategory = State()
    enter_title = State()
    enter_description = State()
    enter_contact = State()
    enter_address = State()
    enter_gmaps = State()
    upload_photo = State()
    enter_discount = State()
    preview_card = State()
    confirm_submit = State()

# Router for partner handlers
partner_router = Router()

def get_inline_skip_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard with a single Skip button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="partner_skip")]
    ])

def _valid_len(text: str, min_len: int = 0, max_len: int | None = None) -> bool:
    """Simple length validator helper."""
    if text is None:
        return False if min_len > 0 else True
    s = text.strip()
    if len(s) < min_len:
        return False
    if max_len is not None and len(s) > max_len:
        return False
    return True

def _validate_title(text: str) -> tuple[bool, str | None]:
    """Validate title: required, 3..100 symbols."""
    if not _valid_len(text, 3, 100):
        if not text or len(text.strip()) < 3:
            return False, "❌ Название слишком короткое. Минимум 3 символа."
        return False, "❌ Название слишком длинное. Максимум 100 символов."
    return True, None

def _validate_optional_max_len(text: str | None, max_len: int, too_long_msg: str) -> tuple[bool, str | None]:
    """Validate optional text: allow empty/None, enforce max length otherwise."""
    if text is None:
        return True, None
    if not _valid_len(text, 0, max_len):
        return False, too_long_msg
    return True, None

def _is_cancel_text(txt: str | None) -> bool:
    if not txt:
        return False
    norm = txt.strip().lower()
    cancel_variants = {
        "отменить", "отмена", "cancel", "стоп",
        "❌ отменить", "⛔ отменить", "❌ отмена", "⛔ отмена",
    }
    return norm in cancel_variants

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with cancel option"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⛔ Отменить")]],
        resize_keyboard=True
    )

def get_photos_reply_keyboard(current_count: int, max_photos: int = 6) -> ReplyKeyboardMarkup:
    """Reply-клавиатура для шага загрузки фото: 'Готово (X/max)' над 'Отменить'."""
    # Безопасность: ограничим границы для отображения
    c = max(0, min(int(current_count or 0), max_photos))
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"✅ Готово ({c}/{max_photos})")],
            [KeyboardButton(text="⛔ Отменить")],
        ],
        resize_keyboard=True,
    )

# Callback from inline choice menu: start partner card flow
@partner_router.callback_query(F.data == "act:add_partner_card")
async def on_add_partner_card_cb(callback: CallbackQuery, state: FSMContext):
    """Запустить мастер добавления карточки по каллбэку из меню выбора."""
    try:
        await callback.answer()
    except Exception:
        pass
    # Reuse the same flow as /add_card but via callback
    await start_add_card(callback.message, state)

# Alias: start adding card via /add_partner command
@partner_router.message(Command("add_partner"))
async def start_add_partner(message: Message, state: FSMContext):
    """Alias for /add_partner to start the same add-card flow."""
    await start_add_card(message, state)

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with skip and cancel options"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭️ Пропустить")],
            [KeyboardButton(text="⛔ Отменить")]
        ],
        resize_keyboard=True
    )

def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard with categories"""
    # Основной путь: новый метод
    try:
        categories = db_v2.get_categories()  # список Category
        items = []
        for c in categories:
            items.append({
                'slug': getattr(c, 'slug', None),
                'name': getattr(c, 'name', None),
                'emoji': getattr(c, 'emoji', '') or ''
            })
    except AttributeError:
        # Фоллбэк для старого билда: читаем напрямую из БД, чтобы не падать
        items = []
        try:
            with db_v2.get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT slug, name, COALESCE(emoji, '') AS emoji
                    FROM categories_v2
                    WHERE is_active = 1
                    ORDER BY priority_level DESC, name ASC
                    """
                )
                items = [dict(r) for r in cur.fetchall()]
        except Exception:
            items = []

    buttons: list[list[InlineKeyboardButton]] = []
    for item in items:
        slug = item.get('slug')
        name = item.get('name') or ''
        emoji = item.get('emoji') or ''
        if not slug or not name:
            continue
        label = f"{emoji} {name}".strip()
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"partner_cat:{slug}")])

    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="partner_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_preview_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for card preview"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data="partner_submit")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="partner_edit")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="partner_cancel")]
    ])

def get_partner_cards_inline(page: int = 0, has_prev: bool = False, has_next: bool = False) -> InlineKeyboardMarkup:
    """Inline keyboard: навигация по страницам списка карточек."""
    nav_row: list[InlineKeyboardButton] = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pc:page:{max(page-1,0)}"))
    nav_row.append(InlineKeyboardButton(text="🔄 Обновить", callback_data=f"pc:page:{page}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"pc:page:{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[nav_row])

def _build_cards_list_text(cards: list[dict], page: int, page_size: int, total: int) -> str:
    start = page * page_size
    end = start + len(cards)
    header = f"📂 Ваши карточки {start+1}–{end} из {total}:\n"
    lines = [header]
    for c in cards:
        title = (c.get('title') or '(без названия)')
        status = (c.get('status') or 'pending')
        cid = int(c.get('id'))
        lines.append(f"{_status_emoji(status)} {title} — {status}  (#${cid})")
    lines.append("\n👉 Нажмите ниже, чтобы открыть карточку и выполнить действие.")
    return "\n".join(lines)

def _build_cards_list_buttons(cards: list[dict], page: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for c in cards:
        title = (c.get('title') or '(без названия)')
        cid = int(c.get('id'))
        rows.append([InlineKeyboardButton(text=f"🔎 {title[:40]}", callback_data=f"pc:view:{cid}:{page}")])
    if not rows:
        rows = [[]]
    rows.append([InlineKeyboardButton(text="↩️ К списку", callback_data=f"pc:page:{page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def _render_cards_page(message_or_cbmsg, user_id: int, full_name: str, page: int, *, edit: bool = False):
    """Общий рендер страницы списка карточек для партнёра.
    message_or_cbmsg: объект с методами answer()/edit_text().
    edit=True будет пытаться редактировать сообщение, иначе отправлять новое.
    """
    PAGE_SIZE = 5
    partner = db_v2.get_or_create_partner(user_id, full_name)
    logger.info("partner.render_cards_page: user=%s partner_id=%s page=%s", user_id, partner.id, page)
    with db_v2.get_connection() as conn:
        total = int(
            conn.execute(
                "SELECT COUNT(*) FROM cards_v2 WHERE partner_id = ? AND status IN ('approved','published')",
                (partner.id,),
            ).fetchone()[0]
        )
        offset = max(page, 0) * PAGE_SIZE
        cur = conn.execute(
            """
            SELECT c.*, cat.name as category_name,
                   COALESCE(COUNT(cp.id), 0) as photos_count
            FROM cards_v2 c
            JOIN categories_v2 cat ON c.category_id = cat.id
            LEFT JOIN card_photos cp ON cp.card_id = c.id
            WHERE c.partner_id = ? AND c.status IN ('approved','published')
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (partner.id, PAGE_SIZE, offset),
        )
        cards = [dict(r) for r in cur.fetchall()]
    has_prev = page > 0
    has_next = (page + 1) * PAGE_SIZE < total
    if not cards:
        # пустая страница
        if edit:
            await message_or_cbmsg.edit_text(
                "📭 На этой странице карточек нет.",
                reply_markup=get_partner_cards_inline(page=page, has_prev=has_prev, has_next=has_next),
            )
        else:
            await message_or_cbmsg.answer(
                "📭 На этой странице карточек нет.",
                reply_markup=get_partner_cards_inline(page=page, has_prev=has_prev, has_next=has_next),
            )
        return
    text = _build_cards_list_text(cards, page=page, page_size=PAGE_SIZE, total=total)
    try:
        if edit:
            await message_or_cbmsg.edit_text(text, reply_markup=_build_cards_list_buttons(cards, page=page))
        else:
            await message_or_cbmsg.answer(text, reply_markup=_build_cards_list_buttons(cards, page=page))
    except Exception:
        # Фоллбэк: отправим новым сообщением
        await message_or_cbmsg.answer(text, reply_markup=_build_cards_list_buttons(cards, page=page))
    await message_or_cbmsg.answer("Навигация:", reply_markup=get_partner_cards_inline(page=page, has_prev=has_prev, has_next=has_next))

def _status_emoji(status: str) -> str:
    s = (status or "").lower()
    if s == "pending":
        return "⏳"
    if s == "published":
        return "✅"
    if s == "rejected":
        return "❌"
    if s == "draft":
        return "📝"
    return "•"

def format_card_preview(card_data: dict, category_name: str) -> str:
    """Format card preview text"""
    text = f"📋 **Предпросмотр карточки**\n\n"
    text += f"📂 **Категория:** {category_name}\n"
    text += f"📝 **Название:** {card_data.get('title', 'Не указано')}\n"
    
    if card_data.get('description'):
        text += f"📄 **Описание:** {card_data['description']}\n"
    
    if card_data.get('contact'):
        text += f"📞 **Контакт:** {card_data['contact']}\n"
    
    if card_data.get('address'):
        text += f"📍 **Адрес:** {card_data['address']}\n"
    
    if card_data.get('discount_text'):
        text += f"🎫 **Скидка:** {card_data['discount_text']}\n"
    
    # Поддержка мультифото в состоянии FSM
    photos = card_data.get('photos')
    if photos and isinstance(photos, list) and len(photos) > 0:
        text += f"📸 **Фото:** Прикреплено ({len(photos)} шт.)\n"
    elif card_data.get('photo_file_id'):
        text += f"📸 **Фото:** Прикреплено (1 шт.)\n"
    
    text += f"\n💡 После отправки карточка попадет на модерацию."
    
    return text

# Command to start adding card
@partner_router.message(Command("add_card"))
async def start_add_card(message: Message, state: FSMContext):
    """Start adding new card (only if feature enabled)"""
    if not settings.features.partner_fsm:
        await message.answer("🚧 Функция добавления карточек временно недоступна.")
        return
    
    # Get or create partner
    partner = db_v2.get_or_create_partner(
        message.from_user.id,
        message.from_user.full_name
    )
    
    # Сохраняем partner_id и город по умолчанию (Нячанг = 1)
    await state.update_data(partner_id=partner.id, city_id=1)
    await state.set_state(AddCardStates.choose_city)
    await message.answer(
        "🏪 Добавление новой карточки\n\nВыберите город (по умолчанию Нячанг):",
        reply_markup=get_cities_inline(active_id=1, cb_prefix="pfsm:city")
    )

# ===== Reply-button entry points (no new slash commands) =====
@partner_router.message(F.text.startswith("➕"))
async def start_add_card_via_button(message: Message, state: FSMContext):
    """Start add-card flow from reply keyboard button '➕ Добавить карточку'."""
    if not settings.features.partner_fsm:
        await message.answer("🚧 Добавление карточек временно недоступно.")
        return
    # Reuse the same flow as /add_card
    await start_add_card(message, state)

# ====== City selection ======
@partner_router.callback_query(F.data.startswith("pfsm:city:"))
async def on_city_selected(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = callback.data.split(":")
    # expected: pfsm:city:<id>
    city_id = int(data[-1]) if data and data[-1].isdigit() else 1
    await state.update_data(city_id=city_id)
    # После города — выбор района
    await state.set_state(AddCardStates.choose_area)
    await callback.message.edit_text(
        "Выберите район:",
        reply_markup=get_areas_inline(city_id)
    )

@partner_router.callback_query(F.data.startswith("pfsm:area:"))
async def on_area_selected(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = callback.data.split(":")
    val = data[-1] if data else "skip"
    if val != "skip" and val.isdigit():
        await state.update_data(area_id=int(val))
    else:
        await state.update_data(area_id=None)
    await state.set_state(AddCardStates.choose_category)
    await callback.message.edit_text(
        "Выберите категорию для вашего заведения:",
        reply_markup=get_categories_keyboard()
    )


@partner_router.message(F.text.startswith("📂"))
async def show_my_cards(message: Message):
    """Показать список карточек партнёра с пагинацией (кнопка '📂 Мои карточки')."""
    PAGE_SIZE = 5
    try:
        # Покажем первую страницу
        # Если карточек нет вообще — короткое сообщение с навигацией
        with db_v2.get_connection() as conn:
            partner = db_v2.get_or_create_partner(message.from_user.id, message.from_user.full_name)
            total = int(
                conn.execute(
                    "SELECT COUNT(*) FROM cards_v2 WHERE partner_id = ? AND status IN ('approved','published')",
                    (partner.id,)
                ).fetchone()[0]
            )
        if total == 0:
            await message.answer(
                "📭 У вас пока нет карточек. Нажмите '➕ Добавить карточку' чтобы создать первую.",
                reply_markup=get_partner_cards_inline(page=0, has_prev=False, has_next=False),
            )
            return
        await _render_cards_page(message, message.from_user.id, message.from_user.full_name, page=0, edit=False)
    except Exception as e:
        logger.exception("partner.show_my_cards failed: %s", e)
        await message.answer("❌ Ошибка при загрузке списка карточек. Попробуйте позже.")

# i18n handler: react to translated text for "Мои карточки"
@partner_router.message(F.text.in_([t.get('my_cards', '') for t in translations.values()]))
async def show_my_cards_i18n(message: Message):
    return await show_my_cards(message)

# i18n handler: react to translated text for "Добавить карточку"
@partner_router.message(F.text.in_([t.get('add_card', '') for t in translations.values()]))
async def start_add_card_via_button_i18n(message: Message, state: FSMContext):
    if not settings.features.partner_fsm:
        await message.answer("🚧 Добавление карточек временно недоступно.")
        return
    await start_add_card(message, state)

@partner_router.callback_query(F.data.startswith("pc:page:"))
async def partner_cards_page(callback: CallbackQuery):
    """Пагинация списка карточек: pc:page:<page>."""
    try:
        await callback.answer()
    except Exception:
        pass
    try:
        page = int(callback.data.split(":")[2])
        await _render_cards_page(callback.message, callback.from_user.id, callback.from_user.full_name, page=page, edit=True)
    except Exception as e:
        logger.exception("partner.cards_page failed: %s", e)
        try:
            await callback.message.edit_text("❌ Ошибка при обновлении списка. Попробуйте позже.")
        except Exception:
            await callback.message.answer("❌ Ошибка при обновлении списка. Попробуйте позже.")

@partner_router.callback_query(F.data.startswith("pc:view:"))
async def partner_card_view(callback: CallbackQuery):
    """Просмотр одной карточки и быстрые действия: pc:view:<id>:<page>."""
    try:
        await callback.answer()
    except Exception:
        pass
    try:
        _, _, id_str, page_str = callback.data.split(":", 3)
        card_id = int(id_str)
        page = int(page_str)
        card = db_v2.get_card_by_id(card_id)
        if not card:
            await callback.message.edit_text("❌ Карточка не найдена.")
            return
        title = card.get('title') or '(без названия)'
        status = card.get('status') or 'pending'
        cat = card.get('category_name') or ''
        discount = card.get('discount_text') or '—'
        address = card.get('address') or '—'
        contact = card.get('contact') or '—'
        text = (
            f"📋 Карточка #{card_id}\n\n"
            f"📝 Название: {title}\n"
            f"📂 Категория: {cat}\n"
            f"⏱ Статус: {status}\n"
            f"🎫 Скидка: {discount}\n"
            f"📍 Адрес: {address}\n"
            f"📞 Контакт: {contact}"
        )
        # Кнопки действий
        act_rows: list[list[InlineKeyboardButton]] = []
        if status in ("published", "approved", "archived"):
            toggle_label = "👁️ Скрыть" if status == "published" else "👁️ Показать"
            act_rows.append([InlineKeyboardButton(text=toggle_label, callback_data=f"pc:toggle:{card_id}:{page}")])
        act_rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"pc:del:{card_id}:{page}")])
        act_rows.append([InlineKeyboardButton(text="↩️ К списку", callback_data=f"pc:page:{page}")])
        kb = InlineKeyboardMarkup(inline_keyboard=act_rows)

        # Попробуем получить все фото карточки и отправить медиагруппу
        try:
            photos = db_v2.get_card_photos(card_id)
        except Exception:
            photos = []

        if photos:
            # Сформируем медиагруппу (до 6 фото)
            media: list[InputMediaPhoto] = []
            for idx, p in enumerate(photos[:6]):
                fid = p.get('file_id') if isinstance(p, dict) else getattr(p, 'file_id', None)
                if not fid:
                    continue
                if idx == 0:
                    media.append(InputMediaPhoto(media=fid, caption=f"{title}"))
                else:
                    media.append(InputMediaPhoto(media=fid))
            # Удалим предыдущее сообщение (если возможно), затем отправим медиагруппу и отдельный текст
            try:
                await callback.message.delete()
            except Exception:
                try:
                    await callback.message.edit_text("📷 Просмотр карточки…")
                except Exception:
                    pass
            try:
                await callback.message.answer_media_group(media)
            except Exception:
                # Фоллбэк: если медиагруппа не прошла, отправим первое фото отдельно
                try:
                    await callback.message.answer_photo(photos[0].get('file_id') if isinstance(photos[0], dict) else getattr(photos[0], 'file_id', None))
                except Exception:
                    pass
            # Затем отправим текст с кнопками
            await callback.message.answer(text, reply_markup=kb)
        else:
            # Фото нет — оставляем прежнее поведение
            await callback.message.edit_text(text, reply_markup=kb)
        logger.info("partner.card_view: user=%s card_id=%s page=%s", callback.from_user.id, card_id, page)
    except Exception as e:
        logger.exception("partner.card_view failed: %s", e)
        await callback.message.answer("❌ Ошибка при открытии карточки.")

@partner_router.callback_query(F.data.startswith("pc:toggle:"))
async def partner_card_toggle(callback: CallbackQuery):
    """Переключение видимости карточки: published <-> archived."""
    try:
        await callback.answer()
    except Exception:
        pass
    try:
        _, _, id_str, page_str = callback.data.split(":", 3)
        card_id = int(id_str)
        page = int(page_str)
        card = db_v2.get_card_by_id(card_id)
        if not card:
            await callback.message.answer("❌ Карточка не найдена.")
            return
        cur = (card.get('status') or 'pending').lower()
        new_status = None
        if cur == 'published':
            new_status = 'archived'
        elif cur in ('approved', 'archived'):
            new_status = 'published'
        else:
            await callback.message.answer("⚠️ Эту карточку пока нельзя публиковать/архивировать (статус не подходит).")
            return
        ok = db_v2.update_card_status(card_id, new_status)
        logger.info("partner.card_toggle: user=%s card_id=%s %s->%s ok=%s", callback.from_user.id, card_id, cur, new_status, ok)
        await _render_cards_page(callback.message, callback.from_user.id, callback.from_user.full_name, page=page, edit=True)
    except Exception as e:
        logger.exception("partner.card_toggle failed: %s", e)
        await callback.message.answer("❌ Ошибка при изменении статуса.")

@partner_router.callback_query(F.data.startswith("pc:del:"))
async def partner_card_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления карточки: pc:del:<id>:<page>."""
    try:
        await callback.answer()
    except Exception:
        pass
    try:
        _, _, id_str, page_str = callback.data.split(":", 3)
        card_id = int(id_str)
        page = int(page_str)
        text = (
            f"❗ Вы уверены, что хотите удалить карточку #{card_id}?\n"
            f"Это действие нельзя отменить."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"pc:del:confirm:{card_id}:{page}")],
            [InlineKeyboardButton(text="↩️ Отмена", callback_data=f"pc:view:{card_id}:{page}")],
        ])
        await callback.message.edit_text(text, reply_markup=kb)
        logger.info("partner.card_delete_confirm: user=%s card_id=%s page=%s", callback.from_user.id, card_id, page)
    except Exception as e:
        logger.exception("partner.card_delete_confirm failed: %s", e)
        await callback.message.answer("❌ Ошибка при подготовке удаления.")

@partner_router.callback_query(F.data.startswith("pc:del:confirm:"))
async def partner_card_delete(callback: CallbackQuery):
    """Удаление карточки после подтверждения."""
    try:
        await callback.answer()
    except Exception:
        pass
    try:
        parts = callback.data.split(":")
        card_id = int(parts[3])
        page = int(parts[4])
        ok = db_v2.delete_card(card_id)
        logger.info("partner.card_delete: user=%s card_id=%s ok=%s", callback.from_user.id, card_id, ok)
        await _render_cards_page(callback.message, callback.from_user.id, callback.from_user.full_name, page=page, edit=True)
    except Exception as e:
        logger.exception("partner.card_delete failed: %s", e)
        await callback.message.answer("❌ Ошибка при удалении карточки.")

# Category selection
@partner_router.callback_query(F.data.startswith("partner_cat:"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection"""
    # Acknowledge callback to stop Telegram's loading state
    try:
        await callback.answer()
    except Exception:
        pass
    category_slug = callback.data.split(":")[1]
    category = db_v2.get_category_by_slug(category_slug)
    
    if not category:
        await callback.answer("❌ Категория не найдена")
        return
    
    await state.update_data(
        category_id=category.id,
        category_name=category.name
    )
    # Если есть подкатегории для данной категории — спросим их сначала
    subcat_kb = get_subcategories_inline(category.slug)
    if subcat_kb is not None:
        await state.set_state(AddCardStates.choose_subcategory)
        await callback.message.edit_text(
            f"✅ Выбрана категория: **{category.name}**\n\n"
            f"Выберите подкатегорию:",
            reply_markup=subcat_kb
        )
        return
    # Иначе сразу переходим к названию
    await state.set_state(AddCardStates.enter_title)
    await callback.message.edit_text(
        f"✅ Выбрана категория: **{category.name}**\n\n"
        f"📝 Теперь введите название вашего заведения:\n"
        f"*(например: \"Ресторан У Моря\")*",
        reply_markup=None
    )
    await callback.message.answer(
        "Введите название:",
        reply_markup=get_cancel_keyboard()
    )

@partner_router.callback_query(F.data.startswith("pfsm:subcat:"))
async def on_subcategory_selected(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split(":")
    val = parts[-1] if parts else "skip"
    if val != "skip" and val.isdigit():
        await state.update_data(subcategory_id=int(val))
    else:
        await state.update_data(subcategory_id=None)
    await state.set_state(AddCardStates.enter_title)
    data = await state.get_data()
    try:
        logger.info(
            "partner.submit_card: user_id=%s photos_count=%s first_photo_present=%s",
            callback.from_user.id,
            len(list(data.get('photos') or [])),
            bool((data.get('photos') or [data.get('photo_file_id')])[0] if (data.get('photos') or data.get('photo_file_id')) else None),
        )
    except Exception:
        pass
    cat_name = data.get('category_name', '')
    await callback.message.edit_text(
        f"✅ Выбрана категория: **{cat_name}**\n\n"
        f"📝 Теперь введите название вашего заведения:\n"
        f"*(например: \"Ресторан У Моря\")*",
        reply_markup=None
    )
    await callback.message.answer(
        "Введите название:",
        reply_markup=get_cancel_keyboard()
    )

# Title input
@partner_router.message(AddCardStates.enter_title, F.text)
async def enter_title(message: Message, state: FSMContext):
    """Handle title input"""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    
    title = message.text.strip()
    ok, err = _validate_title(title)
    if not ok:
        await message.answer(err)
        return
    
    await state.update_data(title=title)
    await state.set_state(AddCardStates.enter_description)
    
    # Основной промпт + reply-клавиатура с отменой
    data = await state.get_data()
    cur_descr = data.get('description')
    base_descr_prompt = (
        f"✅ Название: **{title}**\n\n"
        f"📄 Теперь введите описание заведения:\n"
        f"*(расскажите о ваших услугах, особенностях, атмосфере)*"
    )
    if cur_descr:
        base_descr_prompt += f"\n\nТекущее описание: {cur_descr}"
    await message.answer(base_descr_prompt, reply_markup=get_cancel_keyboard())
    # Inline-кнопка пропуска
    await message.answer("Можно пропустить шаг описания:", reply_markup=get_inline_skip_keyboard())

# Description input
@partner_router.message(AddCardStates.enter_description, F.text)
async def enter_description(message: Message, state: FSMContext):
    """Handle description input"""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    
    description = None
    if message.text != "⏭️ Пропустить":
        description = message.text.strip()
        ok, err = _validate_optional_max_len(description, 500, "❌ Описание слишком длинное. Максимум 500 символов.")
        if not ok:
            await message.answer(err)
            return
    
    await state.update_data(description=description)
    await state.set_state(AddCardStates.enter_contact)
    
    data = await state.get_data()
    cur_contact = data.get('contact')
    contact_prompt = (
        f"📞 Введите контактный телефон партнёра:\n"
        f"Пример: +84 90 123 45 67"
    )
    if cur_contact:
        contact_prompt += f"\n\nТекущий телефон: {cur_contact}"
    await message.answer(contact_prompt, reply_markup=get_cancel_keyboard())

# Contact input
@partner_router.message(AddCardStates.enter_contact, F.text)
async def enter_contact(message: Message, state: FSMContext):
    """Handle contact input (обязателен, телефон)."""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    phone = (message.text or "").strip()
    # Простой валидатор телефона: цифры, +, пробелы, дефисы, скобки, от 7 до 20 символов значащих
    digits = re.sub(r"[^0-9]", "", phone)
    if len(digits) < 7:
        await message.answer("❌ Укажите корректный телефон (минимум 7 цифр). Пример: +84 90 123 45 67")
        return
    ok, err = _validate_optional_max_len(phone, 200, "❌ Контакт слишком длинный. Максимум 200 символов.")
    if not ok:
        await message.answer(err)
        return
    await state.update_data(contact=phone)
    await state.set_state(AddCardStates.enter_address)
    cur_addr = (await state.get_data()).get('address')
    addr_prompt = "📍 Введите адрес (улица, район, номер дома):"
    if cur_addr:
        addr_prompt += f"\n\nТекущий адрес: {cur_addr}"
    await message.answer(addr_prompt, reply_markup=get_cancel_keyboard())

# Address input
@partner_router.message(AddCardStates.enter_address, F.text)
async def enter_address(message: Message, state: FSMContext):
    """Handle address input (требуется)."""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("❌ Адрес слишком короткий. Укажите улицу и номер дома.")
        return
    ok, err = _validate_optional_max_len(address, 300, "❌ Адрес слишком длинный. Максимум 300 символов.")
    if not ok:
        await message.answer(err)
        return
    await state.update_data(address=address)
    # Переходим к обязательной ссылке Google Maps
    await state.set_state(AddCardStates.enter_gmaps)
    await message.answer(
        "🗺️ Вставьте ссылку Google Maps (местоположение заведения):",
        reply_markup=get_cancel_keyboard()
    )

# Google Maps link input
@partner_router.message(AddCardStates.enter_gmaps, F.text)
async def enter_gmaps(message: Message, state: FSMContext):
    """Handle Google Maps link input (обязателен)."""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    url = (message.text or "").strip()
    if not _is_valid_gmaps(url):
        await message.answer("❌ Пожалуйста, отправьте корректную ссылку Google Maps.")
        return
    ok, err = _validate_optional_max_len(url, 200, "❌ Ссылка Google Maps слишком длинная. Максимум 200 символов.")
    if not ok:
        await message.answer(err)
        return
    await state.update_data(google_maps_url=url)
    await state.set_state(AddCardStates.upload_photo)
    try:
        logger.info(
            "partner.enter_gmaps -> upload_photo: user_id=%s current_state=%s",
            message.from_user.id,
            await state.get_state(),
        )
    except Exception:
        pass
    await message.answer(
        "📸 Загрузите фото заведения:\n"
        "*(интерьер, блюда, фасад)*",
        reply_markup=get_photos_reply_keyboard(0, 6)
    )
    await message.answer("Загрузка фото:", reply_markup=get_photos_control_inline(0))

# Photo upload
@partner_router.message(AddCardStates.upload_photo, F.photo)
async def upload_photo(message: Message, state: FSMContext):
    """Загрузка фото: поддержка до 6 фото с управлением."""
    photo_file_id = message.photo[-1].file_id  # наибольшее по размеру
    data = await state.get_data()
    photos = list(data.get('photos') or [])
    try:
        logger.info(
            "partner.upload_photo: user_id=%s got_photo=%s current_count=%s",
            message.from_user.id,
            bool(photo_file_id),
            len(photos),
        )
    except Exception:
        pass
    if len(photos) >= 6:
        # Лимит достигнут — обновим reply-клавиатуру (счётчик) и покажем inline-управление
        await message.answer(
            "ℹ️ Достигнут лимит 6 фото. Нажмите 'Готово' или удалите лишнее.",
            reply_markup=get_photos_reply_keyboard(len(photos), 6)
        )
        await message.answer("Управление фото:", reply_markup=get_photos_control_inline(len(photos)))
        
    else:
        photos.append(photo_file_id)
        await state.update_data(photos=photos)
        try:
            logger.info(
                "partner.upload_photo: user_id=%s appended fid, new_count=%s",
                message.from_user.id,
                len(photos),
            )
        except Exception:
            pass
        if len(photos) < 6:
            # 1) обновим reply-клавиатуру с текущим счётчиком
            await message.answer(
                f"✅ Фото добавлено ({len(photos)}/6). Пришлите ещё фото или нажмите 'Готово'.",
                reply_markup=get_photos_reply_keyboard(len(photos), 6),
            )
            # 2) отдельно покажем inline-управление
            await message.answer("Управление фото:", reply_markup=get_photos_control_inline(len(photos)))
        else:
            # Достигли лимита — сразу предлагаем перейти далее
            await message.answer(
                f"✅ Добавлено 6/6 фото. Нажмите 'Готово' для продолжения.",
                reply_markup=get_photos_reply_keyboard(len(photos), 6),
            )
            await message.answer("Управление фото:", reply_markup=get_photos_control_inline(len(photos)))

@partner_router.message(AddCardStates.upload_photo, F.text)
async def skip_photo(message: Message, state: FSMContext):
    """Handle photo skip"""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return

    # Обработка reply-кнопки "Готово (X/6)"
    if (message.text or "").strip().startswith("✅ Готово"):
        try:
            cur = await state.get_data()
            logger.info(
                "partner.skip_photo: user_id=%s pressed Done, photos_count=%s",
                message.from_user.id,
                len(cur.get('photos') or []),
            )
        except Exception:
            pass
        await state.set_state(AddCardStates.enter_discount)
        await message.answer(
            f"🎫 Введите информацию о скидке:\n"
            f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
            reply_markup=get_cancel_keyboard(),
        )
        await message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())
        return

    if message.text == "⏭️ Пропустить":
        # Пропуск фото — очистить список
        await state.update_data(photos=[] , photo_file_id=None)
        try:
            logger.info(
                "partner.skip_photo: user_id=%s skipped photos, photos_cleared",
                message.from_user.id,
            )
        except Exception:
            pass
        await state.set_state(AddCardStates.enter_discount)
        await message.answer(
            f"🎫 Введите информацию о скидке:\n"
            f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
            reply_markup=get_cancel_keyboard(),
        )
        await message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())
    else:
        await message.answer(
            "📸 Пожалуйста, загрузите фото или нажмите 'Пропустить' / 'Готово'",
            reply_markup=get_photos_reply_keyboard(len((await state.get_data()).get('photos') or []), 6)
        )
        await message.answer(
            "Управление фото:",
            reply_markup=get_photos_control_inline(len((await state.get_data()).get('photos') or []))
        )

# Discount input
@partner_router.message(AddCardStates.enter_discount, F.text)
async def enter_discount(message: Message, state: FSMContext):
    """Handle discount input"""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    
    discount_text = None
    if message.text != "⏭️ Пропустить":
        discount_text = message.text.strip()
        ok, err = _validate_optional_max_len(discount_text, 100, "❌ Описание скидки слишком длинное. Максимум 100 символов.")
        if not ok:
            await message.answer(err)
            return
    
    await state.update_data(discount_text=discount_text)
    await state.set_state(AddCardStates.preview_card)
    
    # Show preview
    data = await state.get_data()
    preview_text = format_card_preview(data, data.get('category_name', ''))
    photos = data.get('photos') or ([] if data.get('photo_file_id') is None else [data.get('photo_file_id')])
    if photos:
        # Показать первое фото с подписью предпросмотра
        await message.answer_photo(
            photo=photos[0],
            caption=preview_text,
            reply_markup=get_preview_keyboard(),
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_preview_keyboard(),
        )

# ===== Inline Skip callback handlers for optional steps =====
@partner_router.callback_query(AddCardStates.enter_description, F.data == "partner_skip")
async def skip_description_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Очистить описание при пропуске
    await state.update_data(description=None)
    await state.set_state(AddCardStates.enter_contact)
    await callback.message.answer(
        f"📞 Введите контактную информацию:\n"
        f"*(телефон, Telegram, WhatsApp, Instagram)*",
        reply_markup=get_cancel_keyboard()
    )
    await callback.message.answer("Можно пропустить контакты:", reply_markup=get_inline_skip_keyboard())

@partner_router.callback_query(AddCardStates.enter_contact, F.data == "partner_skip")
async def skip_contact_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Очистить контакт при пропуске
    await state.update_data(contact=None)
    await state.set_state(AddCardStates.enter_address)
    await callback.message.answer(
        f"📍 Введите адрес заведения:\n"
        f"*(улица, район, ориентиры)*",
        reply_markup=get_cancel_keyboard()
    )
    await callback.message.answer("Можно пропустить адрес:", reply_markup=get_inline_skip_keyboard())

@partner_router.callback_query(AddCardStates.enter_address, F.data == "partner_skip")
async def skip_address_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Очистить адрес при пропуске
    await state.update_data(address=None)
    await state.set_state(AddCardStates.upload_photo)
    await callback.message.answer(
        f"📸 Загрузите фото заведения:\n"
        f"*(интерьер, блюда, фасад)*",
        reply_markup=get_photos_reply_keyboard(0, 6)
    )
    await callback.message.answer("Загрузка фото:", reply_markup=get_photos_control_inline(0))

@partner_router.callback_query(AddCardStates.upload_photo, F.data == "partner_skip")
async def skip_photo_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Очистить фото при пропуске (мультифото)
    await state.update_data(photos=[], photo_file_id=None)
    await state.set_state(AddCardStates.enter_discount)
    await callback.message.answer(
        f"🎫 Введите информацию о скидке:\n"
        f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
        reply_markup=get_cancel_keyboard()
    )
    await callback.message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())

def get_photos_control_inline(current_count: int) -> InlineKeyboardMarkup:
    """Inline-клавиатура управления фото на шаге загрузки (без кнопок Готово/Отменить)."""
    rows: list[list[InlineKeyboardButton]] = []
    if current_count == 0:
        rows.append([InlineKeyboardButton(text="⏭️ Пропустить", callback_data="partner_skip")])
    if current_count > 0:
        rows.append([InlineKeyboardButton(text="🗑 Удалить последнее", callback_data="pfsm:photos:del_last")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

@partner_router.callback_query(AddCardStates.upload_photo, F.data == "pfsm:photos:del_last")
async def on_photos_del_last(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    photos = list(data.get('photos') or [])
    if photos:
        try:
            logger.info(
                "partner.photos_del_last: user_id=%s before_count=%s",
                callback.from_user.id,
                len(photos),
            )
        except Exception:
            pass
        photos.pop()
        await state.update_data(photos=photos)
        try:
            logger.info(
                "partner.photos_del_last: user_id=%s after_count=%s",
                callback.from_user.id,
                len(photos),
            )
        except Exception:
            pass
        await callback.message.answer(
            f"🗑 Удалено. Осталось фото: {len(photos)}/6. Загрузите ещё или нажмите 'Готово'.",
            reply_markup=get_photos_reply_keyboard(len(photos), 6),
        )
        await callback.message.answer("Управление фото:", reply_markup=get_photos_control_inline(len(photos)))
    else:
        await callback.message.answer(
            "Нет загруженных фото. Пришлите фото или нажмите 'Пропустить'.",
            reply_markup=get_photos_reply_keyboard(0, 6),
        )
        await callback.message.answer("Управление фото:", reply_markup=get_photos_control_inline(0))

@partner_router.callback_query(AddCardStates.upload_photo, F.data == "pfsm:photos:done")
async def on_photos_done(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Переход к шагу скидки
    try:
        cur = await state.get_data()
        logger.info(
            "partner.photos_done: user_id=%s photos_count=%s",
            callback.from_user.id,
            len(cur.get('photos') or []),
        )
    except Exception:
        pass
    await state.set_state(AddCardStates.enter_discount)
    await callback.message.answer(
        f"🎫 Введите информацию о скидке:\n"
        f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())

@partner_router.message(AddCardStates.upload_photo, F.document)
async def upload_photo_document(message: Message, state: FSMContext):
    """Загрузка изображений, отправленных как документ (file)."""
    try:
        mt = (getattr(message.document, 'mime_type', None) or '').lower()
    except Exception:
        mt = ''
    if not mt.startswith('image/'):
        try:
            logger.info(
                "partner.upload_photo_document: user_id=%s skipped_non_image mime=%s",
                message.from_user.id,
                mt,
            )
        except Exception:
            pass
        await message.answer(
            "❗ Это не изображение. Пришлите фото или нажмите 'Пропустить'.",
            reply_markup=get_photos_reply_keyboard(len((await state.get_data()).get('photos') or []), 6),
        )
        return
    fid = message.document.file_id
    data = await state.get_data()
    photos = list(data.get('photos') or [])
    try:
        logger.info(
            "partner.upload_photo_document: user_id=%s got_doc_image=%s current_count=%s",
            message.from_user.id,
            bool(fid),
            len(photos),
        )
    except Exception:
        pass
    if len(photos) >= 6:
        await message.answer(
            "ℹ️ Достигнут лимит 6 фото. Нажмите 'Готово'.",
            reply_markup=get_photos_reply_keyboard(len(photos), 6),
        )
        await message.answer("Управление фото:", reply_markup=get_photos_control_inline(len(photos)))
        return
    photos.append(fid)
    await state.update_data(photos=photos, photo_file_id=photos[0] if photos else None)
    try:
        logger.info(
            "partner.upload_photo_document: user_id=%s new_count=%s",
            message.from_user.id,
            len(photos),
        )
    except Exception:
        pass
    await message.answer(
        f"✅ Добавлено фото ({len(photos)}/6). Можете прислать ещё или нажать 'Готово'.",
        reply_markup=get_photos_reply_keyboard(len(photos), 6),
    )
    await message.answer("Управление фото:", reply_markup=get_photos_control_inline(len(photos)))

@partner_router.message(AddCardStates.upload_photo)
async def upload_photo_fallback(message: Message, state: FSMContext):
    """Фоллбек на шаге загрузки фото: логируем неожиданный тип контента для диагностики."""
    try:
        logger.info(
            "partner.upload_photo_fallback: user_id=%s type=%s has_photo=%s has_doc=%s media_group_id=%s",
            message.from_user.id,
            getattr(message, 'content_type', None),
            bool(getattr(message, 'photo', None)),
            bool(getattr(message, 'document', None)),
            getattr(message, 'media_group_id', None),
        )
    except Exception:
        pass
    await message.answer(
        "📸 Пожалуйста, отправьте фото (как изображение) или нажмите 'Пропустить' / 'Готово'.",
        reply_markup=get_photos_reply_keyboard(len((await state.get_data()).get('photos') or []), 6),
    )
    await message.answer(
        "Управление фото:",
        reply_markup=get_photos_control_inline(len((await state.get_data()).get('photos') or [])),
    )

@partner_router.callback_query(AddCardStates.enter_discount, F.data == "partner_skip")
async def skip_discount_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Очистить скидку при пропуске
    await state.update_data(discount_text=None)
    await state.set_state(AddCardStates.preview_card)
    data = await state.get_data()
    preview_text = format_card_preview(data, data.get('category_name', ''))
    await callback.message.answer(preview_text, reply_markup=get_preview_keyboard())

# Submit card
@partner_router.callback_query(F.data == "partner_submit")
async def submit_card(callback: CallbackQuery, state: FSMContext):
    """Submit card for moderation"""
    # Acknowledge callback to prevent UI lag
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    
    try:
        # Create card
        card = Card(
            id=None,
            partner_id=data['partner_id'],
            category_id=data['category_id'],
            title=data['title'],
            description=data.get('description'),
            contact=data.get('contact'),
            address=data.get('address'),
            google_maps_url=data.get('google_maps_url'),
            # Первое фото сохраняем в карточку для обратной совместимости
            photo_file_id=(data.get('photos') or [data.get('photo_file_id')])[0] if (data.get('photos') or data.get('photo_file_id')) else None,
            discount_text=data.get('discount_text'),
            status='pending',  # Waiting for moderation
            priority_level=0,
            subcategory_id=data.get('subcategory_id'),
            city_id=data.get('city_id'),
            area_id=data.get('area_id')
        )
        card_id = db_v2.create_card(card)
        
        # Сохранить все фото в card_photos с позициями
        try:
            photos = list((data.get('photos') or []))
            for idx, fid in enumerate(photos):
                try:
                    db_v2.add_card_photo(int(card_id), str(fid), position=idx)
                except Exception as pe:
                    logger.error("add_card_photo failed: card_id=%s pos=%s err=%s", card_id, idx, pe)
            try:
                logger.info("partner.submit_card: persisted photos for card_id=%s count=%s", card_id, len(photos))
            except Exception:
                pass
        except Exception as e2:
            logger.exception("Failed to persist photos for card_id=%s: %s", card_id, e2)
        
        title = (data.get('title') or '').strip() or '(без названия)'
        await callback.message.edit_text(
            f"✅ **Карточка отправлена на модерацию!**\n\n"
            f"📋 ID: #{card_id}\n"
            f"📝 Название: {title}\n"
            f"⏳ Статус: На рассмотрении\n\n"
            f"💡 Вы получите уведомление, когда модератор рассмотрит вашу карточку.",
            reply_markup=None
        )
        
        # Notify admin about new card
        if settings.features.moderation:
            try:
                bot = callback.bot
                await bot.send_message(
                    settings.bots.admin_id,
                    f"🆕 **Новая карточка на модерацию**\n\n"
                    f"ID: #{card_id}\n"
                    f"Партнер: {callback.from_user.full_name}\n"
                    f"Категория: {data.get('category_name')}\n"
                    f"Название: {data['title']}\n\n"
                    f"Используйте /moderate для просмотра."
                )
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")
        
        await state.clear()

        # After successful submission, restore partner cabinet reply keyboard so UI doesn't disappear.
        try:
            lang = await profile_service.get_lang(callback.from_user.id)
            # ЛК партнёра — показываем партнёрскую клавиатуру с верхней кнопкой QR
            kb = get_partner_keyboard(lang, show_qr=True)
            await callback.message.answer(
                "🏪 Вы в личном кабинете партнёра",
                reply_markup=kb,
            )
        except Exception as e:
            logger.error(f"Failed to restore partner cabinet keyboard: {e}")
        
    except Exception as e:
        logger.error(f"Failed to create card: {e}")
        await callback.answer("❌ Ошибка при создании карточки. Попробуйте позже.")

# Edit card (restart input from title keeping current data)
@partner_router.callback_query(F.data == "partner_edit")
async def edit_card(callback: CallbackQuery, state: FSMContext):
    """Restart editing from title using current state data (non-breaking MVP)."""
    # Acknowledge callback to prevent spinner
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    # Ensure we have at least a category selected
    if not data.get('category_id'):
        await callback.message.edit_text(
            "❌ Нечего редактировать. Пожалуйста, начните заново: /add_card или /add_partner",
            reply_markup=None,
        )
        await state.clear()
        return
    # Move to title entry state; keep existing fields in state for convenience
    await state.set_state(AddCardStates.enter_title)
    # Show current snapshot to guide the user
    cat_name = data.get('category_name', '')
    preview_text = format_card_preview(data, cat_name)
    try:
        await callback.message.edit_text(
            f"✏️ Редактирование карточки\n\n{preview_text}\n\n📝 Текущее название: {data.get('title','(не задано)')}\nВведите новое название (или пришлите текущее ещё раз):",
            reply_markup=None,
        )
    except Exception:
        # Fallback if editing message fails (e.g., was a photo preview)
        await callback.message.answer(
            f"✏️ Редактирование карточки\n\n{preview_text}\n\n📝 Текущее название: {data.get('title','(не задано)')}\nВведите новое название (или пришлите текущее ещё раз):",
        )
    # Provide cancel keyboard
    await callback.message.answer(
        "Введите название:",
        reply_markup=get_cancel_keyboard(),
    )

# Cancel adding card
@partner_router.callback_query(F.data == "partner_cancel")
async def cancel_add_card_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel adding card via callback"""
    # Acknowledge callback to prevent spinner
    try:
        await callback.answer()
    except Exception:
        pass
    await callback.message.edit_text(
        "❌ Добавление карточки отменено.",
        reply_markup=None
    )
    await state.clear()
    # Вернём пользователя в главное меню
    try:
        lang = await profile_service.get_lang(callback.from_user.id)
    except Exception:
        lang = 'ru'
    await callback.message.answer("🏠 Главное меню:", reply_markup=get_main_menu_reply(lang))

# --- Entry points to open Partner Cabinet ---
@partner_router.message(Command("partner"))
async def open_partner_cabinet_cmd(message: Message):
    """Open partner cabinet via /partner command."""
    try:
        # Check if user is a partner
        user_id = message.from_user.id
        partner = await db_v2.get_partner(user_id)
        
        if not partner:
            # If not a partner, show become partner button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=get_text("keyboard.become_partner", message.from_user.language_code or 'ru'),
                    callback_data="become_partner"
                )]
            ])
            await message.answer(
                get_text("partner.not_partner", message.from_user.language_code or 'ru'),
                reply_markup=keyboard
            )
            return
            
        # If partner, show partner cabinet
        await show_partner_cabinet(message, partner)
        
    except Exception as e:
        logger.error(f"Error in open_partner_cabinet_cmd: {e}", exc_info=True)
        await message.answer(
            get_text("error.general", message.from_user.language_code or 'ru'),
            reply_markup=get_return_to_main_menu()
        )

@partner_router.message(F.text.in_(["👤 Кабинет партнера", "👤 Partner Cabinet", "👤 Trang đối tác", "👤 파트너 센тер"]))
async def partner_cabinet_handler(message: Message):
    """Handle partner cabinet button press"""
    try:
        # Get partner data
        user_id = message.from_user.id
        partner = await db_v2.get_partner(user_id)
        
        if not partner:
            await message.answer(
                get_text("partner.not_partner", message.from_user.language_code or 'ru'),
                reply_markup=get_return_to_main_menu()
            )
            return
            
        # Get partner's approved cards count
        approved_cards = await db_v2.get_partner_cards(user_id, status="approved")
        has_approved_cards = len(approved_cards) > 0
        
        # Get partner profile keyboard
        keyboard = get_partner_profile_keyboard(
            {"lang": message.from_user.language_code or 'ru'},
            has_approved_cards
        )
        
        # Format partner info
        partner_info = get_text("cabinet.partner_profile", message.from_user.language_code or 'ru').format(
            approved_cards=len(approved_cards),
            total_views=sum(card.get('views', 0) for card in approved_cards),
            total_scans=sum(card.get('scans', 0) for card in approved_cards)
        )
        
        await message.answer(partner_info, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in partner_cabinet_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error.general", message.from_user.language_code or 'ru'),
            reply_markup=get_return_to_main_menu()
        )

@partner_router.message(F.text.in_(["📊 Статистика", "📊 Statistics", "📊 Thống kê", "📊 통계"]))
@partner_router.callback_query(F.data.startswith("partner:stats"))
async def partner_statistics_handler(update: Union[Message, CallbackQuery], state: FSMContext = None):
    """
    Show detailed partner statistics with period selection
    Handles both command/message and callback query
    """
    try:
        # Get message and user info
        if isinstance(update, CallbackQuery):
            message = update.message
            await update.answer()
            user_id = update.from_user.id
            lang = update.from_user.language_code or 'ru'
        else:
            message = update
            user_id = message.from_user.id
            lang = message.from_user.language_code or 'ru'
        
        # Get partner data
        partner = await db_v2.get_partner(user_id)
        if not partner:
            await message.answer(
                get_text("partner.not_partner", lang),
                reply_markup=get_return_to_main_menu()
            )
            return
        
        # Get period from callback or default to 7 days
        period_days = 7
        if isinstance(update, CallbackQuery) and update.data.startswith("partner:stats:"):
            try:
                period_days = int(update.data.split(":")[2])
            except (IndexError, ValueError):
                pass
        
        # Get statistics data
        stats = await db_v2.get_partner_statistics(
            partner_id=user_id,
            period_days=period_days
        )
        
        # Format statistics message
        stats_text = f"📊 *{get_text('partner.stats_header', lang)}*\n\n"
        
        # Period selector
        periods = [
            (get_text("time.today", lang), 1),
            (get_text("time.week", lang), 7),
            (get_text("time.month", lang), 30),
            (get_text("time.all_time", lang), 0)
        ]
        
        # Period buttons
        period_buttons = []
        for period_name, days in periods:
            if days == period_days:
                period_buttons.append(InlineKeyboardButton(
                    text=f"✅ {period_name}",
                    callback_data=f"partner:stats:{days}"
                ))
            else:
                period_buttons.append(InlineKeyboardButton(
                    text=period_name,
                    callback_data=f"partner:stats:{days}"
                ))
        
        # Cards summary
        stats_text += f"*{get_text('partner.cards_summary', lang)}*\n"
        stats_text += get_text("partner.stats_cards", lang).format(
            total=stats['total_cards'],
            approved=stats['approved_cards'],
            pending=stats['pending_cards'],
            rejected=stats['rejected_cards']
        ) + "\n\n"
        
        # Activity summary
        stats_text += f"*{get_text('partner.activity_summary', lang)}*\n"
        stats_text += get_text("partner.stats_activity", lang).format(
            views=stats['total_views'],
            scans=stats['total_scans'],
            scan_rate=stats['scan_rate']
        ) + "\n\n"
        
        # Top performing cards
        if stats.get('top_cards'):
            stats_text += f"*{get_text('partner.top_cards', lang)}*\n"
            for i, card in enumerate(stats['top_cards'], 1):
                stats_text += (
                    f"{i}. *{escape_markdown(card['title'])}*\n"
                    f"   👁 {card['views']} {get_text('partner.views', lang)} • "
                    f"📱 {card['scans']} {get_text('partner.scans', lang)}\n"
                )
        
        # Add period selection keyboard
        keyboard = [
            period_buttons[:2],  # First row: Today, Week
            period_buttons[2:],  # Second row: Month, All time
            [
                InlineKeyboardButton(
                    text=f"📅 {get_text('partner.export_stats', lang)}",
                    callback_data="partner:export_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("keyboard.back", lang),
                    callback_data="partner:cabinet"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Send or update message
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                stats_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Error in partner_statistics_handler: {e}", exc_info=True)
        error_text = get_text("error.general", lang if 'lang' in locals() else 'ru')
        if isinstance(update, CallbackQuery):
            await update.message.answer(error_text)
        partner = db_v2.get_or_create_partner(message.from_user.id, message.from_user.full_name)
        # Determine if QR should be shown: when partner has at least one card (pending/approved/published)
        show_qr = False
        has_visible = False  # approved/published cards present
        try:
            cards = db_v2.get_partner_cards(partner.id)
            for c in cards:
                status = str(c.get('status'))
                if status in ('pending', 'approved', 'published'):
                    show_qr = True
                    # do not break: also detect if has approved/published
                if status in ('approved', 'published'):
                    has_visible = True
            
        except Exception:
            show_qr = False
            has_visible = False
        # Load language and show correct cabinet
        lang = await profile_service.get_lang(message.from_user.id)
        if not has_visible:
            # Нет видимых карточек у партнёра — показать обычный кабинет пользователя
            await message.answer(get_text('profile_main', lang), reply_markup=get_profile_keyboard(lang))
        else:
            # Партнёрский кабинет с опциональным QR
            kb = get_partner_keyboard(lang, show_qr=show_qr)
            await message.answer("🏪 Вы в личном кабинете партнёра", reply_markup=kb)
    except Exception as e:
        logger.error(f"Failed to open partner cabinet: {e}")


@partner_router.callback_query(F.data.startswith("partner:export:"))
async def export_partner_statistics(callback: CallbackQuery):
    """
    Export partner statistics in the requested format (CSV/Excel)
    """
    try:
        await callback.answer()
        user_id = callback.from_user.id
        lang = callback.from_user.language_code or 'ru'
        
        # Get period from callback data
        try:
            period_days = int(callback.data.split(":")[2])
        except (IndexError, ValueError):
            period_days = 7  # Default to 7 days
        
        # Get partner data
        partner = await db_v2.get_partner(user_id)
        if not partner:
            await callback.message.answer(
                get_text("partner.not_partner", lang),
                reply_markup=get_return_to_main_menu()
            )
            return
        
        # Get statistics data
        stats = await db_v2.get_partner_statistics(
            partner_id=user_id,
            period_days=period_days
        )
        
        # Create CSV data
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow([
            get_text('partner.export_header_date', lang),
            get_text('partner.export_header_views', lang),
            get_text('partner.export_header_scans', lang),
            get_text('partner.export_header_conversion', lang)
        ])
        
        # Write data rows
        for date, day_stats in stats.get('daily_stats', {}).items():
            writer.writerow([
                date,
                day_stats.get('views', 0),
                day_stats.get('scans', 0),
                f"{day_stats.get('conversion_rate', 0):.1f}%"
            ])
        
        # Prepare file for sending
        output.seek(0)
        file_data = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        file_data.name = f"statistics_{period_days}days.csv"
        
        # Send file
        await callback.message.answer_document(
            document=file_data,
            caption=get_text("partner.export_success", lang).format(days=period_days)
        )
        
    except Exception as e:
        logger.error(f"Error exporting partner statistics: {e}", exc_info=True)
        error_text = get_text("error.export_failed", lang if 'lang' in locals() else 'ru')
        if isinstance(callback, CallbackQuery):
            await callback.message.answer(error_text)
        else:
            await callback.answer(error_text, show_alert=True)

@partner_router.message(F.text.startswith("🧑‍💼"))
async def open_partner_cabinet_button(message: Message, state: FSMContext):
    """Become partner button → immediately start add-card wizard (creates partner if missing)."""
    try:
        logger.info(
            "partner.open_button: user_id=%s text=%s partner_fsm=%s",
            message.from_user.id,
            (message.text or "")[:64],
            getattr(settings.features, 'partner_fsm', None),
        )
        # ensure partner exists
        partner = db_v2.get_or_create_partner(message.from_user.id, message.from_user.full_name)
        await state.update_data(partner_id=partner.id)
        # start add card flow right away
        await start_add_card(message, state)
        logger.info("partner.open_button: started add_card flow user_id=%s", message.from_user.id)
    except Exception as e:
        logger.error(f"Failed to start add-card flow via button: {e}")
        await message.answer("❌ Не удалось запустить мастер добавления карточки. Попробуйте позже.")

async def cancel_add_card(message: Message, state: FSMContext):
    """Cancel adding card via message"""
    await message.answer("❌ Добавление карточки отменено.")
    await state.clear()
    # Вернём пользователя в главное меню
    try:
        lang = await profile_service.get_lang(message.from_user.id)
    except Exception:
        lang = 'ru'
    await message.answer("🏠 Главное меню:", reply_markup=get_main_menu_reply(lang))

# Global cancel handler (non-breaking): reacts to '❌ Отменить' only if user is inside AddCardStates
@partner_router.message(F.text.in_(["❌ Отменить", "⛔ Отменить"]))
async def cancel_anywhere(message: Message, state: FSMContext):
    """Allow user to cancel from any AddCardStates step using the same button."""
    cur = await state.get_state()
    # Act only if FSM is currently within AddCardStates to avoid breaking other flows
    if cur and cur.startswith(AddCardStates.__name__ + ":"):
        await cancel_add_card(message, state)

