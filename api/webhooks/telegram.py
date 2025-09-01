"""
Webhook handler for Telegram bot updates.
"""
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core import settings
from core.telegram_service import TelegramService

router = APIRouter()
logger = logging.getLogger(__name__)

class TelegramUpdate(BaseModel):
    """Model for Telegram update."""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    edited_message: Optional[Dict[str, Any]] = None
    channel_post: Optional[Dict[str, Any]] = None
    edited_channel_post: Optional[Dict[str, Any]] = None
    inline_query: Optional[Dict[str, Any]] = None
    chosen_inline_result: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    shipping_query: Optional[Dict[str, Any]] = None
    pre_checkout_query: Optional[Dict[str, Any]] = None
    poll: Optional[Dict[str, Any]] = None
    poll_answer: Optional[Dict[str, Any]] = None
    my_chat_member: Optional[Dict[str, Any]] = None
    chat_member: Optional[Dict[str, Any]] = None
    chat_join_request: Optional[Dict[str, Any]] = None

def verify_telegram_webhook(secret_token: str, request: Request) -> bool:
    """Verify Telegram webhook secret token."""
    if not secret_token:
        return False
        
    # Get X-Telegram-Bot-Api-Secret-Token header
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not token:
        return False
        
    return hmac.compare_digest(token, secret_token)

@router.post("/webhook/telegram")
async def telegram_webhook(
    update: TelegramUpdate,
    request: Request,
    telegram_service: TelegramService = Depends(TelegramService)
):
    """Handle incoming Telegram updates via webhook."""
    # Verify secret token if configured
    if settings.telegram.webhook_secret:
        if not verify_telegram_webhook(settings.telegram.webhook_secret, request):
            logger.warning("Invalid Telegram webhook secret token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook token"
            )
    
    try:
        # Process the update
        await telegram_service.process_update(update.dict())
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "detail": str(e)},
            status_code=500
        )

@router.get("/webhook/telegram/setup")
async def setup_telegram_webhook(
    telegram_service: TelegramService = Depends(TelegramService)
):
    """Set up Telegram webhook with the current URL."""
    if not settings.telegram.is_webhook_configured:
        return {
            "status": "error",
            "detail": "Webhook URL is not configured. Set TELEGRAM_WEBHOOK_URL environment variable."
        }
    
    try:
        result = await telegram_service.set_webhook(
            url=settings.telegram.webhook_url,
            secret_token=settings.telegram.webhook_secret,
            max_connections=settings.telegram.max_connections,
            allowed_updates=settings.telegram.allowed_updates
        )
        return {
            "status": "success",
            "webhook_info": result
        }
    except Exception as e:
        logger.error(f"Error setting up Telegram webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set webhook: {str(e)}"
        )

@router.get("/webhook/telegram/info")
async def get_webhook_info(
    telegram_service: TelegramService = Depends(TelegramService)
):
    """Get current webhook information."""
    try:
        webhook_info = await telegram_service.get_webhook_info()
        return {
            "status": "success",
            "webhook_info": webhook_info
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook info: {str(e)}"
        )
