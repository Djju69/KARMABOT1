from __future__ import annotations

from aiogram.types import Message

# Minimal legacy-compatible stubs used by main_v2 imports
async def restoran_2_10_1_0(message: Message):
    await message.answer("Показываю ресторан (шаблон 2_10_1_0) — заглушка")

async def restoran_2_10_1_1(message: Message):
    await message.answer("Показываю ресторан (шаблон 2_10_1_1) — заглушка")

async def qr_code_postman(message: Message):
    await message.answer("Отправка QR-кода (postman) — заглушка")

__all__ = [
    "restoran_2_10_1_0",
    "restoran_2_10_1_1",
    "qr_code_postman",
]
