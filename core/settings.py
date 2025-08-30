import os
from environs import Env
from dataclasses import dataclass
from typing import Optional

@dataclass
class Features:
    """Feature flags configuration"""
    new_menu: bool = False
    partner_fsm: bool = False
    moderation: bool = False
    qr_webapp: bool = False
    listen_notify: bool = False

@dataclass
class Bots:
    bot_token: str
    admin_id: int

@dataclass
class Settings:
    bots: Bots
    features: Features

def get_settings(path: Optional[str] = None):
    """Load settings from environment variables"""
    env = Env()
    
    # Load from .env file if path is provided
    if path and os.path.exists(path):
        env.read_env(path)
    
    # Load feature flags from environment variables
    features = Features(
        new_menu=env.bool('FEATURE_NEW_MENU', False),
        partner_fsm=env.bool('FEATURE_PARTNER_FSM', False),
        moderation=env.bool('FEATURE_MODERATION', False),
        qr_webapp=env.bool('FEATURE_QR_WEBAPP', False),
        listen_notify=env.bool('FEATURE_LISTEN_NOTIFY', False)
    )
    
    return Settings(
        bots=Bots(
            bot_token=env.str("BOT_TOKEN"),
            admin_id=env.int("ADMIN_ID")
        ),
        features=features
    )

# Initialize settings
settings = get_settings('.env')

# Log feature flags status
print("\n=== Feature Flags ===")
for feature, value in settings.features.__dict__.items():
    print(f"{feature}: {value}")
print("==================\n")
