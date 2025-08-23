from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from ..keyboards.inline_v2 import (
    get_language_inline,
    get_cities_inline,
    get_policy_inline,
)
from ..utils.locales_v2 import get_text
from ..settings import settings
from ..services.profile import profile_service
from ..utils.telemetry import log_event

router = Router(name=__name__)

# Basic text handlers (minimal implementations)
async def _send_welcome_with_policy(message: Message):
    from ..keyboards.inline_v2 import get_policy_inline
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    welcome_text = get_text('welcome_message', lang).format(
        user_name=message.from_user.first_name
    )
    await message.answer(text=welcome_text, reply_markup=get_policy_inline(lang), parse_mode='HTML')


async def ensure_policy_accepted(message: Message) -> bool:
    """Return True if policy accepted. Otherwise send welcome and return False."""
    user_id = message.from_user.id
    if not await profile_service.is_policy_accepted(user_id):
        await log_event("policy_gate_blocked", user=message.from_user, command=getattr(message, 'text', None))
        await _send_welcome_with_policy(message)
        return False
    return True
async def get_start(message: Message):
    from ..keyboards.reply_v2 import get_main_menu_reply
    from ..keyboards.inline_v2 import get_policy_inline
    
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    
    # Проверяем, принял ли пользователь политику
    policy_accepted = await profile_service.is_policy_accepted(user_id)
    
    if not policy_accepted:
        # Если язык ещё не выбран явно — сперва показываем выбор языка
        if not await profile_service.has_lang(user_id):
            await log_event("language_prompt", user=message.from_user)
            await message.answer(
                get_text('choose_language', lang),
                reply_markup=get_language_inline(active=lang)
            )
            return
        # Формируем приветственное сообщение с именем пользователя
        welcome_text = get_text('welcome_message', lang).format(
            user_name=message.from_user.first_name
        )
        
        # Отправляем приветственное сообщение с кнопками
        await log_event("welcome_shown", user=message.from_user, reason="policy_not_accepted")
        await message.answer(
            text=welcome_text,
            reply_markup=get_policy_inline(lang),
            parse_mode='HTML'
        )
    else:
        # Если политика уже принята, показываем главное меню
        await log_event("main_menu_opened", user=message.from_user)
        # Веб-версия доступна только через командное меню /webapp
        reply_kb = get_main_menu_reply(lang)
        await message.answer(
            text=get_text('main_menu_title', lang),
            reply_markup=reply_kb
        )


async def main_menu(message: Message):
    from ..keyboards.reply_v2 import get_main_menu_reply
    if not await ensure_policy_accepted(message):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    await log_event("main_menu_opened", user=message.from_user)
    # Веб-версия доступна только через командное меню /webapp
    reply_kb = get_main_menu_reply(lang)
    await message.answer(get_text('main_menu_title', lang), reply_markup=reply_kb)


# ==== Language & Help (Phase 1) ====


async def on_language_select(message: Message):
    if not await ensure_policy_accepted(message):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(
        get_text('choose_language', lang),
        reply_markup=get_language_inline(active=lang)
    )


@router.callback_query(F.data.regexp(r"^lang:set:(ru|en|vi|ko)$"))
async def on_language_set(callback: CallbackQuery):
    # TODO: сохранить язык в профиле пользователя (Redis/DB)
    _, _, lang = callback.data.split(":")
    await profile_service.set_lang(callback.from_user.id, lang)
    await log_event("language_set", user=callback.from_user, lang=lang)
    # После выбора языка: если политика не принята — отправляем приветствие с согласием
    if not await profile_service.is_policy_accepted(callback.from_user.id):
        try:
            await callback.message.delete()
        except Exception:
            pass
        welcome_text = get_text('welcome_message', lang).format(
            user_name=callback.from_user.first_name
        )
        await callback.message.answer(
            welcome_text,
            reply_markup=get_policy_inline(lang),
            parse_mode='HTML'
        )
    else:
        # Если политика уже принята — сразу обновим главное меню (ReplyKeyboard) и уведомим пользователя
        try:
            await callback.message.delete()
        except Exception:
            pass
        from ..keyboards.reply_v2 import get_main_menu_reply
        await callback.message.answer(
            get_text('main_menu_title', lang),
            reply_markup=get_main_menu_reply(lang)
        )
        await callback.answer(get_text('language_updated', lang))

# Backward-compatible alias expected by older imports
async def language_callback(callback: CallbackQuery):
    return await on_language_set(callback)


async def on_help(message: Message):
    if not await ensure_policy_accepted(message):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    help_text = get_text('help_main', lang)

    # Append docs/support if available
    pdf_user = getattr(settings, f'pdf_user_{lang}', '')
    pdf_partner = getattr(settings, f'pdf_partner_{lang}', '')
    support = getattr(settings, 'support_tg', '')

    extras = []
    if pdf_user:
        extras.append(f"📄 User PDF: {pdf_user}")
    if pdf_partner:
        extras.append(f"📄 Partner PDF: {pdf_partner}")
    if support:
        extras.append(f"🆘 Support: {support}")

    text = help_text + ("\n\n" + "\n".join(extras) if extras else "")
    await message.answer(text)


async def on_webapp(message: Message):
    """Открыть веб-версию (WebApp) — отправляет ссылку на WebApp."""
    if not await ensure_policy_accepted(message):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    url = getattr(settings, 'webapp_qr_url', '') or ''
    if not url:
        await message.answer(get_text('scan_qr_unavailable', lang))
        return
    # Покажем инлайн-кнопку, открывающую WebApp через WebAppInfo. Доступно только через команду /webapp.
    from ..keyboards.inline_v2 import get_webapp_inline
    await message.answer(get_text('main_menu_title', lang), reply_markup=get_webapp_inline(url, lang))


