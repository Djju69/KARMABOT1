from aiogram import Router, F
from ..utils.locales_v2 import get_text, get_supported_languages
from .basic import on_help, on_language_select
from .category_handlers_v2 import (
    show_nearest_v2, handle_profile, show_categories_v2,
    on_restaurants, on_spa, on_hotels, on_transport, on_tours,
    on_transport_submenu, on_tours_submenu
)

main_menu_router = Router(name='main_menu_router')

def create_text_filter(*keys: str):
    """Создает фильтр F.text.in_() для всех переводов указанных ключей."""
    all_translations = []
    for key in keys:
        all_translations.extend([get_text(key, lang) for lang in get_supported_languages()])
    return F.text.in_(all_translations)

# --- Главное меню ---
main_menu_router.message.register(show_categories_v2, create_text_filter('choose_category'))
main_menu_router.message.register(handle_profile, create_text_filter('profile'))
main_menu_router.message.register(show_nearest_v2, create_text_filter('show_nearest'))
main_menu_router.message.register(on_help, create_text_filter('help'))
main_menu_router.message.register(on_language_select, create_text_filter('choose_language'))

# --- Меню категорий ---
main_menu_router.message.register(on_restaurants, create_text_filter('category_restaurants'))
main_menu_router.message.register(on_spa, create_text_filter('category_spa'))
main_menu_router.message.register(on_hotels, create_text_filter('category_hotels'))
main_menu_router.message.register(on_transport, create_text_filter('category_transport'))
main_menu_router.message.register(on_tours, create_text_filter('category_tours'))

# --- Подменю и кнопка 'Назад' ---
main_menu_router.message.register(show_categories_v2, create_text_filter('back_to_categories'))
main_menu_router.message.register(on_transport_submenu, create_text_filter('transport_bikes', 'transport_cars', 'transport_bicycles'))
main_menu_router.message.register(on_tours_submenu, create_text_filter('tours_group', 'tours_private'))
