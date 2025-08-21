from __future__ import annotations

from aiogram import Router
from aiogram.types import Message

router = Router(name=__name__)

# Minimal stubs for legacy callback handlers referenced in main_v2
async def rests_by_district_handler(message: Message):
    await message.answer("Покажем заведения по району (заглушка)")

async def rest_near_me_handler(message: Message):
    await message.answer("Покажем заведения рядом (заглушка)")

async def rests_by_kitchen_handler(message: Message):
    await message.answer("Покажем заведения по кухне (заглушка)")

async def location_handler(message: Message):
    await message.answer("Обрабатываем локацию (заглушка)")

# For backward compatibility with main_v2 import
callback_router = router

__all__ = [
    "callback_router",
    "rests_by_district_handler",
    "rest_near_me_handler",
    "rests_by_kitchen_handler",
    "location_handler",
]
