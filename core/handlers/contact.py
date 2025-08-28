from aiogram.types import Message
from aiogram import Bot
from core.handlers.basic import main_menu

async def get_true_contact(message: Message, bot: Bot):
    await message.answer(f'''Вы отправил <b>свой</b> контакт. Мне очень приятно познакомиться!\n 
Но быстрее будет если Вы обратитесь к администрации /feedback''')
    await main_menu(message, bot)

async def get_fake_contact(message: Message, bot: Bot):
    await message.answer(f'''Вы отправил <b>чужой</b> контакт. Я с ним ничего не могу сделать.\n 
А вот Вы можете обратиться к администрации /feedback''')
    await main_menu(message, bot)


