"""Configuration settings for the application."""
from __future__ import annotations

from __future__ import annotations
import os
from pydantic import BaseModel, Field

# Надёжный фоллбэк: pydantic_settings (v2) → pydantic.BaseSettings (v1) → BaseModel
try:
    from pydantic_settings import BaseSettings as _BaseSettings  # pydantic v2
except Exception:
    try:
        from pydantic import BaseSettings as _BaseSettings       # pydantic v1
    except Exception:
        _BaseSettings = BaseModel                                # фоллбэк без BaseSettings

IS_PROD = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production")

class Bots(BaseModel):
    # берём токен из окружения, чтобы не падать, если Settings соберётся без BaseSettings
    bot_token: str = Field(default_factory=lambda: (
        os.getenv("BOTS__BOT_TOKEN")
        or os.getenv("BOT_TOKEN")
        or ""
    ))
    admin_id: int | None = Field(default_factory=lambda: (
        int(os.getenv("BOTS__ADMIN_ID")) 
        if os.getenv("BOTS__ADMIN_ID") and os.getenv("BOTS__ADMIN_ID").isdigit() 
        else None
    ))

    def masked_token(self) -> str:
        t = self.bot_token or ""
        return f"{t[:8]}…{t[-6:]}" if len(t) > 14 else ("***" if t else "<none>")

class FeatureFlags(BaseModel):
    partner_fsm: bool = False
    moderation: bool = False
    bot_enabled: bool = True
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
