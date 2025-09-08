"""
Admin cabinet: inline menu and callbacks under adm:* namespace.
Conditioned by FEATURE_MODERATION and admin whitelist (settings.bots.admin_id for MVP).
"""
import logging
import logging
import contextlib
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core.settings import settings
from core.utils.locales_v2 import get_text, translations
from core.services import admins_service, profile_service
from core.keyboards.inline_v2 import (
    get_admin_cabinet_inline, 
    get_superadmin_inline, 
    get_superadmin_delete_inline
)
from ..keyboards.reply_v2 import get_main_menu_reply, get_admin_keyboard, get_superadmin_keyboard
from ..database.db_v2 import db_v2

logger = logging.getLogger(__name__)

router = Router(name=__name__)


async def admin_cabinet_handler(message: Message, state: FSMContext):
    """Handle admin cabinet entry point."""
    try:
        user_id = message.from_user.id
        
        # Check if user is admin or super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(user_id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав для доступа к админ-кабинету")
            return
        
        # Show admin cabinet inline menu
        from core.keyboards.inline_v2 import get_admin_cabinet_inline, get_superadmin_inline
        
        if role_name == "super_admin":
            keyboard = get_superadmin_inline()
            text = "👑 <b>Супер-админ панель</b>\n\nВыберите действие:"
        else:
            keyboard = get_admin_cabinet_inline()
            text = "🛡️ <b>Админ панель</b>\n\nВыберите действие:"
        
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in admin_cabinet_handler: {str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при открытии админ-кабинета. Пожалуйста, попробуйте позже.")

# Simple in-memory rate limit for search (per admin)
_search_last_at: dict[int, float] = {}
import time

# Simple anti-spam for superadmin prompt flows
_su_last_at: dict[int, float] = {}

def _su_allowed(user_id: int, window: float = 2.5) -> bool:
    now = time.time()
    last = _su_last_at.get(user_id, 0.0)
    if now - last < window:
        return False
    _su_last_at[user_id] = now
    return True

def _search_allowed(user_id: int, window: float = 2.5) -> bool:
    now = time.time()
    last = _search_last_at.get(user_id, 0.0)
    if now - last < window:
        return False
    _search_last_at[user_id] = now
    return True

def _search_keyboard() -> 'InlineKeyboardMarkup':
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ В очереди", callback_data="adm:search:status:pending"),
         InlineKeyboardButton(text="✅ Опубликованы", callback_data="adm:search:status:published")],
        [InlineKeyboardButton(text="❌ Отклонены", callback_data="adm:search:status:rejected"),
         InlineKeyboardButton(text="🆕 Последние 20", callback_data="adm:search:recent")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:queue")],
    ])

def _queue_nav_keyboard(page: int, has_prev: bool, has_next: bool) -> 'InlineKeyboardMarkup':
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"adm:q:page:{page-1}"))
    row.append(InlineKeyboardButton(text=f"{page+1}", callback_data="noop"))
    if has_next:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"adm:q:page:{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[row, [InlineKeyboardButton(text="🔎 Поиск", callback_data="adm:search")]])

