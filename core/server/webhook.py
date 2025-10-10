"""
Webhook server используя aiogram.webhook.aiohttp_server
"""
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from core.config.deployment import DeploymentConfig

logger = logging.getLogger(__name__)

class WebhookServer:
    """Webhook на aiohttp с aiogram интеграцией"""
    
    def __init__(self, bot: Bot, dp: Dispatcher, config: DeploymentConfig):
        self.bot = bot
        self.dp = dp
        self.config = config
        self.app = web.Application()
        self.runner = None
    
    async def setup_webhook(self):
        """Настроить webhook"""
        logger.info("🔧 Setting up webhook...")
        
        # Удалить старый
        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Old webhook deleted")
        except Exception as e:
            logger.warning(f"⚠️ Webhook delete: {e}")
        
        # Установить новый
        webhook_url = self.config.full_webhook_url
        await self.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        logger.info(f"✅ Webhook set: {webhook_url}")
        
        # Проверить
        info = await self.bot.get_webhook_info()
        logger.info(f"📡 Webhook active: {info.url}")
        if info.last_error_message:
            logger.warning(f"⚠️ Last error: {info.last_error_message}")
    
    def setup_routes(self):
        """Настроить маршруты"""
        # aiogram webhook handler
        SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot
        ).register(self.app, path=self.config.webhook_path)
        
        # Health check
        self.app.router.add_get("/health", self._health)
        self.app.router.add_get("/", self._root)
        
        logger.info(f"📍 Routes: {self.config.webhook_path}, /health")
    
    async def _health(self, request):
        """Health check"""
        info = await self.bot.get_webhook_info()
        return web.json_response({
            "status": "ok",
            "service": "KARMABOT1",
            "mode": "webhook",
            "webhook_url": info.url,
            "pending_updates": info.pending_update_count
        })
    
    async def _root(self, request):
        """Root endpoint"""
        return web.json_response({
            "service": "KARMABOT1",
            "status": "running"
        })
    
    async def start(self):
        """Запустить сервер"""
        await self.setup_webhook()
        self.setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(
            self.runner,
            host=self.config.host,
            port=self.config.port
        )
        await site.start()
        
        logger.info(f"✅ Server started on {self.config.host}:{self.config.port}")
    
    async def stop(self):
        """Остановить сервер"""
        await self.bot.delete_webhook()
        if self.runner:
            await self.runner.cleanup()
        logger.info("✅ Server stopped")
