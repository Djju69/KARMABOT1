from __future__ import annotations
from pydantic import BaseSettings, BaseModel, Field

class Bots(BaseModel):
    bot_token: str
    admin_id: int = 6391215556

    def masked_token(self) -> str:
        t = self.bot_token or ""
        return f"{t[:8]}…{t[-6:]}" if len(t) > 14 else ("***" if t else "<none>")

class FeatureFlags(BaseModel):
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
    bot_enabled: bool = True

    class Config:
        extra = "allow"

    def __getattr__(self, name: str) -> bool:
        return False

class Settings(BaseSettings):
    bots: Bots
    environment: str = Field(
        default="production",
        env=["ENVIRONMENT", "ENV", "APP_ENV", "RAILWAY_ENVIRONMENT", "RAILWAY_STAGE"],
        description="Application environment (production/staging/development)"
    )
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    class Config:
        env_nested_delimiter = "__"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

# Глобальный экземпляр
settings = Settings()