def _build_queue_list_buttons(cards: list[dict], page: int) -> 'InlineKeyboardMarkup':
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows: list[list[InlineKeyboardButton]] = []
    for c in cards:
        cid = int(c.get('id'))
        title = (c.get('title') or '(без названия)')
        rows.append([InlineKeyboardButton(text=f"🔎 #{cid} · {title[:40]}", callback_data=f"adm:q:view:{cid}:{page}")])
    if not rows:
        rows = [[]]
    rows.append([InlineKeyboardButton(text="↩️ К меню", callback_data="adm:queue")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _build_queue_list_text(cards: list[dict], page: int, page_size: int, total: int) -> str:
    start = page * page_size + 1
    end = min((page + 1) * page_size, total)
    lines = [f"🗂️ Очередь модерации: {start}–{end} из {total}"]
    for c in cards:
        lines.append(f"• #{c.get('id')} — {(c.get('title') or '(без названия)')} — {c.get('category_name') or ''}")
    return "\n".join(lines)

async def _render_queue_page(message_or_cbmsg, admin_id: int, page: int, *, edit: bool = False):
    PAGE_SIZE = 5
    logger.info("admin.queue_render: admin=%s page=%s", admin_id, page)
    with db_v2.get_connection() as conn:
        total = int(conn.execute("SELECT COUNT(*) FROM cards_v2 WHERE status = 'pending' ").fetchone()[0])
        offset = max(page, 0) * PAGE_SIZE
        cur = conn.execute(
            """
            SELECT c.id, c.title, cat.name as category_name
            FROM cards_v2 c
            JOIN categories_v2 cat ON c.category_id = cat.id
            WHERE c.status = 'pending'
            ORDER BY c.created_at ASC
            LIMIT ? OFFSET ?
            """,
            (PAGE_SIZE, offset),
        )
        cards = [dict(r) for r in cur.fetchall()]
    has_prev = page > 0
    has_next = (page + 1) * PAGE_SIZE < total
    if total == 0:
        text = "✅ Нет карточек, ожидающих модерации."
        kb = _queue_nav_keyboard(page=0, has_prev=False, has_next=False)
        if edit:
            try:
                await message_or_cbmsg.edit_text(text, reply_markup=kb)
            except Exception:
                await message_or_cbmsg.answer(text, reply_markup=kb)
        else:
            await message_or_cbmsg.answer(text, reply_markup=kb)
        return
    if not cards:
        text = "📭 На этой странице карточек нет."
        kb = _queue_nav_keyboard(page=page, has_prev=has_prev, has_next=has_next)
        if edit:
            try:
                await message_or_cbmsg.edit_text(text, reply_markup=kb)
            except Exception:
                await message_or_cbmsg.answer(text, reply_markup=kb)
        else:
            await message_or_cbmsg.answer(text, reply_markup=kb)
        return
    text = _build_queue_list_text(cards, page=page, page_size=PAGE_SIZE, total=total)
    try:
        if edit:
            await message_or_cbmsg.edit_text(text, reply_markup=_build_queue_list_buttons(cards, page=page))
        else:
            await message_or_cbmsg.answer(text, reply_markup=_build_queue_list_buttons(cards, page=page))
    except Exception:
        await message_or_cbmsg.answer(text, reply_markup=_build_queue_list_buttons(cards, page=page))
    # Навигация отдельным сообщением
    await message_or_cbmsg.answer("Навигация:", reply_markup=_queue_nav_keyboard(page=page, has_prev=has_prev, has_next=has_next))

def _build_card_view_text(card: dict) -> str:
    lines = [f"🔍 Карточка #{card['id']}"]
    lines.append(f"📝 {card.get('title') or '(без названия)'}")
    if card.get('category_name'):
        lines.append(f"📂 {card['category_name']}")
    if card.get('partner_name'):
        lines.append(f"👤 {card['partner_name']}")
    if card.get('description'):
        lines.append(f"📄 {card['description']}")
    if card.get('contact'):
        lines.append(f"📞 {card['contact']}")
    if card.get('address'):
        lines.append(f"📍 {card['address']}")
    if card.get('discount_text'):
        lines.append(f"🎫 {card['discount_text']}")
    return "\n".join(lines)

def _build_card_view_kb(card_id: int, page: int):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm:q:approve:{card_id}:{page}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm:q:reject:{card_id}:{page}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm:q:del:{card_id}:{page}"),
         InlineKeyboardButton(text="↩️ К списку", callback_data=f"adm:q:page:{page}")],
    ])

def _format_cards_rows(rows) -> str:
    lines = ["🔎 Результаты поиска (до 20):"]
    if not rows:
        lines.append("(пусто)")
        return "\n".join(lines)
    for r in rows:
        title = r.get('title') or '(без названия)'
        status = r.get('status') or ''
        cid = r.get('id')
        cat = r.get('category_name') or ''
        lines.append(f"• #{cid} — {title} — {status} — {cat}")
    return "\n".join(lines)


