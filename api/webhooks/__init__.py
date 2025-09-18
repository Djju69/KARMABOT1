""
Webhook handlers for external services.
"""
from fastapi import APIRouter
from .telegram import router as telegram_router

router = APIRouter()
router.include_router(telegram_router, prefix="/webhooks")

__all__ = ["router"]
