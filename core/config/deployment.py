"""
Deployment Configuration
Автоматический выбор webhook/polling на основе окружения
"""
import os
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

class DeploymentMode(str, Enum):
    WEBHOOK = "webhook"
    POLLING = "polling"

class Platform(str, Enum):
    RAILWAY = "railway"
    HEROKU = "heroku"
    LOCAL = "local"

@dataclass
class DeploymentConfig:
    """Конфигурация развертывания"""
    mode: DeploymentMode
    platform: Platform
    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook"
    port: int = 8080
    host: str = "0.0.0.0"
    
    @property
    def full_webhook_url(self) -> Optional[str]:
        if self.mode == DeploymentMode.WEBHOOK and self.webhook_url:
            return f"{self.webhook_url}{self.webhook_path}"
        return None

def detect_platform() -> Platform:
    """Автоопределение платформы"""
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return Platform.RAILWAY
    elif os.getenv("DYNO"):
        return Platform.HEROKU
    return Platform.LOCAL

def get_deployment_config() -> DeploymentConfig:
    """
    Получить конфигурацию развертывания
    
    ЕДИНСТВЕННОЕ место где решается webhook или polling
    """
    platform = detect_platform()
    logger.info(f"🔍 Platform: {platform.value}")
    
    # Явное указание (приоритет)
    explicit_mode = os.getenv("DEPLOYMENT_MODE", "").lower()
    if explicit_mode in ["webhook", "polling"]:
        mode = DeploymentMode(explicit_mode)
    else:
        # Автовыбор
        mode = (DeploymentMode.WEBHOOK 
                if platform in [Platform.RAILWAY, Platform.HEROKU]
                else DeploymentMode.POLLING)
    
    logger.info(f"🔧 Mode: {mode.value}")
    
    # Webhook URL
    webhook_url = None
    if mode == DeploymentMode.WEBHOOK:
        railway_url = os.getenv("RAILWAY_STATIC_URL")
        if railway_url:
            webhook_url = f"https://{railway_url}"
        else:
            webhook_url = os.getenv("WEBHOOK_URL")
        
        if not webhook_url:
            raise ValueError(
                f"Webhook mode требует WEBHOOK_URL для {platform.value}"
            )
    
    config = DeploymentConfig(
        mode=mode,
        platform=platform,
        webhook_url=webhook_url,
        port=int(os.getenv("PORT", 8080)),
    )
    
    logger.info(f"📋 Config: {config}")
    return config

# Singleton
_config = None

def get_config() -> DeploymentConfig:
    global _config
    if _config is None:
        _config = get_deployment_config()
    return _config
