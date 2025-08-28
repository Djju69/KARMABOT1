from aiogram.types import Message, InputFile
from aiogram import Bot, types
from core.windows.qr import qr_code_check
import json
from core.keyboards.inline import discount_generator
from core.windows.qr import generate_qrcode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


text_2_10_1 = f'''Это великолепный ресторан!
        <a href="https://maps.app.goo.gl/2S4DrWRXmBr39gsz8?g_st=ic">👉находится тут👈</a>
Для подтверждения и получения скидки, покажите QR-код официанту <b>ПЕРЕД</b> тем, как сделаете заказ!'''

photo_2_10_1 = 'https://nhatrang.ucoz.net/photo_2_10_1.jpg'

text_2_10_1_1 = f'''Это второй этап'''

photo_2_10_1_1= f'''https://nhatrang.ucoz.net/bez_nazvanija.jpeg'''

# async def restoran_2_10_1(callback_query: types.CallbackQuery, bot: Bot):
#     await bot.answer_callback_query(callback_query.id)
#     await bot.send_photo(callback_query.message.chat.id, photo=photo_2_10_1)
#     await bot.send_message(callback_query.message.chat.id, text=text_2_10_1, disable_web_page_preview=True)
#     await generate_qrcode(callback_query.message, bot)

async def restoran_2_10_1_0(callback_query: types.CallbackQuery, bot: Bot):
    data_rest = {"rest_data": "2_10_1_0"}
    await bot.answer_callback_query(callback_query.id)
    await bot.send_photo(
        callback_query.message.chat.id,
        photo=photo_2_10_1,
        caption=text_2_10_1,
    )
    await qr_code_check(callback_query.message, bot, data_rest["rest_data"])


async def restoran_2_10_1_1(callback_query: types.CallbackQuery, bot: Bot):
    data_rest = {"rest_data": "2_10_1_1"}
    callback_data = json.dumps(data_rest)
    await bot.answer_callback_query(callback_query.id)

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="Нажмите здесь",
                callback_data=callback_data
            )
        ]
    ])

    await bot.send_photo(
        callback_query.message.chat.id,
        photo=photo_2_10_1_1,
        caption=text_2_10_1_1,
        reply_markup=keyboard
    )
    print(callback_data)

async def qr_code_postman(callback_query: types.CallbackQuery):
    data_rest_encoded = callback_query.data
    data_rest = json.loads(data_rest_encoded)
    await qr_code_check(callback_query.message, callback_query.bot, data_rest)