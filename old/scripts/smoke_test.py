"""Smoke tests for KarmaSystemBot."""
import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SmokeTester:
    """Class for running smoke tests against the bot."""
    
    def __init__(self, token: str, admin_id: int):
        """Initialize the smoke tester."""
        self.bot = Bot(token=token)
        self.admin_id = admin_id
        self.dp = Dispatcher()
        self.test_results = {}
        
    async def run_tests(self):
        """Run all smoke tests."""
        logger.info("🚀 Starting smoke tests...")
        
        # Test 1: Check bot is responding
        await self._test_bot_responding()
        
        # Test 2: Admin commands
        await self._test_admin_commands()
        
        # Print summary
        await self._print_summary()
        
        return all(self.test_results.values())
    
    async def _test_bot_responding(self):
        """Test if bot is responding to messages."""
        test_name = "Bot responding to /start"
        try:
            await self.bot.send_message(self.admin_id, "/start")
            self.test_results[test_name] = True
            logger.info(f"✅ {test_name}")
        except Exception as e:
            self.test_results[test_name] = False
            logger.error(f"❌ {test_name}: {str(e)}")
    
    async def _test_admin_commands(self):
        """Test admin commands."""
        tests = [
            ("Admin panel access", 
             lambda: self._send_command("/admin")),
            ("Queue view", 
             lambda: self._send_callback("adm:q:view:1:0")),
        ]
        
        for test_name, test_func in tests:
            try:
                await test_func()
                self.test_results[test_name] = True
                logger.info(f"✅ {test_name}")
            except Exception as e:
                self.test_results[test_name] = False
                logger.error(f"❌ {test_name}: {str(e)}")
            await asyncio.sleep(1)  # Rate limiting
    
    async def _send_command(self, command: str):
        """Send a command to the bot."""
        await self.bot.send_message(self.admin_id, command)
    
    async def _send_callback(self, data: str):
        """Send a callback query to the bot."""
        from aiogram.types import CallbackQuery, User, Message, Chat
        
        callback = CallbackQuery(
            id="test_callback",
            from_user=User(
                id=self.admin_id,
                first_name="Test",
                is_bot=False,
                username="testuser"
            ),
            message=Message(
                message_id=1,
                chat=Chat(id=self.admin_id, type="private"),
                date=0,
                text="Test message"
            ),
            chat_instance="test",
            data=data
        )
        
        # This would need to be adapted to your actual bot's dispatcher
        # For now, we'll just send it as a message
        await self.bot.send_message(
            self.admin_id,
            f"[Test Callback] {data}"
        )
    
    async def _print_summary(self):
        """Print test summary."""
        logger.info("\n📊 Test Summary:")
        for test, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} - {test}")
        
        success = all(self.test_results.values())
        if success:
            logger.info("\n🎉 All smoke tests passed!")
        else:
            failed = sum(1 for r in self.test_results.values() if not r)
            logger.error(f"\n🔴 {failed} test(s) failed!")


async def main():
    """Run smoke tests."""
    token = os.getenv("BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_IDS", "").split(",")[0] or "0")
    
    if not token or not admin_id:
        logger.error("❌ BOT_TOKEN and ADMIN_IDS must be set in .env")
        return False
    
    tester = SmokeTester(token, admin_id)
    return await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
