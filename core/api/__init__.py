"""
API-модули приложения.
"""
from fastapi import APIRouter

# Импортируем все API-роутеры
from . import qr, card

# Создаем основной роутер API
api_router = APIRouter()

# Подключаем все API-роутеры
api_router.include_router(qr.router, prefix="/api/qr", tags=["qr"])
api_router.include_router(card.router, prefix="/api/card", tags=["card"])
