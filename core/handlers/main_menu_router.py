from aiogram import F, Router
from aiogram.types import Message

from ..utils.locales_v2 import translations
from .category_handlers_v2 import (
    handle_profile,
    on_hotels,
    on_restaurants,
    on_spa,
    on_tours,
    on_tours_submenu,
    on_transport,
    on_transport_submenu,
    show_categories_v2,
    show_nearest_v2,
)
from .basic import on_help, on_language_select

main_menu_router = Router(name="main_menu_router")

# --- Main Menu ---
@main_menu_router.message(F.text.in_([t.get('choose_category', '') for t in translations.values()]))
async def _(message: Message): await show_categories_v2(message)

@main_menu_router.message(F.text.in_([t.get('profile', '') for t in translations.values()]))
async def _(message: Message): await handle_profile(message)

@main_menu_router.message(F.text.in_([t.get('show_nearest', '') for t in translations.values()]))
async def _(message: Message): await show_nearest_v2(message)

@main_menu_router.message(F.text.in_([t.get('help', '') for t in translations.values()]))
async def _(message: Message): await on_help(message)

@main_menu_router.message(F.text.in_([t.get('choose_language', '') for t in translations.values()]))
async def _(message: Message): await on_language_select(message)

# --- Category Menu ---
@main_menu_router.message(F.text.in_([t.get('category_restaurants', '') for t in translations.values()]))
async def _(message: Message): await on_restaurants(message)

@main_menu_router.message(F.text.in_([t.get('category_spa', '') for t in translations.values()]))
async def _(message: Message): await on_spa(message)

@main_menu_router.message(F.text.in_([t.get('category_hotels', '') for t in translations.values()]))
async def _(message: Message): await on_hotels(message)

@main_menu_router.message(F.text.in_([t.get('category_transport', '') for t in translations.values()]))
async def _(message: Message): await on_transport(message)

@main_menu_router.message(F.text.in_([t.get('category_tours', '') for t in translations.values()]))
async def _(message: Message): await on_tours(message)

# --- Submenus & Back Buttons ---
@main_menu_router.message(F.text.in_([t.get('back_to_categories', '') for t in translations.values()]))
async def _(message: Message): await show_categories_v2(message)

@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['transport_bikes', 'transport_cars', 'transport_bicycles']]
))
async def _(message: Message): await on_transport_submenu(message)

@main_menu_router.message(F.text.in_(
    [t.get(k, '') for t in translations.values() for k in ['tours_group', 'tours_private']]
))
async def _(message: Message): await on_tours_submenu(message)

