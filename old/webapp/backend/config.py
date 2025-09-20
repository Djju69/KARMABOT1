"""
Конфигурация для WebApp Backend
"""

import os

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/karma_webapp")

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

# JWT настройки
JWT_SECRET = os.getenv("JWT_SECRET", "karma-webapp-secret-key-2025")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 часа

# API настройки
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True
