"""
Настройки приложения KarmaSystem.
"""
import os
import secrets
import logging
from datetime import timedelta
from environs import Env
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

# Импортируем настройки Telegram
from core.telegram_settings import TelegramSettings

@dataclass
class Features:
    """Feature flags configuration"""
    new_menu: bool = field(default=True)  # Включено по умолчанию
    partner_fsm: bool = field(default=True)
    moderation: bool = field(default=False)
    qr_webapp: bool = field(default=False)
    listen_notify: bool = field(default=False)
    
    def __post_init__(self):
        """Initialize feature flags from environment variables"""
        env = Env()
        
        # Load from environment variables if they exist
        self.new_menu = env.bool('FEATURE_NEW_MENU', self.new_menu)
        self.partner_fsm = env.bool('FEATURE_PARTNER_FSM', True)  # Принудительно включено
        self.moderation = env.bool('FEATURE_MODERATION', True)  # Принудительно включено
        self.qr_webapp = env.bool('FEATURE_QR_WEBAPP', self.qr_webapp)
        self.listen_notify = env.bool('FEATURE_LISTEN_NOTIFY', self.listen_notify)
        
        # Log current feature flags
        logger = logging.getLogger(__name__)
        logger.info(f"[FEATURES] New Menu: {self.new_menu}")
        logger.info(f"[FEATURES] Partner FSM: {self.partner_fsm}")
        logger.info(f"[FEATURES] Moderation: {self.moderation}")
        logger.info(f"[FEATURES] QR WebApp: {self.qr_webapp}")
        logger.info(f"[FEATURES] Listen Notify: {self.listen_notify}")

@dataclass
class AuthSettings:
    """Настройки аутентификации"""
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY") or secrets.token_urlsafe(32))
    algorithm: str = field(default="HS256")
    access_token_expire_minutes: int = field(default=60 * 24)  # 24 часа
    refresh_token_expire_days: int = field(default=30)
    email_reset_token_expire_hours: int = field(default=24)
    email_verification_token_expire_hours: int = field(default=72)
    password_reset_url: Optional[str] = field(default=None)
    frontend_url: Optional[str] = field(default=os.getenv("FRONTEND_URL"))
    api_v1_str: str = field(default="/api/v1")
    
    def __post_init__(self):
        """Инициализация настроек аутентификации"""
        env = Env()
        
        # Загрузка из переменных окружения, если они существуют
        self.secret_key = env.str('SECRET_KEY', self.secret_key)
        self.algorithm = env.str('AUTH_ALGORITHM', self.algorithm)
        self.access_token_expire_minutes = env.int('ACCESS_TOKEN_EXPIRE_MINUTES', self.access_token_expire_minutes)
        self.refresh_token_expire_days = env.int('REFRESH_TOKEN_EXPIRE_DAYS', self.refresh_token_expire_days)
        self.email_reset_token_expire_hours = env.int('EMAIL_RESET_TOKEN_EXPIRE_HOURS', self.email_reset_token_expire_hours)
        self.email_verification_token_expire_hours = env.int('EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS', self.email_verification_token_expire_hours)
        self.frontend_url = env.str('FRONTEND_URL', self.frontend_url)
        self.password_reset_url = env.str('PASSWORD_RESET_URL', self.password_reset_url or f"{self.frontend_url}/reset-password" if self.frontend_url else None)
        
        # Логируем настройки (без чувствительных данных)
        logger = logging.getLogger(__name__)
        logger.info("[AUTH] Algorithm: %s", self.algorithm)
        logger.info("[AUTH] Access token expire: %s minutes", self.access_token_expire_minutes)
        logger.info("[AUTH] Refresh token expire: %s days", self.refresh_token_expire_days)
        logger.info("[AUTH] Frontend URL: %s", self.frontend_url)

@dataclass
class Bots:
    """Настройки ботов"""
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN"))
    admin_id: int = field(default_factory=lambda: int(os.getenv("ADMIN_ID", 0)))
    
    def __post_init__(self):
        """Инициализация настроек ботов"""
        env = Env()
        self.bot_token = env.str('BOT_TOKEN', self.bot_token)
        self.admin_id = env.int('ADMIN_ID', self.admin_id)
        
        # Логируем настройки
        logger = logging.getLogger(__name__)
        if self.bot_token:
            logger.info("[BOTS] Bot token configured")
        if self.admin_id:
            logger.info("[BOTS] Admin ID: %s", self.admin_id)

@dataclass
class DatabaseSettings:
    """Настройки базы данных"""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    echo: bool = field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")
    
    def __post_init__(self):
        """Инициализация настроек БД"""
        env = Env()
        self.url = env.str('DATABASE_URL', self.url)
        self.echo = env.bool('DB_ECHO', self.echo)
        
        # Логируем настройки (без пароля)
        if self.url:
            db_log = self.url.split('@')[-1] if '@' in self.url else self.url
            logging.getLogger(__name__).info("[DB] Database: %s", db_log)

@dataclass
class Settings:
    """Основные настройки приложения"""
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    
    # Подсистемы
    bots: Bots = field(default_factory=Bots)
    features: Features = field(default_factory=Features)
    auth: AuthSettings = field(default_factory=AuthSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    
    def __post_init__(self):
        """Инициализация основных настроек"""
        env = Env()
        self.debug = env.bool('DEBUG', self.debug)
        self.environment = env.str('ENVIRONMENT', self.environment)
        
        # Логируем настройки
        logger = logging.getLogger(__name__)
        logger.info("[APP] Environment: %s", self.environment)
        logger.info("[APP] Debug mode: %s", self.debug)

def get_settings(path: Optional[str] = None) -> Settings:
    """
    Загружает настройки из переменных окружения.
    
    Args:
        path: Путь к файлу .env (опционально)
        
    Returns:
        Settings: Объект с настройками
    """
    # Загружаем переменные окружения из файла, если он указан
    if path and os.path.exists(path):
        from dotenv import load_dotenv
        load_dotenv(path)
    
    # Создаем и возвращаем объект настроек
    return Settings()

# Инициализируем настройки
settings = get_settings('.env')

# Логируем загрузку настроек
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application settings initialized")
