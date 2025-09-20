"""
Настройки интеграции с Telegram.
"""
import os
import secrets
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from environs import Env

@dataclass
class TelegramSettings:
    """Настройки интеграции с Telegram"""
    bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    bot_username: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_USERNAME", ""))
    webhook_url: Optional[str] = field(default_factory=lambda: os.getenv("TELEGRAM_WEBHOOK_URL"))
    webhook_secret: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_WEBHOOK_SECRET") or secrets.token_urlsafe(32)
    )
    max_connections: int = field(default=40)
    auth_expire_minutes: int = field(default=15)
    login_redirect_url: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_LOGIN_REDIRECT_URL", "")
    )
    allowed_updates: List[str] = field(
        default_factory=lambda: ["message", "callback_query", "inline_query"]
    )
    
    def __post_init__(self):
        """Инициализация настроек Telegram"""
        env = Env()
        self.bot_token = env.str('TELEGRAM_BOT_TOKEN', self.bot_token)
        self.bot_username = env.str('TELEGRAM_BOT_USERNAME', self.bot_username)
        self.webhook_url = env.str('TELEGRAM_WEBHOOK_URL', self.webhook_url)
        self.webhook_secret = env.str('TELEGRAM_WEBHOOK_SECRET', self.webhook_secret)
        self.login_redirect_url = env.str('TELEGRAM_LOGIN_REDIRECT_URL', self.login_redirect_url)
        
        # Логируем настройки
        logger = logging.getLogger(__name__)
        if self.bot_token and self.bot_username:
            logger.info("[TELEGRAM] Bot configured with username: @%s", self.bot_username)
            if self.webhook_url:
                logger.info("[TELEGRAM] Webhook URL: %s", self.webhook_url)
        else:
            logger.warning("[TELEGRAM] Bot token or username not configured")
    
    @property
    def is_configured(self) -> bool:
        """Проверка корректности конфигурации бота"""
        return bool(self.bot_token and self.bot_username)
    
    @property
    def is_webhook_configured(self) -> bool:
        """Проверка корректности конфигурации вебхука"""
        return bool(self.webhook_url and self.is_configured)
