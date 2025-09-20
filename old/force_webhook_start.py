#!/usr/bin/env python3
"""
Force webhook mode and fix Railway deployment
"""
import os
import sys
import asyncio
import logging
import uvicorn
from pathlib import Path
from datetime import datetime

print("🚨 START.PY LOADED - DEPLOYMENT MARKER V3.0")
print("✅ IMPORTS LOADED SUCCESSFULLY")

# FORCE WEBHOOK ENVIRONMENT
os.environ['RAILWAY_ENVIRONMENT'] = 'production'
os.environ['DISABLE_POLLING'] = 'true'
os.environ['RAILWAY_STATIC_URL'] = 'https://web-production-d51c7.up.railway.app/'

print("🔧 FORCED ENVIRONMENT VARIABLES:")
print(f"  RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT')}")
print(f"  DISABLE_POLLING: {os.getenv('DISABLE_POLLING')}")
print(f"  RAILWAY_STATIC_URL: {os.getenv('RAILWAY_STATIC_URL')}")

# Continue with normal imports
# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

def is_railway_environment():
    """Проверка запуска на Railway"""
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    logger.info(f"🔍 RAILWAY_ENVIRONMENT: '{railway_env}'")
    logger.info(f"🔍 RAILWAY_STATIC_URL: '{railway_url}'")

    # FORCE WEBHOOK MODE FOR RAILWAY
    if railway_env or os.getenv('RAILWAY_PROJECT_ID'):
        logger.info("🚀 FORCE ENABLING WEBHOOK MODE FOR RAILWAY")
        os.environ['RAILWAY_ENVIRONMENT'] = 'production'
        os.environ['DISABLE_POLLING'] = 'true'
        return True

    return railway_env is not None
