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
    redis_url: str = ""

@dataclass
class FeatureFlags:
    partner_fsm: bool = False
    moderation: bool = False
    new_menu: bool = False
    qr_webapp: bool = False
    listen_notify: bool = False
    webapp_security: bool = False

@dataclass
class Settings:
    bots: Bots
    database: Database
    features: FeatureFlags
    log_level: str = "INFO"
    environment: str = "development"
    # Optional extended config (non-breaking)
    pdf_user_ru: str = ""
    pdf_user_en: str = ""
    pdf_user_vi: str = ""
    pdf_user_ko: str = ""
    pdf_partner_ru: str = ""
    pdf_partner_en: str = ""
    pdf_partner_vi: str = ""
    pdf_partner_ko: str = ""
    support_tg: str = ""
    webapp_qr_url: str = ""
    default_lang: str = "ru"
    default_city: str = ""
    # WebApp/JWT and security
    jwt_secret: str = ""
    # Split JWT secrets for domains with dual-key rotation (active/previous)
    jwt_user_secret_active: str = ""
    jwt_user_secret_previous: str = ""
    jwt_partner_secret_active: str = ""
    jwt_partner_secret_previous: str = ""
    jwt_admin_secret_active: str = ""
    jwt_admin_secret_previous: str = ""
    # Global kids for signing headers (active/previous)
    jwt_kid_active: str = ""
    jwt_kid_previous: str = ""
    # Access/Refresh and cookies (for email/password flow)
    access_ttl_sec: int = 900
    refresh_ttl_sec: int = 1209600  # 14 days
    cookie_secure: bool = True
    cookie_samesite: str = "Lax"  # Lax|Strict|None
    cookie_domain: str = ""
    csrf_secret: str = ""
    # Temporary partner test credentials (MVP, no DB)
    partner_login_email: str = ""
    partner_login_password_sha256: str = ""  # hex of sha256(password + pepper)
    partner_login_pepper: str = ""
    auth_window_sec: int = 300
    webapp_allowed_origin: str = ""
    csp_allowed_origin: str = ""
    # Reports
    report_max_req_per_hour: int = 3
    # Policy
    policy_version: int = 1

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
    
    # Allow running WebApp API without bot credentials (e.g., uvicorn web.main:app)
    fastapi_only = os.getenv("FASTAPI_ONLY", "0") == "1"
    if not bot_token and not fastapi_only:
        raise ValueError("BOT_TOKEN is required. Please set it in .env file or environment variables.")
    if not admin_id and not fastapi_only:
        raise ValueError("ADMIN_ID is required. Please set it in .env file or environment variables.")
    if fastapi_only:
        # Provide safe placeholders to satisfy dataclass types
        bot_token = bot_token or "debug"
        admin_id = admin_id or 1
    
    # Database configuration with Railway support
    database_url = env.str("DATABASE_URL", "sqlite:///core/database/data.db")
    
    # Railway/Render PostgreSQL support: normalize to asyncpg driver
    if database_url.startswith("postgresql+asyncpg://"):
        pass  # already normalized
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        # Handle legacy 'postgres://' scheme by upgrading to asyncpg
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    # Feature flags (all OFF by default for safety)
    features = FeatureFlags(
        partner_fsm=env.bool("FEATURE_PARTNER_FSM", False),
        moderation=env.bool("FEATURE_MODERATION", False),
        new_menu=env.bool("FEATURE_NEW_MENU", False),
        qr_webapp=env.bool("FEATURE_QR_WEBAPP", False),
        listen_notify=env.bool("FEATURE_LISTEN_NOTIFY", False),
        webapp_security=env.bool("FEATURE_WEBAPP_SECURITY", False)
    )
    
    return Settings(
        bots=Bots(bot_token=bot_token, admin_id=admin_id),
        database=Database(url=database_url, redis_url=env.str("REDIS_URL", "")),
        features=features,
        log_level=env.str("LOG_LEVEL", "INFO"),
        environment=env.str("ENVIRONMENT", "development"),
        pdf_user_ru=env.str("PDF_USER_RU", ""),
        pdf_user_en=env.str("PDF_USER_EN", ""),
        pdf_user_vi=env.str("PDF_USER_VI", ""),
        pdf_user_ko=env.str("PDF_USER_KO", ""),
        pdf_partner_ru=env.str("PDF_PARTNER_RU", ""),
        pdf_partner_en=env.str("PDF_PARTNER_EN", ""),
        pdf_partner_vi=env.str("PDF_PARTNER_VI", ""),
        pdf_partner_ko=env.str("PDF_PARTNER_KO", ""),
        support_tg=env.str("SUPPORT_TG", ""),
        # Default to production Railway domain if not provided to ensure WebApp links work (policy/help)
        webapp_qr_url=env.str("WEBAPP_QR_URL", "https://web-production-d51c7.up.railway.app"),
        default_lang=env.str("DEFAULT_LANG", "ru"),
        default_city=env.str("DEFAULT_CITY", ""),
        jwt_secret=env.str("JWT_SECRET", ""),
        jwt_user_secret_active=env.str("JWT_USER_SECRET_ACTIVE", env.str("JWT_USER_SECRET", "")),
        jwt_user_secret_previous=env.str("JWT_USER_SECRET_PREVIOUS", ""),
        jwt_partner_secret_active=env.str("JWT_PARTNER_SECRET_ACTIVE", env.str("JWT_PARTNER_SECRET", "")),
        jwt_partner_secret_previous=env.str("JWT_PARTNER_SECRET_PREVIOUS", ""),
        jwt_admin_secret_active=env.str("JWT_ADMIN_SECRET_ACTIVE", env.str("JWT_ADMIN_SECRET", "")),
        jwt_admin_secret_previous=env.str("JWT_ADMIN_SECRET_PREVIOUS", ""),
        jwt_kid_active=env.str("JWT_KID_ACTIVE", "main"),
        jwt_kid_previous=env.str("JWT_KID_PREVIOUS", ""),
        access_ttl_sec=env.int("ACCESS_TTL_SEC", 900),
        refresh_ttl_sec=env.int("REFRESH_TTL_SEC", 1209600),
        cookie_secure=env.bool("COOKIE_SECURE", True),
        cookie_samesite=env.str("COOKIE_SAMESITE", "Lax"),
        cookie_domain=env.str("COOKIE_DOMAIN", ""),
        csrf_secret=env.str("CSRF_SECRET", ""),
        partner_login_email=env.str("PARTNER_LOGIN_EMAIL", ""),
        partner_login_password_sha256=env.str("PARTNER_LOGIN_PASSWORD_SHA256", ""),
        partner_login_pepper=env.str("PARTNER_LOGIN_PEPPER", ""),
        auth_window_sec=env.int("AUTH_WINDOW_SEC", 300),
        webapp_allowed_origin=env.str("WEBAPP_ALLOWED_ORIGIN", "https://web-production-d51c7.up.railway.app"),
        csp_allowed_origin=env.str("CSP_ALLOWED_ORIGIN", "https://web-production-d51c7.up.railway.app"),
        report_max_req_per_hour=env.int("REPORT_MAX_REQ_PER_HOUR", 3),
        policy_version=env.int("POLICY_VERSION", 1)
    )

# Initialize settings (no print for security)
settings = get_settings()

# Validation on import
if settings.environment == "development":
    # Only show non-sensitive config in development
    # Avoid non-ASCII in Windows console to prevent UnicodeEncodeError
    print("[CONFIG] KARMABOT1 Config loaded:")
    print(f"   Database: {settings.database.url}")
    print(f"   Environment: {settings.environment}")
    print(f"   Features: {settings.features}")
    print(f"   Admin ID: {settings.bots.admin_id}")
    # Never print tokens, even in development
