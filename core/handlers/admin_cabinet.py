"""
Admin cabinet: inline menu and callbacks under adm:* namespace.
Conditioned by FEATURE_MODERATION and admin whitelist (settings.bots.admin_id for MVP).
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
import logging

from ..settings import settings
from ..utils.locales_v2 import get_text
from ..services.profile import profile_service
from ..keyboards.inline_v2 import get_admin_cabinet_inline
from ..keyboards.reply_v2 import get_main_menu_reply
from ..services.admins import admins_service
from ..database.db_v2 import db_v2

logger = logging.getLogger(__name__)

router = Router(name=__name__)

# Simple in-memory rate limit for search (per admin)
_search_last_at: dict[int, float] = {}
import time

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
async def open_admin_cabinet(message: Message):
    """Open admin cabinet if moderation feature is on and user is admin."""
    if not settings.features.moderation:
        await message.answer("🚧 Модуль модерации отключён.")
        return
    if not await admins_service.is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(
        f"{get_text('admin_cabinet_title', lang)}\n\n{get_text('admin_hint_queue', lang)}",
        reply_markup=get_admin_cabinet_inline(lang),
    )


# --- Inline callbacks ---
@router.callback_query(F.data == "adm:back")
async def admin_back(callback: CallbackQuery):
    lang = await profile_service.get_lang(callback.from_user.id)
    await callback.message.edit_text(get_text('main_menu_title', lang))
    await callback.message.answer(get_text('main_menu_title', lang), reply_markup=get_main_menu_reply(lang))
    await callback.answer()


@router.callback_query(F.data == "adm:queue")
async def admin_queue(callback: CallbackQuery):
    if not await admins_service.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    text = f"{get_text('admin_cabinet_title', lang)}\n\n{get_text('admin_hint_queue', lang)}"
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_cabinet_inline(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=get_admin_cabinet_inline(lang))
    await callback.answer()


@router.callback_query(F.data == "adm:search")
async def admin_search(callback: CallbackQuery):
    if not await admins_service.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    text = f"{get_text('admin_cabinet_title', lang)}\n\n{get_text('admin_hint_search', lang)}"
    # Show search filters keyboard
    try:
        await callback.message.edit_text(text, reply_markup=_search_keyboard())
    except Exception:
        await callback.message.answer(text, reply_markup=_search_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("adm:search:status:"))
async def admin_search_by_status(callback: CallbackQuery):
    if not await admins_service.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    if not _search_allowed(callback.from_user.id):
        await callback.answer("⏳ Подождите немного…", show_alert=False)
        return
    status = callback.data.split(":")[-1]
    try:
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
        text = _format_cards_rows(rows)
        await callback.message.edit_text(text, reply_markup=_search_keyboard())
    except Exception as e:
        logger.error(f"admin_search_by_status error: {e}")
        await callback.answer("❌ Ошибка поиска", show_alert=False)


@router.callback_query(F.data == "adm:search:recent")
async def admin_search_recent(callback: CallbackQuery):
    if not await admins_service.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    if not _search_allowed(callback.from_user.id):
        await callback.answer("⏳ Подождите немного…", show_alert=False)
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
        text = _format_cards_rows(rows)
        await callback.message.edit_text(text, reply_markup=_search_keyboard())
    except Exception as e:
        logger.error(f"admin_search_recent error: {e}")
        await callback.answer("❌ Ошибка поиска", show_alert=False)


@router.callback_query(F.data == "adm:reports")
async def admin_reports(callback: CallbackQuery):
    if not await admins_service.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    text = f"{get_text('admin_cabinet_title', lang)}\n\n{get_text('admin_hint_reports', lang)}"
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_cabinet_inline(lang))
    except Exception:
        await callback.message.answer(text, reply_markup=get_admin_cabinet_inline(lang))
    await callback.answer()


def get_admin_cabinet_router() -> Router:
    """Return admin cabinet router (enabled with moderation feature)."""
    if settings.features.moderation:
        return router
    return Router()


# --- Super admin management commands ---
@router.message(Command("admin_add"))
async def cmd_admin_add(message: Message):
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /admin_add <tg_id>")
        return
    target = int(parts[1])
    ok, msg = await admins_service.add_admin(message.from_user.id, target)
    await message.answer(msg)


@router.message(Command("admin_remove"))
async def cmd_admin_remove(message: Message):
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /admin_remove <tg_id>")
        return
    target = int(parts[1])
    ok, msg = await admins_service.remove_admin(message.from_user.id, target)
    await message.answer(msg)


@router.message(Command("admin_list"))
async def cmd_admin_list(message: Message):
    if message.from_user.id != settings.bots.admin_id:
        await message.answer("❌ Только главный админ может смотреть список админов.")
        return
    lst = await admins_service.list_admins()
    text = "👑 Главный админ: %d\n" % settings.bots.admin_id
    others = [x for x in lst if x != settings.bots.admin_id]
    if others:
        text += "👥 Админы: " + ", ".join(str(x) for x in others)
    else:
        text += "👥 Админы: (пусто)"
    await message.answer(text)
