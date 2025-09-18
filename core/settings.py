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
    menu_v2: bool = field(default=False)  # RFC: Главное меню V2 (user/partner), partner back behavior
    partner_fsm: bool = field(default=True)
    moderation: bool = field(default=False)
    qr_webapp: bool = field(default=False)
    listen_notify: bool = field(default=False)
    support_voice: bool = field(default=False)  # Голосовой ввод
    support_ai: bool = field(default=True)  # AI-ассистент
    support_reports: bool = field(default=True)  # Отчёты через AI
    webapp_url: str = field(default="https://web-production-d51c7.up.railway.app/webapp")
    # Verbose admin back labels (SuperAdmin-approved; off by default, behind feature flag)
    verbose_admin_back: bool = field(default=False)
    
    def __post_init__(self):
        """Initialize feature flags from environment variables"""
        env = Env()
        
        # Load from environment variables if they exist
        self.new_menu = env.bool('FEATURE_NEW_MENU', self.new_menu)
        self.menu_v2 = env.bool('FEATURE_MENU_V2', self.menu_v2)
        self.partner_fsm = env.bool('FEATURE_PARTNER_FSM', True)  # Принудительно включено
        self.moderation = env.bool('FEATURE_MODERATION', True)  # Принудительно включено
        self.qr_webapp = env.bool('FEATURE_QR_WEBAPP', self.qr_webapp)
        self.listen_notify = env.bool('FEATURE_LISTEN_NOTIFY', self.listen_notify)
        self.support_voice = env.bool('FEATURE_SUPPORT_VOICE', self.support_voice)
        self.support_ai = env.bool('FEATURE_SUPPORT_AI', self.support_ai)
        self.support_reports = env.bool('FEATURE_SUPPORT_REPORTS', self.support_reports)
        self.verbose_admin_back = env.bool('FEATURE_VERBOSE_ADMIN_BACK', self.verbose_admin_back)
        
        # Log current feature flags
        logger = logging.getLogger(__name__)
        logger.info(f"[FEATURES] New Menu: {self.new_menu}")
        logger.info(f"[FEATURES] Menu V2: {self.menu_v2}")
        logger.info(f"[FEATURES] Partner FSM: {self.partner_fsm}")
        logger.info(f"[FEATURES] Moderation: {self.moderation}")
        logger.info(f"[FEATURES] QR WebApp: {self.qr_webapp}")
        logger.info(f"[FEATURES] Listen Notify: {self.listen_notify}")
        logger.info(f"[FEATURES] Support Voice: {self.support_voice}")
        logger.info(f"[FEATURES] Support AI: {self.support_ai}")
        logger.info(f"[FEATURES] Support Reports: {self.support_reports}")
        logger.info(f"[FEATURES] Verbose Admin Back: {self.verbose_admin_back}")

# Back-compat alias for tests expecting FeatureFlags with all-false defaults
class FeatureFlags:
    def __init__(self):
        # Defaults are intentionally False to satisfy safety-first contracts
        self.partner_fsm = False
        self.moderation = False
        self.new_menu = False
        self.qr_webapp = False
        self.listen_notify = False

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
class KarmaConfig:
    """Конфигурация системы кармы согласно ТЗ"""
    level_thresholds: List[int] = field(default_factory=lambda: [100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000])
    daily_login_bonus: int = field(default=5)
    card_bind_bonus: int = field(default=25)
    referral_bonus: int = field(default=50)
    admin_karma_limit: int = field(default=1000)  # макс изменение кармы за раз админом
    card_generation_limit: int = field(default=10000)  # макс карт за раз
    rate_limit_per_minute: int = field(default=20)  # макс запросов в минуту
    
    def __post_init__(self):
        """Инициализация конфигурации кармы"""
        env = Env()
        
        # Загрузка из переменных окружения, если они существуют
        self.daily_login_bonus = env.int('KARMA_DAILY_LOGIN_BONUS', self.daily_login_bonus)
        self.card_bind_bonus = env.int('KARMA_CARD_BIND_BONUS', self.card_bind_bonus)
        self.referral_bonus = env.int('KARMA_REFERRAL_BONUS', self.referral_bonus)
        self.admin_karma_limit = env.int('KARMA_ADMIN_LIMIT', self.admin_karma_limit)
        self.card_generation_limit = env.int('KARMA_CARD_GENERATION_LIMIT', self.card_generation_limit)
        self.rate_limit_per_minute = env.int('KARMA_RATE_LIMIT', self.rate_limit_per_minute)
        
        # Логируем настройки
        logger = logging.getLogger(__name__)
        logger.info("[KARMA] Daily login bonus: %s", self.daily_login_bonus)
        logger.info("[KARMA] Card bind bonus: %s", self.card_bind_bonus)
        logger.info("[KARMA] Referral bonus: %s", self.referral_bonus)
        logger.info("[KARMA] Admin karma limit: %s", self.admin_karma_limit)
        logger.info("[KARMA] Level thresholds: %s", self.level_thresholds)

@dataclass
class CardConfig:
    """Конфигурация системы карт согласно ТЗ"""
    prefix: str = field(default="KS")
    start_number: int = field(default=12340001)
    format: str = field(default="{prefix}{number:08d}")  # KS12340001
    printable_format: str = field(default="{prefix}-{group1}-{group2}")  # KS-1234-0001
    
    def __post_init__(self):
        """Инициализация конфигурации карт"""
        env = Env()
        
        # Загрузка из переменных окружения, если они существуют
        self.prefix = env.str('CARD_PREFIX', self.prefix)
        self.start_number = env.int('CARD_START_NUMBER', self.start_number)
        self.format = env.str('CARD_FORMAT', self.format)
        self.printable_format = env.str('CARD_PRINTABLE_FORMAT', self.printable_format)
        
        # Логируем настройки
        logger = logging.getLogger(__name__)
        logger.info("[CARDS] Prefix: %s", self.prefix)
        logger.info("[CARDS] Start number: %s", self.start_number)
        logger.info("[CARDS] Format: %s", self.format)
        logger.info("[CARDS] Printable format: %s", self.printable_format)

@dataclass
class VoiceSettings:
    """Настройки голосового функционала"""
    max_duration: int = field(default=60)  # seconds
    max_filesize_mb: int = field(default=2)  # MB
    rate_limit: int = field(default=5)  # max requests per user
    rate_period: int = field(default=60)  # seconds rate limit window
    supported_formats: List[str] = field(default_factory=lambda: ['.ogg', '.mp3', '.m4a', '.wav'])
    
    def __post_init__(self):
        """Initialize voice settings from environment variables"""
        env = Env()
        
        self.max_duration = env.int('VOICE_MAX_DURATION', self.max_duration)
        self.max_filesize_mb = env.int('VOICE_MAX_FILESIZE_MB', self.max_filesize_mb)
        self.rate_limit = env.int('VOICE_RATE_LIMIT', self.rate_limit)
        self.rate_period = env.int('VOICE_RATE_PERIOD', self.rate_period)
        
        # Log voice settings
        logger = logging.getLogger(__name__)
        logger.info(f"[VOICE] Max duration: {self.max_duration}s")
        logger.info(f"[VOICE] Max filesize: {self.max_filesize_mb}MB")
        logger.info(f"[VOICE] Rate limit: {self.rate_limit}/{self.rate_period}s")

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
    karma: KarmaConfig = field(default_factory=KarmaConfig)
    cards: CardConfig = field(default_factory=CardConfig)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    
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
