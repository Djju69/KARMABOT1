"""
Partner FSM handlers for adding cards
Behind FEATURE_PARTNER_FSM flag for safe deployment
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
import logging
import re

from ..settings import settings
from ..services.profile import profile_service
from ..keyboards.reply_v2 import (
    get_profile_keyboard,
)
from ..keyboards.inline_v2 import get_cities_inline
from ..database.db_v2 import db_v2, Card
from ..utils.locales_v2 import translations

logger = logging.getLogger(__name__)

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
    choose_category = State()
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
    return txt in ("❌ Отменить", "⛔ Отменить")

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with cancel option"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⛔ Отменить")]],
        resize_keyboard=True
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
    categories = db_v2.get_categories()
    buttons = []
    
    for category in categories:
        buttons.append([InlineKeyboardButton(
            text=f"{category.emoji} {category.name}",
            callback_data=f"partner_cat:{category.slug}"
        )])
    
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
        total = int(conn.execute("SELECT COUNT(*) FROM cards_v2 WHERE partner_id = ?", (partner.id,)).fetchone()[0])
        offset = max(page, 0) * PAGE_SIZE
        cur = conn.execute(
            """
            SELECT c.*, cat.name as category_name
            FROM cards_v2 c
            JOIN categories_v2 cat ON c.category_id = cat.id
            WHERE c.partner_id = ?
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
    
    if card_data.get('photo_file_id'):
        text += f"📸 **Фото:** Прикреплено\n"
    
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
            total = int(conn.execute("SELECT COUNT(*) FROM cards_v2 WHERE partner_id = ?", (db_v2.get_or_create_partner(message.from_user.id, message.from_user.full_name).id,)).fetchone()[0])
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
        # toggle visibility allowed for approved/published/archived
        if status in ("published", "approved", "archived"):
            toggle_label = "👁️ Скрыть" if status == "published" else "👁️ Показать"
            act_rows.append([InlineKeyboardButton(text=toggle_label, callback_data=f"pc:toggle:{card_id}:{page}")])
        # delete
        act_rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"pc:del:{card_id}:{page}")])
        # back
        act_rows.append([InlineKeyboardButton(text="↩️ К списку", callback_data=f"pc:page:{page}")])
        kb = InlineKeyboardMarkup(inline_keyboard=act_rows)
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
    await message.answer(
        "📸 Загрузите фото заведения:\n"
        "*(интерьер, блюда, фасад)*",
        reply_markup=get_cancel_keyboard()
    )
    await message.answer("Можно пропустить фото:", reply_markup=get_inline_skip_keyboard())

# Photo upload
@partner_router.message(AddCardStates.upload_photo, F.photo)
async def upload_photo(message: Message, state: FSMContext):
    """Handle photo upload"""
    photo_file_id = message.photo[-1].file_id  # Get largest photo
    
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(AddCardStates.enter_discount)
    
    data = await state.get_data()
    cur_discount = data.get('discount_text')
    discount_prompt = (
        f"✅ Фото загружено!\n\n"
        f"🎫 Введите информацию о скидке:\n"
        f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*"
    )
    if cur_discount:
        discount_prompt += f"\n\nТекущая скидка: {cur_discount}"
    await message.answer(discount_prompt, reply_markup=get_cancel_keyboard())
    await message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())

@partner_router.message(AddCardStates.upload_photo, F.text)
async def skip_photo(message: Message, state: FSMContext):
    """Handle photo skip"""
    if _is_cancel_text(message.text):
        await cancel_add_card(message, state)
        return
    
    if message.text == "⏭️ Пропустить":
        # Clear photo when skipping via text
        await state.update_data(photo_file_id=None)
        await state.set_state(AddCardStates.enter_discount)
        await message.answer(
            f"🎫 Введите информацию о скидке:\n"
            f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
            reply_markup=get_cancel_keyboard()
        )
        await message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())
    else:
        await message.answer("📸 Пожалуйста, загрузите фото или нажмите 'Пропустить'")

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
    
    if data.get('photo_file_id'):
        await message.answer_photo(
            photo=data['photo_file_id'],
            caption=preview_text,
            reply_markup=get_preview_keyboard()
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_preview_keyboard()
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
        reply_markup=get_cancel_keyboard()
    )
    await callback.message.answer("Можно пропустить фото:", reply_markup=get_inline_skip_keyboard())

@partner_router.callback_query(AddCardStates.upload_photo, F.data == "partner_skip")
async def skip_photo_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    # Очистить фото при пропуске
    await state.update_data(photo_file_id=None)
    await state.set_state(AddCardStates.enter_discount)
    await callback.message.answer(
        f"🎫 Введите информацию о скидке:\n"
        f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
        reply_markup=get_cancel_keyboard()
    )
    await callback.message.answer("Можно пропустить скидку:", reply_markup=get_inline_skip_keyboard())

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
            photo_file_id=data.get('photo_file_id'),
            discount_text=data.get('discount_text'),
            status='pending',  # Waiting for moderation
            # Optional taxonomy/geo
            subcategory_id=data.get('subcategory_id'),
            city_id=data.get('city_id'),
            area_id=data.get('area_id'),
        )
        
        card_id = db_v2.create_card(card)
        
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
                from aiogram import Bot
                bot = Bot.get_current()
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
            # ЛК партнёра — без QR WebApp кнопки
            kb = get_profile_keyboard(lang)
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

# --- Entry points to open Partner Cabinet ---
@partner_router.message(Command("partner"))
async def open_partner_cabinet_cmd(message: Message):
    """Open partner cabinet via /partner command."""
    try:
        # Ensure partner exists
        db_v2.get_or_create_partner(message.from_user.id, message.from_user.full_name)
        # Load language and show partner cabinet keyboard
        lang = await profile_service.get_lang(message.from_user.id)
        kb = get_profile_keyboard(lang)
        await message.answer("🏪 Вы в личном кабинете партнёра", reply_markup=kb)
    except Exception as e:
        logger.error(f"Failed to open partner cabinet: {e}")
        await message.answer("❌ Не удалось открыть кабинет партнёра. Попробуйте позже.")

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

# Global cancel handler (non-breaking): reacts to '❌ Отменить' only if user is inside AddCardStates
@partner_router.message(F.text.in_(["❌ Отменить", "⛔ Отменить"]))
async def cancel_anywhere(message: Message, state: FSMContext):
    """Allow user to cancel from any AddCardStates step using the same button."""
    cur = await state.get_state()
    # Act only if FSM is currently within AddCardStates to avoid breaking other flows
    if cur and cur.startswith(AddCardStates.__name__ + ":"):
        await cancel_add_card(message, state)

# Handle text messages in FSM states
@partner_router.message(AddCardStates.choose_category)
async def invalid_category_input(message: Message):
    """Handle invalid input in category selection"""
    await message.answer("❌ Пожалуйста, выберите категорию из списка выше.")

# Register router only if feature is enabled
def get_partner_router() -> Router:
    """Get partner router if feature is enabled"""
    if settings.features.partner_fsm:
        return partner_router
    return Router()  # Empty router if disabled
