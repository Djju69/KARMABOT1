"""
FastAPI бэкенд для Telegram WebApp
Обеспечивает API для личного кабинета KarmaSystem
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import urllib.parse
import json
import time
import os
from jose import jwt, JWTError
import asyncpg
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем конфигурацию
from config import DATABASE_URL, BOT_TOKEN, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

# Настройки (заглушка, так как core.settings недоступен)
class Settings:
    def __init__(self):
        self.database_url = DATABASE_URL
        self.bots = type('Bots', (), {'token': BOT_TOKEN})()

settings = Settings()

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

security = HTTPBearer()

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

# Получение роли пользователя из БД
async def get_user_role_from_db(tg_id: int) -> str:
    """Получить роль пользователя из базы данных"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        try:
            role = await conn.fetchval(
                "SELECT role FROM users WHERE telegram_id = $1",
                tg_id
            )
            return role or "user"
        finally:
            await conn.close()
    except Exception as e:
        print(f"Error getting user role: {e}")
        return "user"

# JWT функции
def create_access_token(user: User) -> str:
    """Создать JWT токен"""
    to_encode = user.model_dump()
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> User:
    """Проверить JWT токен"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return User(**payload)
    except JWTError:
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

@app.get("/api/partner/cards")
async def get_partner_cards(
    user: User = Depends(require_roles("partner", "admin", "superadmin"))
):
    """Получить карточки партнера"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        try:
            if user.role == "partner":
                # Партнер видит только свои карточки
                cards = await conn.fetch("""
                    SELECT id, title, description, category, status, created_at, updated_at
                    FROM partner_places 
                    WHERE partner_id = (
                        SELECT id FROM partners WHERE telegram_id = $1
                    )
                    ORDER BY created_at DESC
                """, user.tg_id)
            else:
                # Админы видят все карточки
                cards = await conn.fetch("""
                    SELECT pp.id, pp.title, pp.description, pp.category, pp.status, 
                           pp.created_at, pp.updated_at, p.title as partner_name
                    FROM partner_places pp
                    JOIN partners p ON pp.partner_id = p.id
                    ORDER BY pp.created_at DESC
                """)
            
            return {"cards": [dict(card) for card in cards]}
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/partner/cards")
async def create_partner_card(
    card_data: PartnerCard,
    user: User = Depends(require_roles("partner", "admin", "superadmin"))
):
    """Создать новую карточку партнера"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        try:
            # Получаем partner_id
            partner_id = await conn.fetchval(
                "SELECT id FROM partners WHERE telegram_id = $1",
                user.tg_id
            )
            
            if not partner_id:
                raise HTTPException(status_code=400, detail="Partner not found")
            
            # Создаем карточку
            card_id = await conn.fetchval("""
                INSERT INTO partner_places 
                (partner_id, title, description, category, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                RETURNING id
            """, partner_id, card_data.title, card_data.description, 
                card_data.category, "pending")
            
            return {"card_id": card_id, "status": "created"}
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/admin/moderation")
async def get_moderation_queue(
    user: User = Depends(require_roles("admin", "superadmin"))
):
    """Получить очередь модерации для админов"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        try:
            # Партнеры на модерации
            partners = await conn.fetch("""
                SELECT id, title, contact_name, contact_phone, status, created_at
                FROM partners 
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 10
            """)
            
            # Заведения на модерации
            places = await conn.fetch("""
                SELECT pp.id, pp.title, pp.address, pp.status, p.title as partner_name, pp.created_at
                FROM partner_places pp
                JOIN partners p ON pp.partner_id = p.id
                WHERE pp.status = 'pending'
                ORDER BY pp.created_at ASC
                LIMIT 10
            """)
            
            return {
                "partners": [dict(p) for p in partners],
                "places": [dict(p) for p in places]
            }
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/stats/overview")
async def get_stats_overview(
    user: User = Depends(get_current_user)
):
    """Получить общую статистику"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        try:
            # Базовая статистика
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            total_partners = await conn.fetchval("SELECT COUNT(*) FROM partners WHERE status = 'approved'")
            total_places = await conn.fetchval("SELECT COUNT(*) FROM partner_places WHERE status = 'approved'")
            
            stats = {
                "total_users": total_users,
                "total_partners": total_partners,
                "total_places": total_places
            }
            
            # Дополнительная статистика для партнеров
            if user.role in ("partner", "admin", "superadmin"):
                partner_id = await conn.fetchval(
                    "SELECT id FROM partners WHERE telegram_id = $1",
                    user.tg_id
                )
                if partner_id:
                    my_places = await conn.fetchval(
                        "SELECT COUNT(*) FROM partner_places WHERE partner_id = $1",
                        partner_id
                    )
                    stats["my_places"] = my_places
            
            return stats
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "ok", "service": "karma-webapp-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
