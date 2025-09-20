"""Script to check and clean up Telegram webhook."""
import os
import sys
import logging

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from core.config import load_settings, Bots

# Load settings
settings = load_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_webhook():
    """Check and clean up webhook configuration."""
    try:
        # Get bot token from settings
        bot_token = settings.bots.bot_token
        if not bot_token:
            print("❌ Bot token not found in settings")
            return 1
            
        print(f"🤖 Bot token: {bot_token[:8]}...")
        
        async with Bot(token=bot_token) as bot:
            # Check current webhook info
            webhook_info = await bot.get_webhook_info()
            print("\n=== Current Webhook Info ===")
            print(f"URL: {webhook_info.url or 'None'}")
            print(f"Has custom certificate: {webhook_info.has_custom_certificate}")
            print(f"Pending update count: {webhook_info.pending_update_count}")
            print(f"Last error date: {webhook_info.last_error_date}")
            print(f"Last error message: {webhook_info.last_error_message}")
            print(f"Max connections: {webhook_info.max_connections}")
            print(f"Allowed updates: {webhook_info.allowed_updates}")
            
            # Delete webhook if it exists
            if webhook_info.url:
                print("\nDeleting webhook...")
                deleted = await bot.delete_webhook(drop_pending_updates=True)
                print(f"Webhook deleted: {deleted}")
                
                # Verify deletion
                webhook_info = await bot.get_webhook_info()
                print(f"\nWebhook after deletion: {webhook_info.url or 'None'}")
            
            # Get bot info
            me = await bot.get_me()
            print("\n=== Bot Info ===")
            print(f"Bot: @{me.username} (ID: {me.id})")
            print(f"Name: {me.full_name}")
            
            # Get updates
            print("\n=== Recent Updates ===")
            updates = await bot.get_updates(limit=3)
            if updates:
                for i, update in enumerate(updates, 1):
                    print(f"\nUpdate {i}:")
                    print(f"  Update ID: {update.update_id}")
                    if update.message:
                        msg = update.message
                        print(f"  Message: {msg.text or 'No text'}")
                        print(f"  From: {msg.from_user.username or msg.from_user.id}")
                    else:
                        print(f"  Type: {update.update_type}")
            else:
                print("No recent updates found.")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(check_webhook()))
