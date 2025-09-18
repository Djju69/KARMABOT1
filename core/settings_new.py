"""
Исправленный файл настроек для KARMABOT1
Поместите этот файл в /app/core/settings_new.py
"""
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

# Исправлено: используем pydantic-settings для BaseSettings
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, validator, PostgresDsn, AnyUrl
    PYDANTIC_V2 = True
except ImportError:
    # Fallback для старых версий pydantic
    try:
        from pydantic import BaseSettings, Field, validator, PostgresDsn, AnyUrl
        PYDANTIC_V2 = False
    except ImportError:
        # Совсем базовая реализация без pydantic
        BaseSettings = object
        PYDANTIC_V2 = False
        
        def Field(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        def validator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator


class Settings:
    """
    Настройки для KARMABOT1
    Поддерживает как Pydantic v1, так и v2
    """
    
    def __init__(self):
        # Основные настройки бота
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
        
        # База данных - автоматическое переключение на PostgreSQL для Railway
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Локальная разработка - SQLite
            database_url = "sqlite:///core/database/data.db"
        elif database_url.startswith('postgres://'):
            # Railway PostgreSQL - исправить формат URL
            database_url = database_url.replace('postgres://', 'postgresql://')
        
        self.DATABASE_URL: str = database_url
        print(f"🗄️ Используется БД: {database_url.split('@')[0] if '@' in database_url else database_url}...")
        
        # Фича-флаги (по умолчанию выключены для безопасности)
        self.FEATURE_PARTNER_FSM: bool = os.getenv("FEATURE_PARTNER_FSM", "false").lower() == "true"
        self.FEATURE_MODERATION: bool = os.getenv("FEATURE_MODERATION", "false").lower() == "true"
        self.FEATURE_NEW_MENU: bool = os.getenv("FEATURE_NEW_MENU", "false").lower() == "true"
        self.FEATURE_QR_WEBAPP: bool = os.getenv("FEATURE_QR_WEBAPP", "false").lower() == "true"
        self.FEATURE_LISTEN_NOTIFY: bool = os.getenv("FEATURE_LISTEN_NOTIFY", "false").lower() == "true"
        
        # Дополнительные настройки
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # WebApp настройки
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "your_jwt_secret_here_change_in_production")
        self.AUTH_WINDOW_SEC: int = int(os.getenv("AUTH_WINDOW_SEC", "300"))
        self.WEBAPP_QR_URL: str = os.getenv("WEBAPP_QR_URL", "")
        self.WEBAPP_ALLOWED_ORIGIN: str = os.getenv("WEBAPP_ALLOWED_ORIGIN", "*")
        self.CSP_ALLOWED_ORIGIN: str = os.getenv("CSP_ALLOWED_ORIGIN", "*")
        self.FASTAPI_ONLY: bool = os.getenv("FASTAPI_ONLY", "false").lower() == "true"
        
        # Redis настройки
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
        
        # Webhook настройки
        self.WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")
        self.WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8080"))
        self.WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
        self.USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "false").lower() == "true"
        
        # Проверяем обязательные параметры только в production
        if self.ENVIRONMENT == "production":
            self._validate_settings()
    
    def _validate_settings(self):
        """Проверяет корректность настроек"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not self.ADMIN_ID:
            raise ValueError("ADMIN_ID is required")
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Возвращает словарь всех фича-флагов"""
        return {
            "PARTNER_FSM": self.FEATURE_PARTNER_FSM,
            "MODERATION": self.FEATURE_MODERATION,
            "NEW_MENU": self.FEATURE_NEW_MENU,
            "QR_WEBAPP": self.FEATURE_QR_WEBAPP,
            "LISTEN_NOTIFY": self.FEATURE_LISTEN_NOTIFY,
        }
    
    def is_development(self) -> bool:
        """Проверяет, запущен ли проект в режиме разработки"""
        return self.ENVIRONMENT.lower() in ["development", "dev", "local"]
    
    def is_production(self) -> bool:
        """Проверяет, запущен ли проект в продакшн режиме"""
        return self.ENVIRONMENT.lower() in ["production", "prod"]


