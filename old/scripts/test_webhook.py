#!/usr/bin/env python3
"""
Script to test Telegram webhook.

This script sends a test update to the webhook endpoint to verify it's working.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
import httpx

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_webhook():
    """Send a test update to the webhook endpoint."""
    if not settings.telegram.webhook_url:
        logger.error("Webhook URL is not configured. Set TELEGRAM_WEBHOOK_URL environment variable.")
        return False
    
    # Sample update payload (simplified)
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345678,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "language_code": "en"
            },
            "chat": {
                "id": 12345678,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": 1648227600,
            "text": "/start"
        }
    }
    
    headers = {}
    if settings.telegram.webhook_secret:
        headers["X-Telegram-Bot-Api-Secret-Token"] = settings.telegram.webhook_secret
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Sending test update to {settings.telegram.webhook_url}")
            response = await client.post(
                settings.telegram.webhook_url,
                json=test_update,
                headers=headers,
                timeout=10.0
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ Webhook is working correctly!")
                return True
            else:
                logger.error(f"❌ Webhook returned status code: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing webhook: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    if not settings.telegram.webhook_url:
        logger.error("Error: TELEGRAM_WEBHOOK_URL environment variable is not set")
        print("\nPlease set the following environment variables:")
        print(f"- TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhooks/telegram")
        if not settings.telegram.webhook_secret:
            print(f"- TELEGRAM_WEBHOOK_SECRET={settings.telegram.webhook_secret}  # Auto-generated if not set")
        sys.exit(1)
    
    # Run the async function
    success = asyncio.run(test_webhook())
    sys.exit(0 if success else 1)
