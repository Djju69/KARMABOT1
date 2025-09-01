"""
Настройки приложения KarmaSystem (новая версия).
"""
import os
import secrets
import logging
from datetime import timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator, PostgresDsn, AnyUrl

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    # Основные настройки
    DEBUG: bool = Field(default=False, env='DEBUG')
    ENVIRONMENT: str = Field(default='production', env='ENVIRONMENT')
    LOG_LEVEL: str = Field(default='INFO', env='LOG_LEVEL')
    
    # Настройки бота
    BOT_TOKEN: str = Field(..., env='BOT_TOKEN')
    ADMIN_ID: int = Field(..., env='ADMIN_ID')
    
    # Настройки базы данных
    DATABASE_URL: str = Field(
        default='sqlite:///core/database/data.db',
        env='DATABASE_URL'
    )
    
    # Настройки Redis
    REDIS_URL: str = Field(
        default='redis://localhost:6379/0',
        env='REDIS_URL'
    )
    
    # Настройки JWT
    SECRET_KEY: str = Field(
        default=secrets.token_urlsafe(32),
        env='SECRET_KEY'
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа
    
    # Настройки WebApp
    WEBAPP_HOST: str = Field(default='0.0.0.0', env='WEBAPP_HOST')
    WEBAPP_PORT: int = Field(default=8000, env='WEBAPP_PORT')
    WEBAPP_URL: str = Field(default='http://localhost:8000', env='WEBAPP_URL')
    
    # Настройки CORS
    CORS_ORIGINS: List[str] = Field(
        default=['*'],
        env='CORS_ORIGINS'
    )
    
    # Feature flags
    FEATURE_PARTNER_FSM: bool = Field(
        default=False,
        env='FEATURE_PARTNER_FSM'
    )
    FEATURE_MODERATION: bool = Field(
        default=False,
        env='FEATURE_MODERATION'
    )
    FEATURE_QR_WEBAPP: bool = Field(
        default=False,
        env='FEATURE_QR_WEBAPP'
    )
    FEATURE_LISTEN_NOTIFY: bool = Field(
        default=False,
        env='FEATURE_LISTEN_NOTIFY'
    )
    
    # Валидация URL базы данных
    @validator('DATABASE_URL', pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            path=f"/{os.getenv('DB_NAME', 'karmabot')}",
        )
    
    # Валидация CORS origins
    @validator('CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith('['):
            return [i.strip() for i in v.split(',')]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Инициализируем настройки
settings = Settings()

# Настраиваем логирование
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Логируем загрузку настроек
logger.info(f"Загружены настройки для окружения: {settings.ENVIRONMENT}")
logger.info(f"Режим отладки: {'ВКЛ' if settings.DEBUG else 'ВЫКЛ'}")
logger.info(f"Feature flags: PARTNER_FSM={settings.FEATURE_PARTNER_FSM}, "
           f"MODERATION={settings.FEATURE_MODERATION}, "
           f"QR_WEBAPP={settings.FEATURE_QR_WEBAPP}, "
           f"LISTEN_NOTIFY={settings.FEATURE_LISTEN_NOTIFY}")