# Если доступен Pydantic, создаем улучшенную версию
if BaseSettings != object and PYDANTIC_V2:
    class PydanticSettings(BaseSettings):
        """
        Настройки с использованием Pydantic v2
        """
        model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
        
        # Основные настройки
        bot_token: str = Field("", description="Telegram Bot Token")
        admin_id: int = Field(0, description="Admin Telegram ID")
        
        # База данных
        database_url: str = Field("sqlite:///core/database/data.db", description="Database URL")
        
        # Фича-флаги
        feature_partner_fsm: bool = Field(False, description="Enable Partner FSM")
        feature_moderation: bool = Field(False, description="Enable Moderation")
        feature_new_menu: bool = Field(False, description="Enable New Menu")
        feature_qr_webapp: bool = Field(False, description="Enable QR WebApp")
        feature_listen_notify: bool = Field(False, description="Enable Listen Notify")
        
        # Дополнительные настройки
        log_level: str = Field("INFO", description="Logging level")
        environment: str = Field("development", description="Environment")
        debug: bool = Field(False, description="Debug mode")
        
        # WebApp
        jwt_secret: str = Field("debug", description="JWT Secret")
        auth_window_sec: int = Field(300, description="Auth window in seconds")
        webapp_qr_url: str = Field("", description="WebApp QR URL")
        webapp_allowed_origin: str = Field("*", description="WebApp allowed origin")
        csp_allowed_origin: str = Field("*", description="CSP allowed origin")
        fastapi_only: bool = Field(False, description="FastAPI only mode")
        
        # Redis
        redis_url: str = Field("redis://localhost:6379/0", description="Redis URL")
        redis_host: str = Field("localhost", description="Redis host")
        redis_port: int = Field(6379, description="Redis port")
        redis_db: int = Field(0, description="Redis database")
        
        # Webhook
        webhook_host: str = Field("", description="Webhook host")
        webhook_port: int = Field(8080, description="Webhook port")
        webhook_path: str = Field("/webhook", description="Webhook path")
        use_webhook: bool = Field(False, description="Use webhook")

    try:
        # Пробуем создать Pydantic настройки
        pydantic_settings = PydanticSettings()
        settings = Settings()
        
        # Копируем значения из Pydantic в обычный класс
        for field_name, field_value in pydantic_settings.model_dump().items():
            # Конвертируем snake_case в UPPER_CASE
            attr_name = field_name.upper()
            if hasattr(settings, attr_name):
                setattr(settings, attr_name, field_value)
                
    except Exception as e:
        print(f"Warning: Failed to load Pydantic settings, using fallback: {e}")
        settings = Settings()
else:
    # Используем базовую реализацию
    settings = Settings()


def get_settings():
    """Функция для получения настроек (для совместимости с разными частями кода)"""
    return settings


def validate_settings():
    """Проверяет корректность всех настроек"""
    try:
        settings._validate_settings()
        return True
    except ValueError as e:
        print(f"Settings validation failed: {e}")
        return False


# Автоматическая валидация при импорте только в production
if settings.ENVIRONMENT == "production":
    validate_settings()

# Настройка логирования
import logging

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Уменьшаем логи от сторонних библиотек
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Логируем загрузку настроек
logger.info(f"Загружены настройки для окружения: {settings.ENVIRONMENT}")
logger.info(f"Режим отладки: {'ВКЛ' if settings.DEBUG else 'ВЫКЛ'}")
logger.info(f"Feature flags: PARTNER_FSM={settings.FEATURE_PARTNER_FSM}, "
           f"MODERATION={settings.FEATURE_MODERATION}, "
           f"QR_WEBAPP={settings.FEATURE_QR_WEBAPP}, "
           f"LISTEN_NOTIFY={settings.FEATURE_LISTEN_NOTIFY}")
