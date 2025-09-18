import datetime 
import segno
import json
import asyncio
import gspread
from aiogram import types, Bot
from aiogram.types import Message, BufferedInputFile
from datetime import timezone, timedelta, datetime
from core.keyboards.reply_v2 import get_return_to_main_menu  # Исправлено здесь
from urllib.parse import urlencode
from qrcode_artistic import write_artistic

SHEET_ID = "1jBRhdrrZBGuIq5zaeTwHPWslMYmT7hypFNYPBGUM48E"
WORKSHEET_NAME = "1"

# Попытка подключиться к Google Sheets
try:
    gc = gspread.service_account(filename='mythic-brook-414011-6b6b807faea2.json')
    sheet = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
except Exception as e:
    print(f"[!] Google Sheets отключён: {e}")
    sheet = None


async def qr_code_check(message: types.Message, bot: Bot, data_rest):
    data_parts = data_rest.split('_')

    if len(data_parts) == 4:
        last_digit = int(data_parts[-1])

        if last_digit == 1:
            await message.answer("Последняя цифра равна 1")
        elif last_digit == 0:
            await generate_qrcode(message, bot, data_rest)
        else:
            await message.answer("Последняя цифра не равна ни 0, ни 1")
    else:
        await message.answer("Неправильный формат данных")


async def generate_qrcode(message: types.Message, bot: Bot, data_rest):
    user_id = message.chat.id
    now_gmt7 = datetime.now(timezone(timedelta(hours=7)))
    date_time = now_gmt7.strftime("%Y-%m-%d %H:%M:%S")
    date, time = date_time.split(" ")
    discount = int(5)
    restoran_id = data_rest

    data = {
        "url": "https://nhatrang.ucoz.net/index/test_menu/0-4",
        "date": date,
        "user_id": message.chat.id,
        "discount": discount,
        "restoran_id": restoran_id
    }

    encoded_data = urlencode(data)
    qr_code_url = f"{data['url']}?{encoded_data}"

    background_image = "/Users/trizory/Desktop/Python/Igortestbot/venv/core/photo/Nha Trang.png"

    qrcode = segno.make(qr_code_url, error='H', version=13)
    qrcode.save('qrcode.png', dark='black', light='white', scale=3)

    with open('qrcode.png', 'rb') as image_file:
        image_data = image_file.read()

    photo = BufferedInputFile(image_data, filename='qrcode.png')

    # Используем get_return_to_main_menu для клавиатуры возврата
    keyboard = get_return_to_main_menu('ru')

    await bot.send_photo(message.chat.id, photo=photo, reply_markup=keyboard)

    if sheet:
        try:
            row = len(sheet.get_all_values()) + 1
            sheetrow = '=ROW()-1'
            sheet.update_cell(row, 1, sheetrow)
            sheet.update_cell(row, 2, date)
            sheet.update_cell(row, 3, time)
            sheet.update_cell(row, 4, user_id)
            sheet.update_cell(row, 5, discount)
            sheet.update_cell(row, 6, restoran_id)
        except Exception as e:
            print(f"[!] Ошибка при обновлении Google Sheet: {e}")
