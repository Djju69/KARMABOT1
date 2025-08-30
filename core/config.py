"""Configuration settings for the application."""
from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


def get_environment() -> str:
    """Get the current environment."""
    return os.getenv("ENVIRONMENT", "development").lower()


class Database(BaseModel):
    """Database configuration."""
    url: str | None = Field(
        default=None,
        env=["DATABASE__URL", "DATABASE_URL", "POSTGRES_URL", "POSTGRESQL_URL"],
        description="Database connection URL"
    )
    async_url: str | None = Field(
        default=None,
        description="Async database connection URL"
    )

    @property
    def dsn(self) -> str | None:
        """Get the database connection string (URL)."""
        return self.url or self.async_url


class Bots(BaseModel):
    """Bot-related configuration."""
    bot_token: str = Field(..., description="Telegram bot token")
    admin_id: int | None = Field(None, description="Admin user ID")
    
    @field_validator('bot_token', mode='before')
    @classmethod
    def validate_bot_token(cls, v: Any) -> str:
        """Validate and normalize bot token."""
        if not v:
            raise ValueError("Bot token cannot be empty")
            
        # If it's already a string, ensure it's stripped
        if isinstance(v, str):
            v = v.strip()
            
        # If it's a path-like object, read the token from file
        if hasattr(v, 'read'):
            v = v.read().strip()
        
        # Ensure token is in the correct format
        if not isinstance(v, str) or ':' not in v:
            raise ValueError(
                "Invalid bot token format. Expected format: '1234567890:ABCdefGHIjklmNOPQRSTUVWXYZ0123456789'"
            )
            
        return v
    
    def masked_token(self) -> str:
        """Get a masked version of the bot token for logging."""
        if not self.bot_token:
            return "<none>"
        return f"{self.bot_token[:4]}...{self.bot_token[-4:]}" if len(self.bot_token) > 8 else "***"


class FeatureFlags(BaseModel):
    """Feature flags for the application."""
    bot_enabled: bool = Field(True, description="Enable/disable the bot")
    partner_fsm: bool = Field(False, description="Enable partner FSM features")
    moderation: bool = Field(False, description="Enable moderation features")


class Settings(BaseSettings):
    """Application settings."""
    environment: str = Field(
        default="production",
        env=["ENVIRONMENT", "ENV", "APP_ENV", "RAILWAY_ENVIRONMENT", "RAILWAY_STAGE"],
        description="Application environment (development, production, etc.)"
    )
    bots: Bots
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    database: Database = Field(default_factory=Database)
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate the environment value."""
        return v.lower()

    class Config:
        """Pydantic configuration."""
        env_nested_delimiter = "__"
        case_sensitive = False
        env_file = ".env" if get_environment() != "production" else None
        env_file_encoding = "utf-8"
        extra = "ignore"


def load_settings() -> Settings:
    """Load and validate settings with proper error handling and logging.
    
    Returns:
        Settings: The loaded settings
        
    Raises:
        ValueError: If required settings are missing or invalid
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log environment information for debugging
    env_vars = {
        'ENVIRONMENT': os.getenv('ENVIRONMENT'),
        'BOTS__BOT_TOKEN': os.getenv('BOTS__BOT_TOKEN'),
        'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT')
    }
    logger.debug("Environment variables: %s", 
                {k: f"{v[:4]}...{v[-4:]}" if k == 'BOTS__BOT_TOKEN' and v else v 
                 for k, v in env_vars.items()})
    
    try:
        # Try to load settings with environment variables
        settings = Settings()
        logger.info("Successfully loaded settings")
        logger.debug("Bot token (masked): %s", 
                    settings.bots.masked_token() if hasattr(settings, 'bots') else 'N/A')
        return settings
        
    except Exception as e:
        logger.error("Failed to load settings: %s", str(e), exc_info=True)
        
        # Check for common issues
        token = os.getenv("BOTS__BOT_TOKEN")
        if not token:
            error_msg = (
                "BOTS__BOT_TOKEN environment variable is required. "
                "Please set it before starting the application."
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e
            
        # Check token format
        if ':' not in token:
            error_msg = (
                "Invalid token format. Expected format: '1234567890:ABCdefGHIjklmNOPQRSTUVWXYZ0123456789'\n"
                f"Current token (first 10 chars): {token[:10]!r}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e
            
        # If we get here, the error is something else
        logger.error("Unexpected error loading settings")
        raise


# Global settings instance
settings = load_settings()
