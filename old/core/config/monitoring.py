"""Monitoring and observability configuration."""
from typing import Optional
from pydantic import BaseModel, Field

class SentrySettings(BaseModel):
    """Sentry configuration settings."""
    dsn: Optional[str] = Field(
        None,
        description="Sentry DSN for error tracking. If not set, Sentry will be disabled."
    )
    environment: str = Field(
        "development",
        description="Environment name (e.g., development, staging, production)"
    )
    traces_sample_rate: float = Field(
        1.0,
        description="Sample rate for performance tracing (0.0 - 1.0)",
        ge=0.0,
        le=1.0
    )

class MonitoringSettings(BaseModel):
    """Monitoring and observability settings."""
    enabled: bool = Field(
        True,
        description="Enable monitoring features"
    )
    sentry: SentrySettings = Field(
        default_factory=SentrySettings,
        description="Sentry error tracking configuration"
    )
    health_check_interval: int = Field(
        300,
        description="Health check interval in seconds",
        gt=0
    )

    class Config:
        env_prefix = "MONITORING_"
        env_nested_delimiter = "__"

# Default monitoring settings
DEFAULT_MONITORING_SETTINGS = MonitoringSettings()
