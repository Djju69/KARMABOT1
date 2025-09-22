"""
Callback handlers
"""
from aiogram import Router

router = Router()

@router.callback_query()
async def callback_handler(callback):
    """Callback handler placeholder"""
    pass
