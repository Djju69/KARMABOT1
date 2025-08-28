from aiogram import types, Bot, F
from aiogram.types import Message, InputFile, BufferedInputFile
from core.handlers.basic import main_menu
import datetime
import segno
import gspread
import json
from datetime import timezone, timedelta, datetime
from core.keyboards.reply import return_to_main_menu
from urllib.parse import urlencode
import asyncio
from qrcode_artistic import write_artistic


SHEET_ID = "1jBRhdrrZBGuIq5zaeTwHPWslMYmT7hypFNYPBGUM48E"
WORKSHEET_NAME = "1"

gc = gspread.service_account(filename='mythic-brook-414011-6b6b807faea2.json')
sheet = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

async def discount_generator(message: types.Message, bot: Bot,data_rest):
    text=f'''Ведите пожалуйста сумму вашего чека'''
    await generate_qrcode_new(message, bot)

async def generate_qrcode_new(message: types.Message, bot: Bot,data_rest):
  user_id = message.chat.id
  now_gmt7 = datetime.now(timezone(timedelta(hours=7)))
  date_time = now_gmt7.strftime("%Y-%m-%d %H:%M:%S")
  date, time = date_time.split(" ")
  discount = int(5)
  restoran_id = data_rest.get("rest_data")

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
  # qrcode.to_artistic(background=background_image, target="qrcode.png", scale=3, border=1)

  with open('qrcode.png', 'rb') as image_file:
    image_data = image_file.read()

  photo = BufferedInputFile(image_data, filename='qrcode.png')

  await bot.send_photo(message.chat.id,
                       photo=photo,
                       reply_markup=return_to_main_menu)

  row = len(sheet.get_all_values()) + 1
  sheetrow = '=ROW()-1'
  sheet.update_cell(row, 1, sheetrow)
  sheet.update_cell(row, 2, date)
  sheet.update_cell(row, 3, time)
  sheet.update_cell(row, 4, user_id)
  sheet.update_cell(row, 5, discount)
  sheet.update_cell(row, 6, restoran_id)