async def on_profile(message: Message):
    """Показывает информацию профиля пользователя: язык, город, статус политики."""
    if not await ensure_policy_accepted(message):
        return
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    city_id = await profile_service.get_city_id(user_id)
    policy = await profile_service.is_policy_accepted(user_id)
    city_txt = str(city_id) if city_id is not None else "—"
    policy_txt = "✅" if policy else "❌"
    text = (
        f"👤 Профиль\n"
        f"• Язык: {lang}\n"
        f"• Город ID: {city_txt}\n"
        f"• Политика: {policy_txt}"
    )
    await message.answer(text)


async def on_policy_command(message: Message):
    """Отправляет ссылку на политику конфиденциальности."""
    # Блокируем до принятия политики: разрешён только /start и inline-кнопка
    if not await ensure_policy_accepted(message):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    await log_event("policy_command", user=message.from_user, lang=lang)
    url = get_text('policy_url', lang)
    await message.answer(f"📄 Политика конфиденциальности:\n{url}")


async def on_add_partner(message: Message):
    """Точка входа для партнёра. Если FSM включена — подсказка на /add_card."""
    if not await ensure_policy_accepted(message):
        return
    if getattr(settings.features, 'partner_fsm', False):
        await message.answer("🏪 Добавить партнёра: используйте команду /add_card")
    else:
        await message.answer("🚧 Добавление партнёров временно недоступно.")


async def on_clear_cache(message: Message):
    """Очистка кэша профилей (только админ)."""
    if not await ensure_policy_accepted(message):
        return
    if message.from_user.id != settings.bots.admin_id:
        await message.answer("❌ Доступ запрещён.")
        return
    await profile_service.clear_cache()
    await message.answer("🧹 Кэш профилей очищен.")


async def on_partner_on(message: Message):
    """Admin: mark current user as active partner (enables QR button)."""
    if message.from_user.id != settings.bots.admin_id:
        await message.answer("❌ Доступ запрещён.")
        return
    await profile_service.set_partner_active(message.from_user.id, True)
    await message.answer("✅ partner_active = true")


async def on_partner_off(message: Message):
    """Admin: mark current user as NOT active partner (disables QR button)."""
    if message.from_user.id != settings.bots.admin_id:
        await message.answer("❌ Доступ запрещён.")
        return
    await profile_service.set_partner_active(message.from_user.id, False)
    await message.answer("✅ partner_active = false")


# ==== City selection & Policy acceptance (Phase 1) ====
async def on_city_menu(message: Message):
    if not await ensure_policy_accepted(message):
        return
    lang = await profile_service.get_lang(message.from_user.id)
    active = await profile_service.get_city_id(message.from_user.id)
    await message.answer(get_text('choose_city', lang), reply_markup=get_cities_inline(active_id=active))


@router.callback_query(F.data.regexp(r"^city:set:[0-9]+$"))
async def on_city_set(callback: CallbackQuery):
    lang = await profile_service.get_lang(callback.from_user.id)
    _, _, id_str = callback.data.split(":")
    active = int(id_str)
    await profile_service.set_city_id(callback.from_user.id, active)
    await log_event("city_set", user=callback.from_user, city_id=active)
    await callback.message.edit_text(get_text('city_selected', lang))
    await callback.message.edit_reply_markup(reply_markup=get_cities_inline(active_id=active))
    await callback.answer(get_text('city_updated', lang))


@router.callback_query(F.data == "policy:accept")
async def on_policy_accept(callback: CallbackQuery):
    from ..keyboards.reply_v2 import get_main_menu_reply
    user_id = callback.from_user.id
    lang = await profile_service.get_lang(user_id)

    # Отмечаем, что политика принята
    await profile_service.set_policy_accepted(user_id, True)
    await log_event("policy_accepted", user=callback.from_user, lang=lang)

    # Подтверждаем действие
    await callback.answer(get_text('policy_accepted', lang))

    # Удаляем сообщение с инлайн-клавиатурой и показываем главное меню
    await callback.message.delete()
    # Веб-версия доступна только через командное меню /webapp
    reply_kb = get_main_menu_reply(lang)
    await callback.message.answer(
        get_text('main_menu_title', lang),
        reply_markup=reply_kb
    )

# Register defaults to router to ensure availability
router.message.register(get_start, CommandStart())
router.message.register(main_menu, Command("menu"))
router.message.register(on_help, Command("help"))
router.message.register(on_profile, Command("profile"))
router.message.register(on_webapp, Command("webapp"))
router.message.register(on_add_partner, Command("add_partner"))
router.message.register(on_city_menu, Command("city"))
router.message.register(on_policy_command, Command("policy"))
router.message.register(on_clear_cache, Command("clear_cache"))
router.message.register(on_partner_on, Command("partner_on"))
router.message.register(on_partner_off, Command("partner_off"))

# Open language selection when user taps the reply button (e.g., "🌐 Язык")
# We match by leading globe emoji to avoid hardcoding per-language labels.
router.message.register(on_language_select, F.text.startswith("🌐"))

# Fallback for any other text messages
@router.message(F.text)
async def on_unhandled_message(message: Message):
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(get_text('unhandled_message', lang))

__all__ = [
    "router",
    "get_start", "main_menu",
    "on_language_select", "on_language_set", "language_callback", "on_help",
    "on_city_menu", "on_city_set", "on_policy_accept",
]
