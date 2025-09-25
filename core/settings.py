"""
Минимальные настройки для совместимости с main_v2.py
"""
import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from environs import Env

logger = logging.getLogger(__name__)

@dataclass
class Features:
    new_menu: bool = field(default=True)
    menu_v2: bool = field(default=False)
    partner_fsm: bool = field(default=True)
    moderation: bool = field(default=False)
    qr_webapp: bool = field(default=False)
    listen_notify: bool = field(default=False)
    support_voice: bool = field(default=False)
    support_ai: bool = field(default=True)
    support_reports: bool = field(default=True)
    webapp_url: str = field(default="https://webbot-production-42fe.up.railway.app")
    verbose_admin_back: bool = field(default=False)
    multi_platform_available: bool = field(default=True)

@dataclass
class Settings:
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "False").lower() == "true")
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data.db"))
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    features: Features = field(default_factory=Features)
    
    # Настройки ботов
    admin_id: int = field(default_factory=lambda: int(os.getenv("ADMIN_ID", "6391215556")))  # Ваш ID как админ
    
    # Дополнительные атрибуты для совместимости
    admins: list = field(default_factory=list)
    super_admins: list = field(default_factory=lambda: [6391215556])  # Ваш ID как супер-админ
    partners: list = field(default_factory=list)

    def __post_init__(self):
        env = Env()
        env.read_env()  # read .env file, if it exists

        self.environment = env.str("ENVIRONMENT", self.environment)
        self.debug = env.bool("DEBUG", self.debug)
        self.bot_token = env.str("BOT_TOKEN", self.bot_token)
        self.database_url = env.str("DATABASE_URL", self.database_url)
        self.supabase_url = env.str("SUPABASE_URL", self.supabase_url)
        self.supabase_key = env.str("SUPABASE_KEY", self.supabase_key)
        self.redis_url = env.str("REDIS_URL", self.redis_url)

        # Ensure multi_platform_available is set based on environment or explicit flag
        self.features.multi_platform_available = env.bool("MULTI_PLATFORM_AVAILABLE", self.features.multi_platform_available)

        if not self.bot_token:
            logger.warning("BOT_TOKEN is not set in environment variables.")
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase URL or Key is not set in environment variables.")

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Создаем глобальный объект settings для совместимости
settings = get_settings()