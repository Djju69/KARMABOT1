"""
Cabinet handlers: personal cabinet inside Telegram (no WebApp)
Provides /cabinet and /my_cards with pagination and simple status toggle
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from typing import List, Tuple

from ..database.db_v2 import db_v2
from ..utils.locales_v2 import get_text, get_all_texts
from ..keyboards.reply_v2 import get_profile_keyboard
from ..keyboards.inline_v2 import get_catalog_item_row, get_pagination_row
from .partner import AddCardStates, get_skip_keyboard, get_categories_keyboard
from ..settings import settings
from ..services.cache import cache_service

router = Router()

PAGE_SIZE = 5


def _build_keyset_nav_row(prefix: str, page_items: List[dict]) -> List[List[InlineKeyboardButton]]:
    """Build keyset prev/next buttons using first/last item cursors.
    Callback format:
      pc:ks:next:<prio>:<id>
      pc:ks:prev:<prio>:<id>
    """
    rows: List[List[InlineKeyboardButton]] = []
    if not page_items:
        return rows
    first = page_items[0]
    last = page_items[-1]
    f_prio, f_id = int(first.get('priority_level', 0)), int(first.get('id'))
    l_prio, l_id = int(last.get('priority_level', 0)), int(last.get('id'))
    rows.append([
        InlineKeyboardButton(text='⬅️ Назад', callback_data=f"{prefix}:ks:prev:{f_prio}:{f_id}"),
        InlineKeyboardButton(text='➡️ Далее', callback_data=f"{prefix}:ks:next:{l_prio}:{l_id}")
    ])
    return rows


def _paginate(items: List[dict], page: int, per_page: int) -> Tuple[List[dict], int, int]:
    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    return items[start:start + per_page], page, pages


def _status_badge(status: str, lang: str) -> str:
    """Map various internal statuses to i18n badge keys per spec.
    Mapping:
      published/approved -> active
      archived/hidden    -> hidden
      pending/draft      -> pending
      rejected           -> rejected
    """
    status = (status or '').lower()
    key_map = {
        'published': 'cabinet.status.active',
        'approved': 'cabinet.status.active',
        'archived': 'cabinet.status.hidden',
        'hidden': 'cabinet.status.hidden',
        'pending': 'cabinet.status.pending',
        'draft': 'cabinet.status.pending',
        'rejected': 'cabinet.status.rejected',
    }
    i18n_key = key_map.get(status, 'cabinet.status.active')
    return get_text(i18n_key, lang)


def _render_partner_cards_full(cards: List[dict], lang: str, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    # Build text
    if not cards:
        text = "📭 Пока нет карточек. Нажмите, чтобы добавить первую."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='➕ Добавить карточку', callback_data='pc:add')]
        ])
        return text, kb

    page_cards, cur, pages = _paginate(cards, page, PAGE_SIZE)

    # Header
    t = get_all_texts(lang)
    header = f"{t.get('my_cards', 'Мои карточки')}: {len(cards)} | {t.get('catalog_page', 'Стр.')} {cur}/{pages}"

    # Body rows
    lines: List[str] = []
    for c in page_cards:
        status = c.get('status', 'draft')
        emoji = _status_badge(status, lang)
        title = c.get('title') or 'Без названия'
        cat = c.get('category_name') or ''
        lines.append(f"{emoji} {title} — {cat} (id:{c.get('id')})")

    text = header + "\n\n" + "\n".join(lines)

    # Inline keyboard: per-card action rows + pagination
    inline_rows: List[List[InlineKeyboardButton]] = []
    for c in page_cards:
        cid = int(c.get('id'))
        gmaps = c.get('google_maps_url')
        # Info + map row (reuse)
        inline_rows.append(get_catalog_item_row(cid, gmaps, lang))
        # Status toggle row
        status = c.get('status', 'draft')
        if status == 'archived':
            next_status = 'published'
            label = get_text('btn_unhide', lang)
        elif status == 'published':
            next_status = 'archived'
            label = get_text('btn_hide', lang)
        else:
            # For other statuses, propose publish
            next_status = 'published'
            label = get_text('btn_publish', lang)
        inline_rows.append([
            InlineKeyboardButton(text=label, callback_data=f"pc:status:{cid}:{next_status}"),
            InlineKeyboardButton(text='✏️ Редактировать', callback_data=f"pc:edit:{cid}")
        ])

    # Add button row (always visible)
    inline_rows.append([InlineKeyboardButton(text='➕ Добавить карточку', callback_data='pc:add')])

    # Pagination row
    inline_rows.append(get_pagination_row('pc', cur, pages, 'all'))

    return text, InlineKeyboardMarkup(inline_keyboard=inline_rows)


async def _render_partner_cards_keyset(partner_id: int, lang: str, after_prio: int | None, after_id: int | None) -> Tuple[str, InlineKeyboardMarkup, List[dict]]:
    """Fetch a keyset page and render text+kb. Returns also items used (for cursors)."""
    items = db_v2.get_partner_cards_keyset_next(partner_id, PAGE_SIZE, after_prio, after_id)
    total = db_v2.count_partner_cards(partner_id)
    t = get_all_texts(lang)
    if not items:
        text = "📭 Пока нет карточек. Нажмите, чтобы добавить первую."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='➕ Добавить карточку', callback_data='pc:add')]])
        return text, kb, items

    # Header without exact page number (keyset): show total and window range
    header = f"{t.get('my_cards', 'Мои карточки')}: {total}"
    lines: List[str] = []
    for c in items:
        status = c.get('status', 'draft')
        emoji = _status_badge(status, lang)
        title = c.get('title') or 'Без названия'
        cat = c.get('category_name') or ''
        lines.append(f"{emoji} {title} — {cat} (id:{c.get('id')})")
    text = header + "\n\n" + "\n".join(lines)

    inline_rows: List[List[InlineKeyboardButton]] = []
    for c in items:
        cid = int(c.get('id'))
        gmaps = c.get('google_maps_url')
        inline_rows.append(get_catalog_item_row(cid, gmaps, lang))
        status = c.get('status', 'draft')
        if status == 'archived':
            next_status = 'published'; label = get_text('btn_unhide', lang)
        elif status == 'published':
            next_status = 'archived'; label = get_text('btn_hide', lang)
        else:
            next_status = 'published'; label = get_text('btn_publish', lang)
        inline_rows.append([
            InlineKeyboardButton(text=label, callback_data=f"pc:status:{cid}:{next_status}"),
            InlineKeyboardButton(text='✏️ Редактировать', callback_data=f"pc:edit:{cid}")
        ])
    inline_rows.append([InlineKeyboardButton(text='➕ Добавить карточку', callback_data='pc:add')])
    inline_rows.extend(_build_keyset_nav_row('pc', items))

    return text, InlineKeyboardMarkup(inline_keyboard=inline_rows), items


@router.message(Command(commands=["cabinet"]))
async def cmd_cabinet(message: Message):
    if not settings.features.partner_fsm:
        await message.answer(
            "🚧 Личный кабинет временно недоступен. Попросите администратора включить partner_fsm.")
        return

    lang = 'ru'  # TODO: fetch from user profile
    partner = db_v2.get_partner_by_tg_id(message.from_user.id)
    t = get_all_texts(lang)

    if not partner:
        # New user welcome
        response = (
            f"👤 **{t.get('profile_main', 'Личный кабинет')}**\n\n"
            "Добро пожаловать! Вы можете:\n\n"
            f"➕ {t.get('add_card', 'Добавить карточку')} — /add_card\n"
            f"📋 {t.get('my_cards', 'Мои карточки')} — /my_cards\n"
            f"📊 {t.get('profile_stats', 'Статистика')}\n\n"
            "Начните с добавления первой карточки командой /add_card"
        )
        await message.answer(response, reply_markup=get_profile_keyboard(lang))
    # Inline entry to partner cabinets (categories)
    if partner:
        await message.answer(
            get_text('my_cabinets', lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text('my_cabinets', lang), callback_data='pc:cabinets')]
            ])
        )
        return

    # Existing partner summary
    cards = db_v2.get_partner_cards(partner.id)
    response = f"👤 **{t.get('profile_main', 'Личный кабинет')}**\n\n"
    response += f"Всего карточек: {len(cards)}\n"
    # Status counts
    counts = {}
    for c in cards:
        s = c.get('status', 'draft')
        counts[s] = counts.get(s, 0) + 1
    if counts:
        response += "\nПо статусам:\n"
        for s, cnt in counts.items():
            emoji = _status_badge(s, lang)
            response += f" • {emoji} {s}: {cnt}\n"

    await message.answer(response, reply_markup=get_profile_keyboard(lang))


@router.message(Command(commands=["my_cards"]))
async def cmd_my_cards(message: Message):
    if not settings.features.partner_fsm:
        await message.answer("🚧 Раздел партнера отключён администратором.")
        return

    lang = 'ru'
    partner = db_v2.get_partner_by_tg_id(message.from_user.id)
    if not partner:
        await message.answer("Сначала добавьте первую карточку: /add_card")
        return

    # Keyset first page with cache 45s
    cache_key = f"cabinet:{partner.id}:ks:first"
    cached = await cache_service.get(cache_key)
    if cached:
        # naive: cached value is not structured; recompute for now to ensure fresh buttons with valid callbacks
        text, kb, _items = await _render_partner_cards_keyset(partner.id, lang, None, None)
    else:
        text, kb, _items = await _render_partner_cards_keyset(partner.id, lang, None, None)
        await cache_service.set(cache_key, "1", 45)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r"^pc:pg:[0-9]+$"))
async def cb_pc_pagination(callback: CallbackQuery):
    try:
        _, _, page_str = callback.data.split(":")
        page = int(page_str)
        lang = 'ru'
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        if not partner:
            await callback.answer("Нет данных", show_alert=False)
            return
        # Backward compat: still support offset pagination if message contains old buttons
        cards = db_v2.get_partner_cards(partner.id)
        text, kb = _render_partner_cards_full(cards, lang, page=page)
        await callback.message.edit_text(text=text, reply_markup=kb)
        await callback.answer()
    except Exception:
        await callback.answer("Ошибка пагинации", show_alert=False)


@router.callback_query(F.data.regexp(r"^pg:pc:all:[0-9]+$"))
async def cb_pc_pagination_alt(callback: CallbackQuery):
    """Alternative handler to support get_pagination_row('pc', ..., 'all').
    Matches pattern: pg:pc:all:<page>
    """
    try:
        _, _, _, page_str = callback.data.split(":")
        page = int(page_str)
        lang = 'ru'
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        if not partner:
            await callback.answer("Нет данных", show_alert=False)
            return
        cards = db_v2.get_partner_cards(partner.id)
        text, kb = _render_partner_cards_full(cards, lang, page=page)
        await callback.message.edit_text(text=text, reply_markup=kb)
        await callback.answer()
    except Exception:
        await callback.answer("Ошибка пагинации", show_alert=False)


@router.callback_query(F.data.regexp(r"^pc:ks:(next|prev):-?[0-9]+:-?[0-9]+$"))
async def cb_pc_keyset(callback: CallbackQuery):
    try:
        _, _, dir_s, prio_s, id_s = callback.data.split(":")
        dir_next = dir_s == 'next'
        lang = 'ru'
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        if not partner:
            await callback.answer("Нет данных", show_alert=False)
            return
        prio = int(prio_s); cid = int(id_s)
        cache_key = f"cabinet:{partner.id}:ks:{dir_s}:{prio}:{cid}"
        cached = await cache_service.get(cache_key)
        # Always recompute content but use cache as throttle flag; set 45s TTL
        after_prio = prio if dir_next else None
        after_id = cid if dir_next else None
        if dir_next:
            text, kb, _items = await _render_partner_cards_keyset(partner.id, lang, after_prio, after_id)
        else:
            items = db_v2.get_partner_cards_keyset_prev(partner.id, PAGE_SIZE, prio, cid)
            if not items:
                text, kb, _ = await _render_partner_cards_keyset(partner.id, lang, None, None)
            else:
                t = get_all_texts(lang)
                header = f"{t.get('my_cards', 'Мои карточки')}: {db_v2.count_partner_cards(partner.id)}"
                lines = []
                for c in items:
                    status = c.get('status', 'draft')
                    emoji = {'draft': '📝','pending':'⏳','published':'✅','rejected':'❌','archived':'🗂️'}.get(status, '📄')
                    title = c.get('title') or 'Без названия'
                    cat = c.get('category_name') or ''
                    lines.append(f"{emoji} {title} — {cat} (id:{c.get('id')})")
                text = header + "\n\n" + "\n".join(lines)
                inline_rows: List[List[InlineKeyboardButton]] = []
                for c in items:
                    cid2 = int(c.get('id'))
                    gmaps = c.get('google_maps_url')
                    inline_rows.append(get_catalog_item_row(cid2, gmaps, lang))
                    status = c.get('status', 'draft')
                    if status == 'archived':
                        next_status = 'published'; label = '♻️ Разархивировать'
                    elif status == 'published':
                        next_status = 'archived'; label = '🗂 Архивировать'
                    else:
                        next_status = 'published'; label = '✅ Опубликовать'
                    inline_rows.append([
                        InlineKeyboardButton(text=label, callback_data=f"pc:status:{cid2}:{next_status}"),
                        InlineKeyboardButton(text='✏️ Редактировать', callback_data=f"pc:edit:{cid2}")
                    ])
                inline_rows.append([InlineKeyboardButton(text='➕ Добавить карточку', callback_data='pc:add')])
                inline_rows.extend(_build_keyset_nav_row('pc', items))
                kb = InlineKeyboardMarkup(inline_keyboard=inline_rows)
        if not cached:
            await cache_service.set(cache_key, "1", 45)
        await callback.message.edit_text(text=text, reply_markup=kb)
        await callback.answer()
    except Exception:
        await callback.answer("Ошибка пагинации", show_alert=False)


@router.callback_query(F.data.regexp(r"^pc:status:[0-9]+:(published|archived)$"))
async def cb_pc_status(callback: CallbackQuery):
    try:
        _, _, id_str, next_status = callback.data.split(":")
        card_id = int(id_str)
        # Update status
        db_v2.update_card_status(card_id, next_status)
        # Invalidate cabinet cache for this partner
        try:
            partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
            if partner:
                await cache_service.delete_by_mask(f"cabinet:{partner.id}:*")
        except Exception:
            pass
        # Repaint same page (assume page hint unavailable -> page 1)
        lang = 'ru'
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        if partner:
            text, kb, _ = await _render_partner_cards_keyset(partner.id, lang, None, None)
        else:
            text, kb = _render_partner_cards_full([], lang, page=1)
        await callback.message.edit_text(text=text, reply_markup=kb)
        await callback.answer("Статус обновлен")
    except Exception:
        await callback.answer("Ошибка изменения статуса", show_alert=True)


@router.callback_query(F.data.regexp(r"^pc:edit:[0-9]+$"))
async def cb_pc_edit(callback: CallbackQuery, state: FSMContext):
    """Start FSM edit flow for a card owned by the partner"""
    try:
        _, _, id_str = callback.data.split(":")
        card_id = int(id_str)
        lang = 'ru'
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        if not partner:
            await callback.answer("Сначала создайте профиль: /add_card", show_alert=True)
            return
        card = db_v2.get_card_by_id(card_id)
        if not card or int(card.get('partner_id')) != int(partner.id):
            await callback.answer("❌ Нет доступа к этой карточке", show_alert=True)
            return

        # Prefill FSM state with existing values
        await state.update_data(
            edit_card_id=card_id,
            partner_id=partner.id,
            category_id=card.get('category_id'),
            category_name=card.get('category_name'),
            title=card.get('title'),
            description=card.get('description'),
            contact=card.get('contact'),
            address=card.get('address'),
            photo_file_id=card.get('photo_file_id'),
            discount_text=card.get('discount_text')
        )

        await state.set_state(AddCardStates.enter_title)
        current_title = card.get('title') or 'Без названия'
        await callback.message.edit_text(
            f"✏️ Режим редактирования карточки #{card_id}\n\n"
            f"Текущее название: **{current_title}**\n\n"
            f"Отправьте новое название или нажмите 'Пропустить', чтобы оставить без изменений.",
            reply_markup=None
        )
        await callback.message.answer(
            "Введите новое название или нажмите '⏭️ Пропустить':",
            reply_markup=get_skip_keyboard()
        )
        await callback.answer()
    except Exception:
        await callback.answer("Ошибка запуска редактирования", show_alert=True)


@router.callback_query(F.data == "pc:add")
async def cb_pc_add(callback: CallbackQuery, state: FSMContext):
    """Start FSM creating a new card from cabinet"""
    if not settings.features.partner_fsm:
        await callback.answer("🚧 Добавление временно недоступно", show_alert=True)
        return
    partner = db_v2.get_or_create_partner(callback.from_user.id, callback.from_user.full_name)
    await state.update_data(partner_id=partner.id)
    # Invalidate cabinet cache for this partner (new item will appear)
    try:
        await cache_service.delete_by_mask(f"cabinet:{partner.id}:*")
    except Exception:
        pass
    await state.set_state(AddCardStates.choose_category)
    await callback.message.edit_text(
        "🏪 **Добавление новой карточки**\n\nВыберите категорию для вашего заведения:",
        reply_markup=None
    )
    await callback.message.answer(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()


# Factory for main include

def get_cabinet_router() -> Router:
    return router


# === Partner cabinets: categories and per-category cabinet (skeleton) ===

@router.callback_query(F.data == 'pc:cabinets')
async def cb_pc_cabinets(callback: CallbackQuery):
    """Show 5 fixed partner categories with i18n labels."""
    lang = 'ru'
    partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
    if not partner:
        await callback.answer("Нет данных", show_alert=False)
        return
    # Fixed 5 categories by slugs
    cats = [
        ("restaurants", get_text('category_restaurants', lang)),
        ("spa", get_text('category_spa', lang)),
        ("transport", get_text('category_transport', lang)),
        ("hotels", get_text('category_hotels', lang)),
        ("tours", get_text('category_tours', lang)),
    ]
    rows: List[List[InlineKeyboardButton]] = []
    for slug, label in cats:
        rows.append([InlineKeyboardButton(text=label, callback_data=f"pc:cab:{slug}")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(get_text('my_cabinets', lang), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^pc:cab:[a-z_]+$"))
async def cb_pc_cabinet_category(callback: CallbackQuery):
    """Open category cabinet skeleton: header, status summary, filtered list 5/pg (offset renderer)."""
    lang = 'ru'
    try:
        _, _, slug = callback.data.split(":")
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        if not partner:
            await callback.answer("Нет данных", show_alert=False)
            return
        # Fetch all partner cards and filter by category_slug if present
        all_cards = db_v2.get_partner_cards(partner.id)
        cards = [c for c in all_cards if (c.get('category_slug') == slug) or (c.get('category_name','').lower() == slug)]
        # Header with status summary
        cat_title_map = {
            'restaurants': get_text('category_restaurants', lang),
            'spa': get_text('category_spa', lang),
            'transport': get_text('category_transport', lang),
            'hotels': get_text('category_hotels', lang),
            'tours': get_text('category_tours', lang),
        }
        title = cat_title_map.get(slug, slug)
        counts: dict[str,int] = {}
        for c in cards:
            s = c.get('status', 'draft')
            counts[s] = counts.get(s, 0) + 1
        summary_lines = []
        for s, cnt in counts.items():
            summary_lines.append(f"{_status_badge(s, lang)} {s}: {cnt}")
        summary = "\n".join(summary_lines)
        header = f"{title}\n{summary}\n\n"
        # Render first page (offset renderer is fine as skeleton)
        text, list_kb = _render_partner_cards_full(cards, lang, page=1)
        # Compose extra controls: metrics, add offer, back
        extra_rows = [
            [InlineKeyboardButton(text=get_text('btn_metrics_category', lang), callback_data=f"pc:metrics:{slug}")],
            [InlineKeyboardButton(text=get_text('btn_add_offer', lang), callback_data='pc:add')],
            [InlineKeyboardButton(text='◀️ Назад', callback_data='pc:cabinets')],
        ]
        merged = list_kb.inline_keyboard + extra_rows
        await callback.message.edit_text(header + text, reply_markup=InlineKeyboardMarkup(inline_keyboard=merged))
        await callback.answer()
    except Exception:
        await callback.answer("Ошибка открытия кабинета", show_alert=False)
