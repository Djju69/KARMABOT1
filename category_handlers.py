from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot
from core.keyboards.reply import return_to_main_menu
from core.windows.main_menu import main_menu_text

# Клавиатура с категориями
categories_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🍜 Рестораны'), KeyboardButton(text='🧘 SPA и массаж')],
        [KeyboardButton(text='🙵 Аренда байков'), KeyboardButton(text='🏨 Отели')],
        [KeyboardButton(text='📍 Показать ближайшие')],
        [KeyboardButton(text='Вернуться в главное меню🏘')]
    ],
    resize_keyboard=True
)

# Клавиатура с запросом геолокации
send_location_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📍 Отправить геолокацию', request_location=True)],
        [KeyboardButton(text='Вернуться в главное меню🏘')]
    ],
    resize_keyboard=True
)

# Обработчик кнопки "Категории"
async def show_categories(message: Message, bot: Bot):
    await message.answer("Выберите категорию 👇", reply_markup=categories_menu)

# Обработчик кнопки "Показать ближайшие"
async def show_nearest(message: Message, bot: Bot):
    await message.answer("Пожалуйста, отправьте свою геолокацию 🗺", reply_markup=send_location_keyboard)

# Обработчик геолокации
async def handle_location(message: Message, bot: Bot):
    await message.answer("Спасибо! Функция 'Ближайшие заведения' скоро будет доступна 😊")
    await bot.send_message(chat_id=message.chat.id, text=main_menu_text, reply_markup=return_to_main_menu)

# 🚀 Обработчик выбора конкретной категории
async def category_selected(message: Message, bot: Bot):
    category = message.text
    if category == '🍜 Рестораны':
        await message.answer("Вот список ресторанов, участвующих в программе скидок: 🍽️\n\n"
                             "1. Hải sản Mộc quán Nha Trang\n"
                             "2. Test рест\n\n"
                             "Покажите QR-код перед заказом, чтобы получить скидку!")
    elif category == '🧘 SPA и массаж':
        await message.answer("Список салонов SPA и массажей появится совсем скоро 💆‍♀️")
    elif category == '🙵 Аренда байков':
        await message.answer("Сервис аренды байков будет доступен в ближайшее время 🛵")
    elif category == '🏨 Отели':
        await message.answer("Мы работаем над добавлением отелей 🏨")
    else:
        await message.answer("Пожалуйста, выберите категорию из списка.")
