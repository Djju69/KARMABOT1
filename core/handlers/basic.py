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

router = Router(name=__name__)

# Basic text handlers (minimal implementations)
async def get_start(message: Message):
    from ..keyboards.reply_v2 import get_main_menu_reply
    from ..keyboards.inline_v2 import get_policy_inline
    
    user_id = message.from_user.id
    lang = await profile_service.get_lang(user_id)
    
    # Проверяем, принял ли пользователь политику
    policy_accepted = await profile_service.is_policy_accepted(user_id)
    
    if not policy_accepted:
        # Формируем приветственное сообщение с именем пользователя
        welcome_text = get_text('welcome_message', lang).format(
            user_name=message.from_user.first_name
        )
        
        # Отправляем приветственное сообщение с кнопками
        await message.answer(
            text=welcome_text,
            reply_markup=get_policy_inline(lang),
            parse_mode='HTML'
        )
    else:
        # Если политика уже принята, показываем главное меню
        await message.answer(
            text=get_text('main_menu_title', lang),
            reply_markup=get_main_menu_reply(lang)
        )


async def main_menu(message: Message):
    from ..keyboards.reply_v2 import get_main_menu_reply
    lang = await profile_service.get_lang(message.from_user.id)
    await message.answer(
        get_text('main_menu_title', lang),
        reply_markup=get_main_menu_reply(lang)
    )


# ==== Language & Help (Phase 1) ====


async def on_language_select(message: Message):
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
    await callback.message.edit_text(
        get_text('choose_language', lang)
    )
    await callback.message.edit_reply_markup(reply_markup=get_language_inline(active=lang))
    await callback.answer(get_text('language_updated', lang))

# Backward-compatible alias expected by older imports
async def language_callback(callback: CallbackQuery):
    return await on_language_set(callback)


async def on_help(message: Message):
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


# ==== City selection & Policy acceptance (Phase 1) ====
async def on_city_menu(message: Message):
    lang = await profile_service.get_lang(message.from_user.id)
    active = await profile_service.get_city_id(message.from_user.id)
    await message.answer(get_text('choose_city', lang), reply_markup=get_cities_inline(active_id=active))


@router.callback_query(F.data.regexp(r"^city:set:[0-9]+$"))
async def on_city_set(callback: CallbackQuery):
    lang = await profile_service.get_lang(callback.from_user.id)
    _, _, id_str = callback.data.split(":")
    active = int(id_str)
    await profile_service.set_city_id(callback.from_user.id, active)
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

    # Подтверждаем действие
    await callback.answer(get_text('policy_accepted', lang))

    # Удаляем сообщение с инлайн-клавиатурой и показываем главное меню
    await callback.message.delete()
    await callback.message.answer(
        get_text('main_menu_title', lang),
        reply_markup=get_main_menu_reply(lang)
    )

# Register defaults to router to ensure availability
router.message.register(get_start, CommandStart())
router.message.register(main_menu, Command("menu"))

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
