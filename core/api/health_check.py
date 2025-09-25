"""
Health check endpoint для мониторинга состояния базы данных
"""
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from core.database.postgresql_service import PostgreSQLService
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# Создаем экземпляр сервиса для healthcheck
database_url = os.getenv('DATABASE_URL')
if database_url:
    db_service = PostgreSQLService(database_url)
else:
    db_service = None

@router.get("/health/database")
async def database_health_check():
    """Health check для базы данных"""
    if not db_service:
        raise HTTPException(status_code=503, detail="Database service not initialized")
    
    try:
        # Проверяем соединение
        is_healthy = await db_service.health_check()
        
        if is_healthy:
            return {
                "status": "healthy",
                "database": "connected",
                "message": "Database connection is stable"
            }
        else:
            raise HTTPException(status_code=503, detail="Database health check failed")
            
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@router.get("/health")
async def general_health_check():
    """Общий health check"""
    return {
        "status": "healthy",
        "service": "karmabot",
        "message": "Service is running"
    }
