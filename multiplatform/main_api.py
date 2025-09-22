"""
Главный файл для запуска мульти-платформенной системы
FastAPI сервер с отказоустойчивостью и мониторингом
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.platform_endpoints import main_router
from database.enhanced_unified_service import enhanced_unified_db
from monitoring.system_monitor import SystemMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальная переменная для монитора
system_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global system_monitor
    
    # Startup
    logger.info("🚀 Starting Multi-Platform System...")
    
    try:
        # Инициализация баз данных
        enhanced_unified_db.init_databases()
        logger.info("✅ Enhanced unified database initialized")
        
        # Запуск мониторинга системы
        system_monitor = SystemMonitor()
        monitoring_task = asyncio.create_task(system_monitor.run_monitoring_loop())
        logger.info("🔍 System monitoring started")
        
        logger.info("✅ Multi-Platform System started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Multi-Platform System: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Multi-Platform System...")
    
    if system_monitor:
        logger.info("🔍 System monitoring stopped")
    
    logger.info("✅ Multi-Platform System shutdown complete")

# Создание FastAPI приложения
app = FastAPI(
    title="🛡️ Fault-Tolerant Multi-Platform System",
    description="""
    Отказоустойчивая многоплатформенная система с поддержкой:
    - 🤖 Telegram Bot
    - 🌐 Website
    - 📱 Mobile Apps (iOS/Android)
    - 🖥️ Desktop Apps (Windows/Mac/Linux)
    - 🔗 Partner API
    
    Система автоматически переключается между PostgreSQL (Railway) и Supabase,
    использует локальный кеш для обеспечения непрерывной работы.
    """,
    version="1.0.0",
    contact={
        "name": "System Administrator",
        "email": "admin@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации запросов"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "timestamp": "2025-01-01T00:00:00Z"
        }
    )

# Подключение роутеров
app.include_router(main_router, prefix="/v1")

# Статические файлы для дашборда
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

# Корневой endpoint
@app.get("/")
async def root():
    """Корневой endpoint с информацией о системе"""
    return {
        "message": "🛡️ Fault-Tolerant Multi-Platform System",
        "version": "1.0.0",
        "status": "operational",
        "platforms": ["telegram", "website", "mobile", "desktop", "api"],
        "features": [
            "fault-tolerance",
            "cross-platform-sync", 
            "monitoring",
            "admin-dashboard",
            "real-time-alerts"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "dashboard": "/dashboard/system_dashboard.html",
            "health": "/v1/health",
            "admin_status": "/v1/admin/status"
        },
        "timestamp": "2025-01-01T00:00:00Z"
    }

# Endpoint для дашборда
@app.get("/dashboard/", response_class=HTMLResponse)
async def dashboard():
    """Перенаправление на дашборд"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>System Dashboard</title>
        <meta http-equiv="refresh" content="0; url=/dashboard/system_dashboard.html">
    </head>
    <body>
        <p>Redirecting to dashboard...</p>
        <script>window.location.href = '/dashboard/system_dashboard.html';</script>
    </body>
    </html>
    """)

# Endpoint для проверки здоровья
@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    try:
        from database.fault_tolerant_service import fault_tolerant_db
        system_status = fault_tolerant_db.get_system_status()
        
        return {
            "status": "healthy" if system_status['health']['overall'] else "degraded",
            "mode": system_status['mode'],
            "timestamp": system_status['timestamp'],
            "components": {
                "postgresql": system_status['health']['postgresql']['status'],
                "supabase": system_status['health']['supabase']['status'],
                "cache": system_status['cache']['total_items'] > 0,
                "queue": system_status['queue']['total_operations']
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-01-01T00:00:00Z"
        }

# Endpoint для получения статуса мониторинга
@app.get("/monitoring/status")
async def monitoring_status():
    """Статус мониторинга системы"""
    global system_monitor
    
    if not system_monitor:
        return {"status": "monitoring_not_initialized"}
    
    return system_monitor.get_monitoring_status()

# Endpoint для принудительной синхронизации
@app.post("/admin/sync")
async def force_sync():
    """Принудительная синхронизация всех отложенных операций"""
    try:
        from database.fault_tolerant_service import fault_tolerant_db
        result = fault_tolerant_db.force_sync_all_pending()
        
        return {
            "status": "success",
            "message": "Sync operation completed",
            "result": result,
            "timestamp": "2025-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Force sync failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": "2025-01-01T00:00:00Z"
        }

if __name__ == "__main__":
    import uvicorn
    
    # Настройки для запуска - ПОРТ 8001
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))  # ИСПРАВЛЕНО: порт 8001
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"📚 API Documentation: http://{host}:{port}/docs")
    logger.info(f"📊 Dashboard: http://{host}:{port}/dashboard/")
    logger.info(f"🔍 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "main_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
