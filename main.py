from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.platform_endpoints import main_router
from core.database.enhanced_unified_service import enhanced_unified_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    }
)

# CORS middleware для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📝 {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"📤 {request.method} {request.url} - {response.status_code}")
    return response

# Подключение роутеров API
app.include_router(main_router, prefix="/v1")

# Статические файлы для dashboard
dashboard_path = Path(__file__).parent / "dashboard"
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=dashboard_path), name="static")

# Маршрут для dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Показать системный dashboard"""
    dashboard_file = Path(__file__).parent / "dashboard" / "system_dashboard.html"
    
    if dashboard_file.exists():
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>Dashboard not found</h1>
                <p>Please ensure dashboard/system_dashboard.html exists</p>
            </body>
        </html>
        """)

# События запуска и остановки
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Starting Fault-Tolerant Multi-Platform System")
    
    # Инициализация баз данных
    try:
        enhanced_unified_db.init_databases()
        logger.info("✅ Database initialization completed")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Проверка здоровья системы
    health_status = enhanced_unified_db.health_check()
    logger.info(f"🏥 System health: {health_status['mode']}")
    
    logger.info("🌟 System ready to handle multi-platform requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    logger.info("🛑 Shutting down Fault-Tolerant Multi-Platform System")
    
    # Принудительная синхронизация перед остановкой
    try:
        sync_result = enhanced_unified_db.force_system_sync()
        logger.info(f"📥 Final sync completed: {sync_result}")
    except Exception as e:
        logger.error(f"❌ Final sync failed: {e}")
    
    logger.info("✅ System shutdown completed")

# Дополнительные маршруты для удобства
@app.get("/")
async def root():
    """Корневая страница с информацией о системе"""
    return {
        "service": "🛡️ Fault-Tolerant Multi-Platform System",
        "version": "1.0.0",
        "status": "operational",
        "description": "Отказоустойчивая система для управления пользователями и заказами на множественных платформах",
        "platforms": {
            "telegram": "Telegram Bot integration",
            "website": "Web platform support",
            "mobile": "iOS and Android apps",
            "desktop": "Windows, Mac, Linux applications",
            "api": "Partner API access"
        },
        "features": [
            "🔄 Automatic failover between databases",
            "💾 Local caching for offline operations",
            "🔗 Cross-platform account linking",
            "📊 Real-time monitoring and alerts",
            "🛡️ Fault-tolerant architecture"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "dashboard": "/dashboard",
            "health": "/v1/admin/health",
            "platforms": "/v1/platforms"
        },
        "current_time": enhanced_unified_db.get_current_timestamp()
    }

@app.get("/status")
async def quick_status():
    """Быстрая проверка статуса системы"""
    try:
        health = enhanced_unified_db.health_check()
        return {
            "status": "ok" if health['health']['overall'] else "degraded",
            "mode": health['mode'],
            "databases": {
                "postgresql": "✅" if health['health']['postgresql']['status'] else "❌",
                "supabase": "✅" if health['health']['supabase']['status'] else "❌"
            },
            "uptime": f"{health['uptime']['overall']}%",
            "timestamp": health['timestamp']
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": enhanced_unified_db.get_current_timestamp()
        }

# Обработчики ошибок
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return {
        "error": "Not Found",
        "message": f"Path {request.url.path} not found",
        "available_endpoints": {
            "api": "/v1/",
            "docs": "/docs",
            "dashboard": "/dashboard",
            "status": "/status"
        }
    }

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": enhanced_unified_db.get_current_timestamp()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Конфигурация для запуска
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "log_level": "info",
        "reload": os.getenv("ENVIRONMENT", "production") == "development"
    }
    
    logger.info(f"🚀 Starting server on {config['host']}:{config['port']}")
    uvicorn.run("main:app", **config)
