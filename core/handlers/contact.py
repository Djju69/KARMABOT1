from __future__ import annotations

from aiogram.types import Message

# Minimal contact handlers compatible with aiogram v3
async def get_true_contact(message: Message):
    await message.answer("Спасибо! Контакт подтвержден (ваш номер).")

async def get_fake_contact(message: Message):
    await message.answer("Это не ваш контакт. Пожалуйста, поделитесь своим номером через кнопку.")

__all__ = ["get_true_contact", "get_fake_contact"]
