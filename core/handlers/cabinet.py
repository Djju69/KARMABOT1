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
from .partner import AddCardStates, get_skip_keyboard
from ..settings import settings

router = Router()

PAGE_SIZE = 5


def _paginate(items: List[dict], page: int, per_page: int) -> Tuple[List[dict], int, int]:
    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    return items[start:start + per_page], page, pages


def _render_partner_cards(cards: List[dict], lang: str, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    # Build text
    if not cards:
        text = "📭 Пока нет карточек. Используйте /add_card, чтобы добавить первую."
        return text, InlineKeyboardMarkup(inline_keyboard=[])

    page_cards, cur, pages = _paginate(cards, page, PAGE_SIZE)

    # Header
    t = get_all_texts(lang)
    header = f"{t.get('my_cards', 'Мои карточки')}: {len(cards)} | {t.get('catalog_page', 'Стр.')} {cur}/{pages}"

    # Body rows
    lines: List[str] = []
    for c in page_cards:
        status = c.get('status', 'draft')
        emoji = {
            'draft': '📝', 'pending': '⏳', 'published': '✅', 'rejected': '❌', 'archived': '🗂️'
        }.get(status, '📄')
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
            label = '♻️ Разархивировать'
        elif status == 'published':
            next_status = 'archived'
            label = '🗂 Архивировать'
        else:
            # For other statuses, propose publish
            next_status = 'published'
            label = '✅ Опубликовать'
        inline_rows.append([
            InlineKeyboardButton(text=label, callback_data=f"pc:status:{cid}:{next_status}"),
            InlineKeyboardButton(text='✏️ Редактировать', callback_data=f"pc:edit:{cid}")
        ])

    # Pagination row
    inline_rows.append(get_pagination_row('pc', cur, pages, 'all'))

    return text, InlineKeyboardMarkup(inline_keyboard=inline_rows)


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
            emoji = {'draft': '📝','pending':'⏳','published':'✅','rejected':'❌','archived':'🗂️'}.get(s, '📄')
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

    cards = db_v2.get_partner_cards(partner.id)
    text, kb = _render_partner_cards(cards, lang, page=1)
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
        cards = db_v2.get_partner_cards(partner.id)
        text, kb = _render_partner_cards(cards, lang, page=page)
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
        text, kb = _render_partner_cards(cards, lang, page=page)
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
        # Repaint same page (assume page hint unavailable -> page 1)
        lang = 'ru'
        partner = db_v2.get_partner_by_tg_id(callback.from_user.id)
        cards = db_v2.get_partner_cards(partner.id) if partner else []
        text, kb = _render_partner_cards(cards, lang, page=1)
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


# Factory for main include

def get_cabinet_router() -> Router:
    return router
