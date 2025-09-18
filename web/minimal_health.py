"""
Minimal health check server for Railway
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем минимальное FastAPI приложение
app = FastAPI(title="KARMABOT1 Health Check", version="1.0.0")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "KARMABOT1 is running", "status": "ok"}

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    try:
        logger.info("Health check requested")
        return JSONResponse(
            content={
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "railway": os.getenv("RAILWAY_ENVIRONMENT") is not None
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=503
        )

@app.get("/healthz")
async def healthz():
    """Alternative health check endpoint"""
    return await health_check()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting minimal health server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
