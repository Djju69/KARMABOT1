"""Monitoring and error tracking configuration."""
import os
import logging
import platform
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import field

# Import configuration
try:
    from core.config.monitoring import MonitoringSettings, DEFAULT_MONITORING_SETTINGS
except ImportError:
    from dataclasses import dataclass
    
    @dataclass
    class SentrySettings:
        dsn: Optional[str] = None
        environment: str = "development"
        traces_sample_rate: float = 1.0
    
    @dataclass
    class MonitoringSettings:
        enabled: bool = True
        sentry: SentrySettings = field(default_factory=SentrySettings)
        health_check_interval: int = 300
    
    DEFAULT_MONITORING_SETTINGS = MonitoringSettings()

# Try to import Sentry SDK
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global flag to track if monitoring is initialized
_monitoring_initialized = False


def get_system_info() -> Dict[str, Any]:
    """Get system information for monitoring."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "hostname": platform.node(),
        "startup_time": datetime.utcnow().isoformat(),
    }


def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging with appropriate handlers and formatting."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Configure third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def setup_monitoring(settings: Optional[MonitoringSettings] = None) -> bool:
    """Initialize monitoring and error tracking.
    
    Args:
        settings: Monitoring settings. If not provided, defaults will be used.
        
    Returns:
        bool: True if monitoring was initialized successfully, False otherwise.
    """
    global _monitoring_initialized
    
    if _monitoring_initialized:
        logger.warning("Monitoring already initialized")
        return True
    
    settings = settings or DEFAULT_MONITORING_SETTINGS
    
    if not settings.enabled:
        logger.info("Monitoring is disabled in settings")
        return False
    
    # Configure logging first
    configure_logging()
    
    # Initialize Sentry if available and configured
    sentry_initialized = False
    if SENTRY_AVAILABLE and settings.sentry and settings.sentry.dsn:
        try:
            sentry_sdk.init(
                dsn=settings.sentry.dsn,
                environment=settings.sentry.environment,
                traces_sample_rate=settings.sentry.traces_sample_rate,
                release=os.getenv("APP_VERSION"),
                integrations=[
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR
                    ),
                    AsyncioIntegration(),
                ],
                _experiments={
                    "enable_metrics": True,
                },
                **get_system_info()
            )
            sentry_initialized = True
            logger.info("Sentry monitoring initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)
    
    _monitoring_initialized = sentry_initialized or settings.enabled
    return _monitoring_initialized


def capture_exception(error: Exception, **kwargs) -> Optional[str]:
    """Capture and report an exception to the monitoring service.
    
    Args:
        error: The exception to capture
        **kwargs: Additional data to include with the event
        
    Returns:
        Optional[str]: Event ID if the event was captured, None otherwise
    """
    if not _monitoring_initialized or not SENTRY_AVAILABLE:
        return None
    
    try:
        return sentry_sdk.capture_exception(error, **kwargs)
    except Exception as e:
        logger.error(f"Failed to capture exception: {e}", exc_info=True)
        return None


def capture_message(message: str, level: str = "info", **kwargs) -> Optional[str]:
    """Capture a message to the monitoring service.
    
    Args:
        message: The message to capture
        level: The severity level (info, warning, error, fatal)
        **kwargs: Additional data to include with the event
        
    Returns:
        Optional[str]: Event ID if the message was captured, None otherwise
    """
    if not _monitoring_initialized or not SENTRY_AVAILABLE:
        return None
    
    try:
        return sentry_sdk.capture_message(message, level=level, **kwargs)
    except Exception as e:
        logger.error(f"Failed to capture message: {e}", exc_info=True)
        return None
