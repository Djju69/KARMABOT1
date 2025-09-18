"""Test endpoints for monitoring and debugging."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception, metrics
import logging
import psutil
import os

router = APIRouter(tags=["test"])
logger = logging.getLogger(__name__)

@router.get("/test/error")
async def test_error():
    """
    Генерация тестовой ошибки для проверки мониторинга.
    
    Исключение будет залогировано и отправлено в Sentry.
    """
    try:
        # Генерируем ошибку
        result = 1 / 0
        return {"result": result}
    except Exception as e:
        logger.error("Произошла тестовая ошибка", exc_info=True)
        capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail="Тестовая ошибка отправлена в Sentry"
        )

@router.get("/test/metrics")
async def test_metrics():
    """
    Тест отправки кастомных метрик в Sentry.
    
    Увеличивает счётчик test_metric и возвращает информацию о системе.
    """
    # Увеличиваем счётчик
    metrics.incr("test_metric", value=1)
    
    # Собираем информацию о системе
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "status": "success",
        "metrics": {
            "test_metric": "incremented"
        },
        "system": {
            "process_id": os.getpid(),
            "memory_usage_mb": memory_info.rss / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent(),
            "process_memory_percent": process.memory_percent()
        }
    }

@router.get("/test/logs")
async def test_logs():
    """
    Тест логирования на разных уровнях.
    
    Генерирует логи разных уровней для проверки их отображения в Sentry.
    """
    logger.debug("Это DEBUG сообщение")
    logger.info("Это INFO сообщение")
    logger.warning("Это WARNING сообщение")
    logger.error("Это ERROR сообщение")
    
    return {
        "status": "success",
        "message": "Тестовые логи сгенерированы"
    }
