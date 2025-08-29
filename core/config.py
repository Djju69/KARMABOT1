from __future__ import annotations
from pydantic import BaseSettings, BaseModel, Field

def mask_token(token: str | None) -> str:
    """Securely mask a token for logging purposes.
    
    Args:
        token: The token to mask
        
    Returns:
        str: Masked token (first 4 and last 4 chars visible, rest masked)
    """
    if not token or not isinstance(token, str):
        return "<not_set>"
    token = token.strip()
    if len(token) <= 8:
        return "<invalid_length>"
    return f"{token[:4]}...{token[-4:]}"

class Bots(BaseModel):
    bot_token: str
    admin_id: int
    
    def masked_token(self) -> str:
        """Get a masked version of the bot token for logging."""
        return mask_token(self.bot_token)

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
