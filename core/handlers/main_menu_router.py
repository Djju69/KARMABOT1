from aiogram import Router, F, Bot
from aiogram.types import Message

from .basic import on_help
from .category_handlers_v2 import show_nearest_v2, handle_profile, show_categories_v2

# Этот роутер имеет высший приоритет для кнопок главного меню
main_menu_router = Router(name='main_menu_router')

# Регистрация обработчиков с явными фильтрами
main_menu_router.message.register(show_categories_v2, F.text == "🗂 Категории")
main_menu_router.message.register(handle_profile, F.text == "👤 Личный кабинет")
main_menu_router.message.register(show_nearest_v2, F.text == "📍 По районам / Рядом")
main_menu_router.message.register(on_help, F.text == "❓ Помощь")
