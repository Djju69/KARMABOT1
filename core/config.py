"""Configuration settings for the application."""
from __future__ import annotations

import os
import sys
import logging
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# Надёжный фоллбэк: pydantic_settings (v2) → pydantic.BaseSettings (v1) → BaseModel
try:
    from pydantic_settings import BaseSettings as _BaseSettings  # pydantic v2
except Exception:
    try:
        from pydantic import BaseSettings as _BaseSettings       # pydantic v1
    except Exception:
        _BaseSettings = BaseModel                                # фоллбэк без BaseSettings

IS_PROD = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production")

def _pick_bot_token() -> str:
    """Get and validate bot token from environment variables."""
    # Primary source
    primary = os.getenv("BOT_TOKEN", "").strip()
    # Legacy source (for backward compatibility)
    legacy = os.getenv("BOTS__BOT_TOKEN", "").strip()

    if primary and legacy and primary != legacy:
        log.error("BOT_TOKEN и BOTS__BOT_TOKEN заданы и РАЗНЫЕ — используем BOT_TOKEN и игнорируем legacy")
    
    token = primary or legacy
    if not token:
        log.critical("❌ Не найден BOT_TOKEN (или BOTS__BOT_TOKEN) в переменных окружения")
        sys.exit(1)
    
    # Mask token for logging
    mask = token[:8] + "…" + token[-6:] if len(token) > 14 else "***"
    log.info(f"✅ Используется BOT_TOKEN={mask}")
    return token

class Bots(BaseModel):
    # Use the token from environment with proper validation
    bot_token: str = Field(default_factory=_pick_bot_token)
    
    admin_id: int | None = Field(default_factory=lambda: (
        int(os.getenv("ADMIN_ID") or os.getenv("BOTS__ADMIN_ID") or "0") or None
    ))

    def masked_token(self) -> str:
        t = self.bot_token or ""
        return f"{t[:8]}…{t[-6:]}" if len(t) > 14 else ("***" if t else "<none>")

class FeatureFlags(BaseModel):
    partner_fsm: bool = Field(default=False, description="Enable FSM for partner interactions")
    moderation: bool = Field(default=False, description="Enable moderation features")
    bot_enabled: bool = Field(default=True, description="Global bot enabled/disabled")
    new_menu: bool = Field(
        default=os.getenv("FEATURE_NEW_MENU", "false").lower() == "true",
        description="Enable new menu layout with 3 rows"
    )
    qr_webapp: bool = Field(default=False, description="Enable QR code webapp functionality")
    listen_notify: bool = Field(default=False, description="Enable database notifications")
    
    def __init__(self, **data):
        # First set defaults
        default_values = {
            'partner_fsm': False,
            'moderation': False,
            'bot_enabled': True,
            'new_menu': False,
            'qr_webapp': False,
            'listen_notify': False
        }
        
        # Update with any provided values
        default_values.update(data)
        
        # Handle environment variables if not explicitly set
        if 'new_menu' not in data:
            default_values['new_menu'] = os.getenv("FEATURE_NEW_MENU", "false").lower() == "true"
            
        super().__init__(**default_values)
        
        # Log feature flags on initialization
        self._log_feature_flags()
    
    def _log_feature_flags(self):
        """Log current feature flags status"""
        flags = [f"{k}={v}" for k, v in self.dict().items()]
        log.info(f"[FEATURE_FLAGS] {', '.join(flags)}")
    
    class Config:
        extra = "allow"

class Database(BaseModel):
    # не используем validation_alias, чтобы не зависеть от версии pydantic
    url: str | None = Field(default_factory=lambda: (
        os.getenv("DATABASE__URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRESQL_URL")
        or None
    ))
    async_url: str | None = None

    @property
    def dsn(self) -> str | None:
        return self.url or self.async_url

class Settings(_BaseSettings):
    bots: Bots = Field(default_factory=Bots)
    environment: str = Field(
        default=os.getenv("ENVIRONMENT")
             or os.getenv("ENV")
             or os.getenv("APP_ENV")
             or os.getenv("RAILWAY_ENVIRONMENT")
             or os.getenv("RAILWAY_STAGE")
             or "production"
    )
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    database: Database = Field(default_factory=Database)

    class Config:
        # если мы реально на BaseSettings, эти поля применятся; если на BaseModel — не помешают
        env_nested_delimiter = "__"
        case_sensitive = False
        env_file = ".env" if not IS_PROD else None
        env_file_encoding = "utf-8"

def load_settings() -> Settings:
    return Settings()
