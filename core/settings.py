import os
import logging
from environs import Env
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Features:
    """Feature flags configuration"""
    new_menu: bool = field(default=True)  # Включено по умолчанию
    partner_fsm: bool = field(default=False)
    moderation: bool = field(default=False)
    qr_webapp: bool = field(default=False)
    listen_notify: bool = field(default=False)
    
    def __post_init__(self):
        """Initialize feature flags from environment variables"""
        env = Env()
        
        # Load from environment variables if they exist
        self.new_menu = env.bool('FEATURE_NEW_MENU', self.new_menu)
        self.partner_fsm = env.bool('FEATURE_PARTNER_FSM', self.partner_fsm)
        self.moderation = env.bool('FEATURE_MODERATION', self.moderation)
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
    
    # First try to load from environment variables directly
    # Only fall back to .env file if environment variables are not set
    if not os.environ.get('BOT_TOKEN') and path and os.path.exists(path):
        env.read_env(path)
        logger = logging.getLogger(__name__)
        logger.warning("Using .env file as fallback. It's recommended to use environment variables directly in production.")
    
    # Initialize features with default values
    # The __post_init__ will update from environment variables
    features = Features()
    
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
