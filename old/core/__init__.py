"""
Core package for KarmaSystem.

This package contains the core functionality of the application,
including settings, database models, and other essential components.
"""

# Импортируем настройки
from .settings_new import settings as settings
from .telegram_settings import TelegramSettings

__all__ = [
    'settings',
    'TelegramSettings',
]
