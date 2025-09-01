"""
Telegram integration settings and configuration.
"""
import os
from typing import List, Optional
from pydantic import Field, validator

from core.config import BaseModel

class TelegramSettings(BaseModel):
    """Settings for Telegram integration."""
    
    # Bot settings
    bot_token: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN") or "",
        description="Telegram Bot API token"
    )
    bot_username: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_USERNAME") or "",
        description="Telegram bot username (without @)"
    )
    
    # Webhook settings
    webhook_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("TELEGRAM_WEBHOOK_URL"),
        description="Full URL for Telegram webhook"
    )
    webhook_secret: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_WEBHOOK_SECRET") or "",
        description="Secret key for webhook verification"
    )
    max_connections: int = Field(
        default=40,
        description="Maximum number of concurrent connections for webhook"
    )
    
    # Authentication settings
    auth_expire_minutes: int = Field(
        default=15,
        description="Telegram login token expiration time in minutes"
    )
    login_redirect_url: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_LOGIN_REDIRECT_URL") or "",
        description="Redirect URL after successful Telegram login"
    )
    
    # Update settings
    allowed_updates: List[str] = Field(
        default_factory=lambda: ["message", "callback_query", "inline_query"],
        description="List of update types to receive from Telegram"
    )
    
    # API settings (for userbot if needed)
    api_id: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_API_ID") or "",
        description="Telegram API ID (for userbot)"
    )
    api_hash: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_API_HASH") or "",
        description="Telegram API hash (for userbot)"
    )
    
    @validator('webhook_url', pre=True)
    def validate_webhook_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Webhook URL must start with http:// or https://')
        return v
    
    @property
    def is_configured(self) -> bool:
        """Check if Telegram bot is properly configured."""
        return bool(self.bot_token and self.bot_username)
    
    @property
    def is_webhook_configured(self) -> bool:
        """Check if webhook is properly configured."""
        return bool(self.webhook_url and self.is_configured)
    
    def get_webhook_info(self) -> dict:
        """Get webhook configuration info."""
        return {
            "webhook_url": self.webhook_url,
            "allowed_updates": self.allowed_updates,
            "max_connections": self.max_connections,
            "is_configured": self.is_configured,
            "is_webhook_configured": self.is_webhook_configured
        }
