"""
Partner handlers
"""
from aiogram import Router

partner_router = Router()

@partner_router.message()
async def partner_handler(message):
    """Partner handler placeholder"""
    pass
