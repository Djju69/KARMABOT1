"""
Минимальные настройки для новой multi-platform системы
"""
import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class Features:
    """Feature flags для новой системы"""
    new_menu: bool = field(default=True)
    partner_fsm: bool = field(default=True)
    moderation: bool = field(default=False)
    qr_webapp: bool = field(default=False)
    support_ai: bool = field(default=True)
    support_reports: bool = field(default=True)
    webapp_url: str = field(default="https://web-production-d51c7.up.railway.app/webapp")

@dataclass
class Settings:
    """Основные настройки системы"""
    features: Features = field(default_factory=Features)
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development") == "development")

def get_settings() -> Settings:
    """Получить настройки системы"""
    try:
        settings = Settings()
        logger.info("✅ Settings loaded successfully")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        # Возвращаем базовые настройки
        return Settings()