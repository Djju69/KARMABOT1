from __future__ import annotations
from pydantic import BaseSettings, BaseModel, Field

class Bots(BaseModel):
    bot_token: str
    admin_id: int

class FeatureFlags(BaseModel):
    partner_fsm: bool = False
    loyalty_points: bool = True
    referrals: bool = True
    web_cabinets: bool = True

class Settings(BaseSettings):
    bots: Bots
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    class Config:
        env_nested_delimiter = "__"   # FEATURES__PARTNER_FSM=1 и т.п.
        case_sensitive = False

# Глобальный экземпляр (если у вас так принято)
settings = Settings()
