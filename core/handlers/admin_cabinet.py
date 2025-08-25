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
from ..keyboards.inline_v2 import get_admin_cabinet_inline, get_superadmin_inline, get_superadmin_delete_inline
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
        reply_markup=get_admin_cabinet_inline(lang, is_superadmin=(message.from_user.id == settings.bots.admin_id)),
    )


# --- Inline callbacks ---
@router.message(F.text == "👑 Админ кабинет")
async def open_admin_cabinet_by_button(message: Message):
    if not settings.features.moderation:
        await message.answer("🚧 Модуль модерации отключён.")
        return
    if not await admins_service.is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(
        f"{get_text('admin_cabinet_title', lang)}\n\n{get_text('admin_hint_queue', lang)}",
        reply_markup=get_admin_cabinet_inline(lang, is_superadmin=(message.from_user.id == settings.bots.admin_id)),
    )

@router.callback_query(F.data == "adm:back")
async def admin_back(callback: CallbackQuery):
    lang = await profile_service.get_lang(callback.from_user.id)
    await callback.message.edit_text(get_text('main_menu_title', lang))
    await callback.message.answer(get_text('main_menu_title', lang), reply_markup=get_main_menu_reply(lang))
    await callback.answer()


@router.callback_query(F.data == "adm:su:del")
async def su_menu_delete(callback: CallbackQuery):
    if not _is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text("🗑 Удаление: выберите вариант", reply_markup=get_superadmin_delete_inline(lang))
    except Exception:
        await callback.message.answer("🗑 Удаление: выберите вариант", reply_markup=get_superadmin_delete_inline(lang))
    await callback.answer()


@router.callback_query(F.data == "adm:queue")
async def admin_queue(callback: CallbackQuery):
    if not await admins_service.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    text = f"{get_text('admin_cabinet_title', lang)}\n\n{get_text('admin_hint_queue', lang)}"
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_cabinet_inline(lang, is_superadmin=(callback.from_user.id == settings.bots.admin_id)))
    except Exception:
        await callback.message.answer(text, reply_markup=get_admin_cabinet_inline(lang, is_superadmin=(callback.from_user.id == settings.bots.admin_id)))
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
