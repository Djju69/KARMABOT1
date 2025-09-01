from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.settings import settings
import logging

app = FastAPI(
    title="KARMABOT1 Web API",
    description="Web API for KARMABOT1 Telegram bot",
    version="2.0.0"
)

# Настройка CORS
if getattr(settings, 'WEBAPP_ALLOWED_ORIGIN', None):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.WEBAPP_ALLOWED_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "version": "2.0.0"}

@app.post("/auth/webapp")
async def webapp_auth(data: dict):
    """Авторизация через Telegram WebApp"""
    init_data = data.get("initData")
    if not init_data:
        raise HTTPException(status_code=400, detail="initData is required")
    
    # TODO: Реализовать логику авторизации
    return {"token": "placeholder_token"}

@app.get("/auth/me")
async def get_user_info():
    """Получение информации о пользователе"""
    # TODO: Реализовать получение информации по токену
    return {"user_id": "placeholder", "username": "placeholder"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
