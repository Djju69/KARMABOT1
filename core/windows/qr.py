from __future__ import annotations

from aiogram.types import Message

async def generate_qrcode(message: Message):
    await message.answer("Генерируем QR-код (заглушка)")

async def qr_code_check(message: Message):
    await message.answer("Проверяем QR-код (заглушка)")

__all__ = ["generate_qrcode", "qr_code_check"]
