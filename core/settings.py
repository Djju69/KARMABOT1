"""
KARMABOT1 Settings with backward compatibility and .env support
Following Non-Breaking Dev Guide rules
"""
import os
from environs import Env
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Bots:
    bot_token: str
    admin_id: int

@dataclass
class Database:
    url: str

@dataclass
class FeatureFlags:
    partner_fsm: bool = False
    moderation: bool = False
    new_menu: bool = False
    qr_webapp: bool = False
    listen_notify: bool = False

@dataclass
class Settings:
    bots: Bots
    database: Database
    features: FeatureFlags
    log_level: str = "INFO"
    environment: str = "development"

def get_settings(env_path: Optional[str] = None) -> Settings:
    """
    Load settings with fallback strategy for backward compatibility
    
    Priority:
    1. .env file (new way)
    2. Environment variables
    3. Legacy 'input' file (fallback for existing deployments)
    """
    env = Env()
    
    # Try to load .env file first (new way)
    if env_path and Path(env_path).exists():
        env.read_env(env_path)
    elif Path('.env').exists():
        env.read_env('.env')
    
    # Fallback to legacy 'input' file for backward compatibility
    legacy_input_path = Path('input')
    if legacy_input_path.exists() and not os.getenv('BOT_TOKEN'):
        try:
            env.read_env('input')
        except Exception:
            pass  # Silently fail if input file is corrupted
    
    # Get bot configuration with fallbacks
    bot_token = env.str("BOT_TOKEN", env.str("TOKEN", ""))
    admin_id = env.int("ADMIN_ID", 0)
    
    if not bot_token:
        raise ValueError("BOT_TOKEN is required. Please set it in .env file or environment variables.")
    
    if not admin_id:
        raise ValueError("ADMIN_ID is required. Please set it in .env file or environment variables.")
    
    # Database configuration with Railway support
    database_url = env.str("DATABASE_URL", "sqlite:///core/database/data.db")
    
    # Railway PostgreSQL support
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Feature flags (all OFF by default for safety)
    features = FeatureFlags(
        partner_fsm=env.bool("FEATURE_PARTNER_FSM", False),
        moderation=env.bool("FEATURE_MODERATION", False),
        new_menu=env.bool("FEATURE_NEW_MENU", False),
        qr_webapp=env.bool("FEATURE_QR_WEBAPP", False),
        listen_notify=env.bool("FEATURE_LISTEN_NOTIFY", False)
    )
    
    return Settings(
        bots=Bots(bot_token=bot_token, admin_id=admin_id),
        database=Database(url=database_url),
        features=features,
        log_level=env.str("LOG_LEVEL", "INFO"),
        environment=env.str("ENVIRONMENT", "development")
    )

# Initialize settings (no print for security)
settings = get_settings()

# Validation on import
if settings.environment == "development":
    # Only show non-sensitive config in development
    print(f"🔧 KARMABOT1 Config loaded:")
    print(f"   Database: {settings.database.url}")
    print(f"   Environment: {settings.environment}")
    print(f"   Features: {settings.features}")
    print(f"   Admin ID: {settings.bots.admin_id}")
    # Never print tokens, even in development
