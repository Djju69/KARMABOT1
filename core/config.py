from __future__ import annotations
from pydantic import BaseSettings, BaseModel, Field

class Bots(BaseModel):
    bot_token: str
    admin_id: int

class FeatureFlags(BaseModel):
    # Явные флаги, используемые в проекте
    partner_fsm: bool = False
    moderation: bool = False
    loyalty_points: bool = True
    referrals: bool = True
    web_cabinets: bool = True
    anti_flood: bool = True
    rate_limit: bool = True
    captcha: bool = False
    support_ai: bool = False
    partner_portal: bool = True
    web_qr: bool = True

    class Config:
        extra = "allow"  # позволяем незадекларированные флаги из ENV

    def __getattr__(self, name: str) -> bool:
        # Любой неизвестный флаг — безопасно считаем выключенным
        return False

class Settings(BaseSettings):
    bots: Bots
    # Читаем из нескольких популярных переменных окружения
    environment: str = Field(
        default="prod",
        env=["ENVIRONMENT", "ENV", "APP_ENV", "RAILWAY_ENVIRONMENT", "RAILWAY_STAGE"],
    )
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    class Config:
        env_nested_delimiter = "__"   # FEATURES__MODERATION=1 и т.д.
        case_sensitive = False

# Глобальный экземпляр
settings = Settings()