@router.message(Command("admin"))
async def open_admin_cabinet(message: Message, bot: Bot, state: FSMContext):
    """
    Открывает админ-панель, если включена функция модерации и пользователь является администратором.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"open_admin_cabinet called by user {message.from_user.id}")
        logger.info(f"Moderation feature enabled: {settings.features.moderation}")
        
        if not settings.features.moderation:
            logger.warning("Moderation feature is disabled")
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        is_admin = await admins_service.is_admin(message.from_user.id)
        logger.info(f"User {message.from_user.id} is admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        logger.info(f"User language: {lang}")
        
        # Top-level: use Reply keyboard (superadmin has crown in main menu; here use dedicated keyboard)
        is_superadmin = (int(message.from_user.id) == int(settings.bots.admin_id))
        logger.info(f"Is superadmin: {is_superadmin}, admin_id: {settings.bots.admin_id}")
        
        kb = get_superadmin_keyboard(lang) if is_superadmin else get_admin_keyboard(lang)
        
        # Debug: Log the admin_cabinet_title text
        admin_title = get_text('admin_cabinet_title', lang)
        logger.info(f"Admin title text: {admin_title}")
        
        response_text = f"{admin_title}\n\nВыберите раздел:"
        logger.info(f"Full response text: {response_text}")
        
        logger.info(f"Sending response with keyboard: {kb}")
        await message.answer(
            response_text,
            reply_markup=kb,
        )
        logger.info("Response sent successfully")
        
    except Exception as e:
        logger.error(f"Error in open_admin_cabinet: {e}", exc_info=True)
        # Re-raise to see the full traceback in test output
        raise
        await message.answer("❌ Произошла ошибка при открытии админ-панели. Пожалуйста, попробуйте позже.")


# --- Inline callbacks ---
@router.message(F.text == "👑 Админ кабинет")
async def open_admin_cabinet_by_button(message: Message, bot: Bot, state: FSMContext):
    """
    Открывает админ-панель при нажатии на кнопку в основном меню.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        if not await admins_service.is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        kb = get_superadmin_keyboard(lang) if (message.from_user.id == settings.bots.admin_id) else get_admin_keyboard(lang)
        await message.answer(
            f"{get_text('admin_cabinet_title', lang)}\n\nВыберите раздел:",
            reply_markup=kb,
        )
    except Exception as e:
        logger.error(f"Error in open_admin_cabinet_by_button: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при открытии админ-панели. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "adm:back")
async def admin_back(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' в админ-меню."""
    try:
        lang = await profile_service.get_lang(callback.from_user.id)
        await callback.message.edit_text(get_text('main_menu_title', lang))
        await callback.message.answer(
            get_text('main_menu_title', lang), 
            reply_markup=get_main_menu_reply(lang)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in admin_back: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.")

# --- Reply-based admin menu entries ---
@router.message(F.text.in_([t.get('admin_menu_queue', '') for t in translations.values()]))
async def admin_menu_queue_entry(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Обработчик кнопки очереди на модерацию в админ-меню.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        if not await admins_service.is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещён.")
            return
            
        await _render_queue_page(message, message.from_user.id, 0)
    except Exception as e:
        logger.error(f"Error in admin_menu_queue_entry: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при загрузке очереди. Пожалуйста, попробуйте позже.")

@router.message(F.text.in_([t.get('admin_menu_reports', '') for t in translations.values()]))
async def admin_menu_reports_entry(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Обработчик кнопки отчётов в админ-меню.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        if not await admins_service.is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        with db_v2.get_connection() as conn:
            cur = conn.execute("""
                SELECT status, COUNT(*) as cnt
                FROM cards_v2
                GROUP BY status
            """)
            by_status = {row[0] or 'unknown': int(row[1]) for row in cur.fetchall()}

            cur = conn.execute("SELECT COUNT(*) FROM cards_v2")
            total_cards = int(cur.fetchone()[0])

            cur = conn.execute("SELECT COUNT(*) FROM partners_v2")
            total_partners = int(cur.fetchone()[0])

            try:
                cur = conn.execute(
                    """
                    SELECT action, COUNT(*) as cnt
                    FROM moderation_log
                    WHERE created_at >= datetime('now','-7 days')
                    GROUP BY action
                    """
                )
                recent_actions = {row[0]: int(row[1]) for row in cur.fetchall()}
            except Exception:
                recent_actions = {}

        lines = [
            "📊 Отчёты (сводка)",
            f"Всего карточек: {total_cards}",
            f"Всего партнёров: {total_partners}",
            "",
            "По статусам:",
            f"⏳ pending: {by_status.get('pending', 0)}",
            f"✅ published: {by_status.get('published', 0)}",
            f"❌ rejected: {by_status.get('rejected', 0)}",
            f"🗂️ archived: {by_status.get('archived', 0)}",
            f"📝 draft: {by_status.get('draft', 0)}",
        ]
        if recent_actions:
            lines += [
                "",
                "За 7 дней:",
                *[f"• {k}: {v}" for k, v in recent_actions.items()],
            ]
        text = "\n".join(lines)
        # Keep user in reply-based admin menu
        kb = get_superadmin_keyboard(lang) if (message.from_user.id == settings.bots.admin_id) else get_admin_keyboard(lang)
        await message.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error in admin_menu_reports_entry: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при загрузке отчёта. Пожалуйста, попробуйте позже.")

@router.message(F.text.in_([t.get('back_to_main_menu', '') for t in translations.values()]))
async def admin_menu_back_to_main(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Возвращает пользователя в главное меню из админ-панели.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        lang = await profile_service.get_lang(message.from_user.id)
        await message.answer(
            get_text('main_menu_title', lang), 
            reply_markup=get_main_menu_reply(lang)
        )
    except Exception as e:
        logger.error(f"Error in admin_menu_back_to_main: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при возврате в главное меню. Пожалуйста, попробуйте ещё раз.")


@router.callback_query(F.data == "adm:su:del")
async def su_menu_delete(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки удаления в меню суперадмина.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not _is_super_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        lang = await profile_service.get_lang(callback.from_user.id)
        try:
            await callback.message.edit_text(
                "🗑 Удаление: выберите вариант", 
                reply_markup=get_superadmin_delete_inline(lang)
            )
        except Exception:
            await callback.message.answer(
                "🗑 Удаление: выберите вариант", 
                reply_markup=get_superadmin_delete_inline(lang)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in su_menu_delete: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.", show_alert=True)


@router.callback_query(F.data == "adm:queue")
async def admin_queue(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки очереди на модерацию.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        await _render_queue_page(callback.message, callback.from_user.id, page=0, edit=True)
    except Exception as e:
        logger.error(f"Error in admin_queue: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при загрузке очереди. Пожалуйста, попробуйте позже.", show_alert=True)
    finally:
        with contextlib.suppress(Exception):
            await callback.answer()

@router.callback_query(F.data.startswith("adm:q:page:"))
async def admin_queue_page(callback: CallbackQuery) -> None:
    """
    Обработчик пагинации в очереди на модерацию.
    
    Args:
        callback: Callback запрос, содержащий номер страницы
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        try:
            page = int(callback.data.split(":")[3])
            await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid page number in callback data: {callback.data}")
            await callback.answer("❌ Неверный номер страницы", show_alert=True)
        except Exception as e:
            raise e
    except Exception as e:
        logger.error(f"Error in admin_queue_page: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при загрузке страницы. Пожалуйста, попробуйте ещё раз.", show_alert=True)

@router.callback_query(F.data.startswith("adm:q:view:"))
async def admin_queue_view(callback: CallbackQuery) -> None:
    """
    Просмотр деталей карточки в очереди модерации.
    
    Args:
        callback: Callback запрос, содержащий ID карточки и номер страницы
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        try:
            parts = callback.data.split(":")
            if len(parts) < 5:
                raise ValueError("Неверный формат callback данных")
                
            card_id = int(parts[3])
            page = int(parts[4])
            
            card = db_v2.get_card_by_id(card_id)
            if not card:
                await callback.answer("❌ Карточка не найдена", show_alert=True)
                await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
                return
                
            text = _build_card_view_text(card)
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=_build_card_view_kb(card_id, page)
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=_build_card_view_kb(card_id, page)
                )
            
            await callback.answer()
            
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Ошибка формата данных", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in admin_queue_approve: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка при одобрении карточки. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


async def _notify_partner_about_approval(bot: Bot, card_id: int) -> None:
    """Отправляет уведомление партнёру об одобрении карточки."""
    try:
        with db_v2.get_connection() as conn:
            cur = conn.execute("""
                SELECT c.title, p.tg_user_id
                FROM cards_v2 c 
                JOIN partners_v2 p ON c.partner_id = p.id
                WHERE c.id = ?
            """, (card_id,))
            row = cur.fetchone()
            
            if row and row['tg_user_id'] and str(row['tg_user_id']).isdigit():
                try:
                    await bot.send_message(
                        int(row['tg_user_id']), 
                        f"✅ Ваша карточка одобрена!\n#{card_id} — {row['title']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notification to partner {row['tg_user_id']} "
                        f"about approval of card {card_id}: {e}"
                    )
    except Exception as e:
        logger.error(f"Error in _notify_partner_about_approval for card {card_id}: {e}")

@router.callback_query(F.data.startswith("adm:q:del:confirm:"))
async def admin_queue_delete(callback: CallbackQuery) -> None:
    """
    Удаление карточки из очереди модерации после подтверждения.
    
    Args:
        callback: Callback запрос, содержащий ID карточки и номер страницы
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        try:
            parts = callback.data.split(":")
            if len(parts) < 6:
                raise ValueError("Неверный формат callback данных")
                
            card_id = int(parts[4])
            page = int(parts[5])
            
            # Удаляем карточку
            ok = db_v2.delete_card(card_id)
            logger.info(
                "admin.delete: moderator=%s card=%s ok=%s", 
                callback.from_user.id, 
                card_id, 
                ok
            )
            
            # Возвращаемся к очереди
            await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
            await callback.answer("🗑 Карточка удалена", show_alert=False)
            
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Ошибка формата данных", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in admin_queue_delete: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data == "adm:search")
async def admin_search(callback: CallbackQuery) -> None:
    """
    Отображает меню поиска в админ-панели.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        lang = await profile_service.get_lang(callback.from_user.id)
        text = (
            f"{get_text('admin_cabinet_title', lang)}\n\n"
            f"{get_text('admin_hint_search', lang)}"
        )
        
        # Показываем клавиатуру с фильтрами поиска
        try:
            await callback.message.edit_text(
                text, 
                reply_markup=_search_keyboard()
            )
        except Exception as e:
            logger.warning(f"Failed to edit message, sending new one: {e}")
            await callback.message.answer(
                text, 
                reply_markup=_search_keyboard()
            )
            
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin_search: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка при загрузке поиска. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data.startswith("adm:search:status:"))
async def admin_search_by_status(callback: CallbackQuery) -> None:
    """
    Поиск карточек по статусу.
    
    Args:
        callback: Callback запрос, содержащий статус для поиска
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        if not _search_allowed(callback.from_user.id):
            await callback.answer("⏳ Подождите немного перед следующим поиском…", show_alert=False)
            return
            
        try:
            status = callback.data.split(":")[-1]
            if not status:
                raise ValueError("Не указан статус для поиска")
                
            with db_v2.get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT c.id, c.title, c.status, cat.name as category_name
                    FROM cards_v2 c
                    JOIN categories_v2 cat ON c.category_id = cat.id
                    WHERE c.status = ?
                    ORDER BY c.updated_at DESC
                    LIMIT 20
                    """,
                    (status,)
                )
                rows = [dict(r) for r in cur.fetchall()]
                
            if not rows:
                text = f"🔍 Карточек со статусом '{status}' не найдено"
            else:
                text = _format_cards_rows(rows)
                
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=_search_keyboard()
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=_search_keyboard()
                )
                
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in admin_search_by_status: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при выполнении поиска", show_alert=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in admin_search_by_status: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data == "adm:search:recent")
async def admin_search_recent(callback: CallbackQuery) -> None:
    """
    Поиск недавно созданных карточек.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        if not _search_allowed(callback.from_user.id):
            await callback.answer("⏳ Подождите немного перед следующим поиском…", show_alert=False)
            return
            
        try:
            with db_v2.get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT c.id, c.title, c.status, cat.name as category_name
                    FROM cards_v2 c
                    JOIN categories_v2 cat ON c.category_id = cat.id
                    ORDER BY c.created_at DESC
                    LIMIT 20
                    """
                )
                rows = [dict(r) for r in cur.fetchall()]
                
            if not rows:
                text = "🔍 Недавно созданных карточек не найдено"
            else:
                text = _format_cards_rows(rows)
                
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=_search_keyboard()
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=_search_keyboard()
                )
                
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in admin_search_recent: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при выполнении поиска", show_alert=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in admin_search_recent: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data == "adm:reports")
async def admin_reports(callback: CallbackQuery) -> None:
    """
    Показывает отчёт по статистике системы.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        lang = await profile_service.get_lang(callback.from_user.id)
        
        try:
            with db_v2.get_connection() as conn:
                # Cards by status
                cur = conn.execute("""
                    SELECT status, COUNT(*) as cnt
                    FROM cards_v2
                    GROUP BY status
                """)
                by_status = {row[0] or 'unknown': int(row[1]) for row in cur.fetchall()}

                # Totals
                cur = conn.execute("SELECT COUNT(*) FROM cards_v2")
                total_cards = int(cur.fetchone()[0])

                cur = conn.execute("SELECT COUNT(*) FROM partners_v2")
                total_partners = int(cur.fetchone()[0])

                # Recent moderation actions (7 days)
                try:
                    cur = conn.execute(
                        """
                        SELECT action, COUNT(*) as cnt
                        FROM moderation_log
                        WHERE created_at >= datetime('now','-7 days')
                        GROUP BY action
                        """
                    )
                    recent_actions = {row[0]: int(row[1]) for row in cur.fetchall()}
                except Exception as e:
                    logger.warning(f"Failed to get recent actions: {e}")
                    recent_actions = {}

            # Формируем текст отчёта
            lines = [
                "📊 <b>Отчёт по системе</b>",
                "",
                f"<b>Всего карточек:</b> {total_cards}",
                f"<b>Всего партнёров:</b> {total_partners}",
                "",
                "<b>По статусам:</b>",
                f"⏳ Ожидают модерации: {by_status.get('pending', 0)}",
                f"✅ Опубликовано: {by_status.get('published', 0)}",
                f"❌ Отклонено: {by_status.get('rejected', 0)}",
                f"🗂️ В архиве: {by_status.get('archived', 0)}",
                f"📝 Черновики: {by_status.get('draft', 0)}",
            ]
            
            if recent_actions:
                lines += [
                    "",
                    "<b>Действия за 7 дней:</b>",
                    *[f"• {k}: {v}" for k, v in recent_actions.items()],
                ]
                
            text = "\n".join(lines)
            
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=get_admin_cabinet_inline(lang),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=get_admin_cabinet_inline(lang),
                    parse_mode="HTML"
                )
                
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при формировании отчёта", show_alert=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in admin_reports: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


def get_admin_cabinet_router() -> Router:
    """Return admin cabinet router (enabled with moderation feature)."""
    if settings.features.moderation:
        return router
    return Router()


# --- Superadmin inline UI & flows (no slash commands) ---
def _is_super_admin(user_id: int) -> bool:
    return int(user_id) == int(settings.bots.admin_id)


@router.callback_query(F.data == "adm:su")
async def su_menu(callback: CallbackQuery):
    if not _is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text("👑 Суперадмин: выберите действие", reply_markup=get_superadmin_inline(lang))
    except Exception:
        await callback.message.answer("👑 Суперадмин: выберите действие", reply_markup=get_superadmin_inline(lang))
    await callback.answer()


# Simple in-memory state for prompt flows
_su_pending: dict[int, dict] = {}


def _su_set(uid: int, action: str):
    _su_pending[uid] = {"action": action, "ts": time.time()}


def _su_pop(uid: int) -> dict | None:
    return _su_pending.pop(uid, None)


@router.callback_query(F.data.startswith("adm:su:"))
async def su_action(callback: CallbackQuery):
    if not _is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    # Simple anti-spam window for opening prompt
    if not _su_allowed(callback.from_user.id):
        await callback.answer("⏳ Подождите немного…", show_alert=False)
        return
    action = callback.data.split(":", 2)[-1]
    prompts = {
        "ban": "Введите: <tg_id> [причина]",
        "unban": "Введите: <tg_id>",
        "deluser": "Опасно! Введите: <tg_id> ДА",
        "delcard": "Опасно! Введите: <card_id> ДА",
        "delcards_by_tg": "Опасно! Введите: <partner_tg_id> ДА",
        "delallcards": "Опасно! Это удалит ВСЕ карточки. Для подтверждения введите: ДА",
        "addcard": "Введите: <partner_tg_id> <category_slug> <title> [описание]",
    }
    if action not in prompts:
        await callback.answer("Неизвестное действие", show_alert=False)
        return
    _su_set(callback.from_user.id, action)
    await callback.message.answer("✍️ " + prompts[action])
    await callback.answer()


@router.message()
async def su_message_prompt_handler(message: Message):
    # Handle only pending superadmin prompts
    st = _su_pop(message.from_user.id)
    if not st:
        return  # not for us
    if not _is_super_admin(message.from_user.id):
        await message.answer("❌ Только главный админ")
        return
    # Simple anti-spam window for submitting prompt
    if not _su_allowed(message.from_user.id):
        await message.answer("⏳ Подождите немного перед следующей командой…")
        return
    action = st.get("action")
    text = (message.text or "").strip()
    try:
        if action == "ban":
            parts = text.split(maxsplit=1)
            if not parts or not parts[0].isdigit():
                await message.answer("Неверный формат. Ожидается: <tg_id> [причина]")
                return
            uid = int(parts[0])
            reason = parts[1] if len(parts) > 1 else ""
            db_v2.ban_user(uid, reason)
            await message.answer(f"🚫 Забанен: {uid}. {('Причина: '+reason) if reason else ''}")
        elif action == "unban":
            if not text.isdigit():
                await message.answer("Неверный формат. Ожидается: <tg_id>")
                return
            uid = int(text)
            db_v2.unban_user(uid)
            await message.answer(f"✅ Разбанен: {uid}")
        elif action == "deluser":
            parts = text.split()
            if len(parts) < 2 or not parts[0].isdigit() or parts[-1].upper() != "ДА":
                await message.answer("Неверный формат. Ожидается: <tg_id> ДА")
                return
            uid = int(parts[0])
            stats = db_v2.delete_user_cascade_by_tg_id(uid)
            await message.answer(
                "🗑 Удаление пользователя завершено.\n"
                f"partners_v2: {stats.get('partners_v2',0)}, cards_v2: {stats.get('cards_v2',0)}, qr_codes_v2: {stats.get('qr_codes_v2',0)}, moderation_log: {stats.get('moderation_log',0)}\n"
                f"loyalty_wallets: {stats.get('loyalty_wallets',0)}, loy_spend_intents: {stats.get('loy_spend_intents',0)}, user_cards: {stats.get('user_cards',0)}, loyalty_transactions: {stats.get('loyalty_transactions',0)}"
            )
        elif action == "delcard":
            parts = text.split()
            if len(parts) < 2 or not parts[0].isdigit() or parts[-1].upper() != "ДА":
                await message.answer("Неверный формат. Ожидается: <card_id> ДА")
                return
            cid = int(parts[0])
            ok = db_v2.delete_card(cid)
            await message.answer("🗑 Карточка удалена" if ok else "❌ Карточка не найдена")
        elif action == "delcards_by_tg":
            parts = text.split()
            if len(parts) < 2 or not parts[0].isdigit() or parts[-1].upper() != "ДА":
                await message.answer("Неверный формат. Ожидается: <partner_tg_id> ДА")
                return
            pid = int(parts[0])
            n = db_v2.delete_cards_by_partner_tg(pid)
            await message.answer(f"🗑 Удалено карточек: {n}")
        elif action == "delallcards":
            if text.strip().upper() != "ДА":
                await message.answer("Операция отменена. Для подтверждения нужно ввести: ДА")
                return
            n = db_v2.delete_all_cards()
            await message.answer(f"🗑 Удалены ВСЕ карточки. Количество: {n}")
        elif action == "addcard":
            parts = text.split(maxsplit=3)
            if len(parts) < 3 or not parts[0].isdigit():
                await message.answer("Неверный формат. Ожидается: <partner_tg_id> <category_slug> <title> [описание]")
                return
            partner_tg = int(parts[0])
            cat = parts[1]
            title = parts[2]
            desc = parts[3] if len(parts) > 3 else None
            new_id = db_v2.admin_add_card(partner_tg, cat, title, description=desc, status="draft")
            if new_id:
                await message.answer(f"✅ Карточка создана ID={new_id} (draft)")
            else:
                await message.answer("❌ Не удалось создать карточку (проверьте категорию)")
    except Exception as e:
        logger.error(f"su_message_prompt_handler error: {e}")
        await message.answer("❌ Ошибка выполнения действия")
