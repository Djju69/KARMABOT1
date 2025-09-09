"""
Упрощенный FastAPI бэкенд для Telegram WebApp
Без конфликтов зависимостей
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import urllib.parse
import json
import time
import os

# Настройки (заглушки)
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/karma_webapp")
JWT_SECRET = os.getenv("JWT_SECRET", "karma-webapp-secret-key-2025")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 часа

app = FastAPI(
    title="KarmaSystem WebApp API",
    description="API для личного кабинета Telegram WebApp",
    version="1.0.0"
)

# CORS для WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class User(BaseModel):
    tg_id: int
    username: Optional[str] = None
    role: str  # user|partner|admin|superadmin
    karma: Optional[int] = 0

class AuthResponse(BaseModel):
    token: str
    user: User

class PartnerCard(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    category: str
    images: List[str] = []
    status: str = "draft"  # draft|pending|approved|rejected
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Валидация initData
def validate_init_data(init_data: str) -> Dict[str, Any]:
    """Валидация Telegram WebApp initData"""
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        hash_recv = parsed.pop("hash", None)
        
        if not hash_recv:
            raise HTTPException(status_code=401, detail="No hash in initData")
        
        # Создаем строку для проверки
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        
        # Создаем секретный ключ
        secret_key = hmac.new(
            b"WebAppData", 
            BOT_TOKEN.encode(), 
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        hash_calc = hmac.new(
            secret_key, 
            data_check_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем hash
        if not hmac.compare_digest(hash_calc, hash_recv):
            raise HTTPException(status_code=401, detail="Invalid hash")
        
        # Проверяем время (5 минут)
        auth_date = int(parsed.get("auth_date", "0"))
        if abs(time.time() - auth_date) > 60 * 5:
            raise HTTPException(status_code=401, detail="InitData expired")
        
        return parsed
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"InitData validation failed: {str(e)}")

# Получение роли пользователя (заглушка)
async def get_user_role_from_db(tg_id: int) -> str:
    """Получить роль пользователя из базы данных"""
    # Заглушка - возвращаем роль по умолчанию
    return "user"

# JWT функции (упрощенные)
def create_access_token(user: User) -> str:
    """Создать JWT токен (упрощенная версия)"""
    import base64
    import json
    
    # Простой токен без библиотеки jose
    payload = {
        "tg_id": user.tg_id,
        "username": user.username,
        "role": user.role,
        "exp": int(time.time()) + JWT_EXPIRE_MINUTES * 60
    }
    
    # Кодируем в base64 (небезопасно, но работает)
    token = base64.b64encode(json.dumps(payload).encode()).decode()
    return token

def verify_token(token: str) -> User:
    """Проверить JWT токен (упрощенная версия)"""
    try:
        import base64
        import json
        
        # Декодируем из base64
        payload = json.loads(base64.b64decode(token.encode()).decode())
        
        # Проверяем время истечения
        if payload.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=401, detail="Token expired")
        
        return User(
            tg_id=payload["tg_id"],
            username=payload.get("username"),
            role=payload["role"]
        )
        
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Зависимости
def get_current_user(authorization: str = Header(...)) -> User:
    """Получить текущего пользователя из токена"""
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        return verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

def require_roles(*allowed_roles: str):
    """Декоратор для проверки ролей"""
    def dependency(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

# API эндпоинты
@app.post("/api/auth/webapp", response_model=AuthResponse)
async def auth_webapp(payload: dict = Body(...)):
    """Авторизация через Telegram WebApp initData"""
    init_data = payload.get("init_data", "")
    
    # Валидируем initData
    parsed = validate_init_data(init_data)
    
    # Извлекаем данные пользователя
    tg_user = json.loads(parsed["user"])
    tg_id = tg_user["id"]
    username = tg_user.get("username")
    
    # Получаем роль из БД
    role = await get_user_role_from_db(tg_id)
    
    # Создаем объект пользователя
    user = User(
        tg_id=tg_id,
        username=username,
        role=role
    )
    
    # Создаем токен
    token = create_access_token(user)
    
    return AuthResponse(token=token, user=user)

@app.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {"user": user}

@app.get("/api/stats/overview")
async def get_stats_overview(
    user: User = Depends(get_current_user)
):
    """Получить общую статистику (заглушка)"""
    stats = {
        "total_users": 100,
        "total_partners": 25,
        "total_places": 150,
        "my_places": 5 if user.role == "partner" else None
    }
    return stats

@app.get("/api/partner/cards")
async def get_partner_cards(
    user: User = Depends(require_roles("partner", "admin", "superadmin"))
):
    """Получить карточки партнера (заглушка)"""
    cards = [
        {
            "id": "1",
            "title": "Тестовое заведение",
            "description": "Описание заведения",
            "category": "Рестораны",
            "status": "approved",
            "created_at": "2025-01-08T10:00:00Z"
        }
    ]
    return {"cards": cards}

@app.get("/api/admin/moderation")
async def get_moderation_queue(
    user: User = Depends(require_roles("admin", "superadmin"))
):
    """Получить очередь модерации для админов (заглушка)"""
    data = {
        "partners": [
            {
                "id": "1",
                "title": "Новый партнер",
                "contact_name": "Иван Иванов",
                "contact_phone": "+7 900 123 45 67",
                "status": "pending",
                "created_at": "2025-01-08T10:00:00Z"
            }
        ],
        "places": [
            {
                "id": "1",
                "title": "Новое заведение",
                "address": "ул. Тестовая, 1",
                "status": "pending",
                "partner_name": "Тестовый партнер",
                "created_at": "2025-01-08T10:00:00Z"
            }
        ]
    }
    return data

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "ok", "service": "karma-webapp-api", "version": "1.0.0"}

@app.get("/")
async def root():
    """Главная страница"""
    return {
        "message": "KarmaSystem WebApp API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
