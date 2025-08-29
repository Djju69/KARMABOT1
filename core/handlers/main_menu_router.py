from aiogram import Bot, F, Router
from aiogram.types import Message

from ..services.profile import profile_service
from ..utils.locales_v2 import translations
from .basic import get_start, on_language_select, open_cabinet, ensure_policy_accepted
from .category_handlers_v2 import (
    show_categories_v2, on_restaurants, on_spa, on_hotels, on_transport, on_tours,
    on_transport_submenu, on_tours_submenu, on_spa_submenu, on_hotels_submenu,
    on_shops, on_shops_submenu,
    handle_profile, show_nearest_v2
)

main_menu_router = Router(name="main_menu_router")


# --- Main Menu ---
@main_menu_router.message(
    F.text.in_(
        [
            # Common user-typed variants to open the main menu (not a button)
            "Меню", "Главное меню",
            "Menu", "Main Menu",
            # Lowercase variants
            "меню", "главное меню", "menu", "main menu",
        ]
    )
)
async def _(message: Message, bot: Bot, state: FSMContext):
    # Force-open the main menu when users type "menu" manually
    await get_start(message, bot, state)

@main_menu_router.message(F.text.in_([t.get('choose_category', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    await show_categories_v2(message, bot, lang)


@main_menu_router.message(F.text.in_([t.get('profile', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    # Use inline cabinet (render_profile via basic.open_cabinet) instead of legacy reply flow
    await open_cabinet(message)


@main_menu_router.message(F.text.in_([t.get('show_nearest', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await show_nearest_v2(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_([t.get('help', '') for t in translations.values()]))
async def _(message: Message):
    if not await ensure_policy_accepted(message):
        return
    await on_help(message)


@main_menu_router.message(F.text.in_([t.get('choose_language', '') for t in translations.values()]))
async def _(message: Message):
    await on_language_select(message)


# --- Category Menu ---
@main_menu_router.message(F.text.in_([t.get('category_restaurants', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_restaurants(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_([t.get('category_spa', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_spa(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_([t.get('category_hotels', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_hotels(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_([t.get('category_transport', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    await on_transport(message, bot, lang)


@main_menu_router.message(F.text.in_([t.get('category_tours', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    await on_tours(message, bot, lang)


@main_menu_router.message(F.text.in_([t.get('category_shops_services', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_shops(message, bot, lang, city_id)


# --- Submenus & Back Buttons ---
@main_menu_router.message(F.text.in_([t.get('back_to_categories', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    await show_categories_v2(message, bot, lang)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['transport_bikes', 'transport_cars', 'transport_bicycles']]
))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_transport_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['tours_group', 'tours_private']]
))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_tours_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['spa_salon', 'spa_massage', 'spa_sauna']]
))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_spa_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['hotels_hotels', 'hotels_apartments']]
))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_hotels_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['shops_shops', 'shops_services']]
))
async def _(message: Message, bot: Bot, lang: str):
    if not await ensure_policy_accepted(message):
        return
    city_id = await profile_service.get_city_id(message.from_user.id)
    await on_shops_submenu(message, bot, lang, city_id)


@main_menu_router.message(F.text.in_([t.get('back_to_main_menu', '') for t in translations.values()]))
async def _(message: Message, bot: Bot, state: FSMContext, lang: str):
    await get_start(message, bot, state)
