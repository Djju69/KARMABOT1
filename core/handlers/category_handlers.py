from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot
from aiogram.fsm.context import FSMContext

from core.keyboards.reply import get_return_to_main_menu
from core.windows.main_menu import main_menu_text
from core.utils.locales import translations
from core.database.db import db  # Импорт базы данных


def get_categories_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    t = translations.get(lang, translations['ru'])
    categories = db.get_categories()  # Ожидается List[Tuple[id, name, emoji]]
    keyboard = []
    row = []

    for i, (_, name, emoji) in enumerate(categories):
        row.append(KeyboardButton(text=f"{emoji} {name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text=t['show_nearest'])])
    keyboard.append([KeyboardButton(text=t['back_to_main'])])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_location_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    t = translations.get(lang, translations['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['send_location'], request_location=True)],
            [KeyboardButton(text=t['back_to_main'])]
        ],
        resize_keyboard=True
    )


async def show_categories(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    t = translations.get(lang, translations['ru'])

    await message.answer(t['choose_category'], reply_markup=get_categories_menu(lang))


async def show_nearest(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    t = translations.get(lang, translations['ru'])

    await message.answer(t['please_send_location'], reply_markup=get_location_keyboard(lang))


async def handle_location(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    t = translations.get(lang, translations['ru'])

    await message.answer(t['thanks_location'])
    keyboard = get_return_to_main_menu(lang)
    await bot.send_message(chat_id=message.chat.id, text=main_menu_text, reply_markup=keyboard)


async def category_selected(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    t = translations.get(lang, translations['ru'])

    category_text = message.text.strip()
    categories = db.get_categories()
    category_id = None
    category_name = None

    for id_, name, emoji in categories:
        full_name = f"{emoji} {name}"
        if category_text == full_name:
            category_id = id_
            category_name = name.lower()
            break

    if not category_id:
        await message.answer(t.get('please_choose_category', 'Пожалуйста, выберите категорию из списка.'))
        return

    if not hasattr(db, 'get_places_by_category_id'):
        await message.answer(t.get('no_places', 'Заведения пока не найдены.'))
        return

    places = db.get_places_by_category_id(category_id)

    if places:
        for place in places:
            await message.answer(f"✅ {place[0]}")
    else:
        if category_name == 'рестораны':
            await message.answer(t.get('restaurants_list', 'Заведения будут добавлены скоро.'))
        elif category_name in ['spa', 'спа', 'spa и массаж']:
            await message.answer(t.get('spa_coming_soon', 'SPA появятся скоро.'))
        elif 'байк' in category_name:
            await message.answer(t.get('bike_rent_soon', 'Аренда байков будет доступна скоро.'))
        elif category_name == 'отели':
            await message.answer(t.get('hotels_soon', 'Отели скоро появятся.'))
        else:
            await message.answer(t.get('no_places', 'Заведения пока не найдены.'))

    keyboard = get_return_to_main_menu(lang)
    await message.answer(main_menu_text, reply_markup=keyboard)
