"""
Маршруты для работы с Telegram-интеграцией.
Включает эндпоинты для привязки аккаунта Telegram и аутентификации через Telegram.
"""
from datetime import timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.schemas.auth import Token, UserInDB, UserBase
from core.services.telegram_service import TelegramService
from core.security import get_current_user
from core.config import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.post("/auth-token", response_model=Dict[str, str])
async def generate_telegram_auth_token(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Генерирует токен для привязки аккаунта Telegram.
    
    Этот токен должен быть использован в Telegram-боте для подтверждения владения аккаунтом.
    """
    telegram_service = TelegramService(db)
    token = await telegram_service.generate_auth_token(current_user.id)
    
    return {
        "message": "Токен для привязки Telegram аккаунта сгенерирован",
        "token": token,
        "expires_in": 900  # 15 минут в секундах
    }

@router.post("/link-account", response_model=Dict[str, str])
async def link_telegram_account(
    telegram_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Привязывает аккаунт Telegram к текущему пользователю.
    
    Требует данных из Telegram WebApp.
    """
    telegram_service = TelegramService(db)
    success, message = await telegram_service.link_telegram_account(
        current_user.id, 
        telegram_data
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}

@router.post("/login", response_model=Token)
async def login_via_telegram(
    telegram_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Аутентификация через Telegram.
    
    Принимает данные из Telegram WebApp и возвращает токены доступа.
    """
    telegram_service = TelegramService(db)
    result = await telegram_service.authenticate_telegram(telegram_data.get("id"))
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось аутентифицироваться через Telegram. Убедитесь, что аккаунт привязан.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user, access_token, refresh_token = result
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserBase.from_orm(user)
    }

@router.get("/me", response_model=Dict[str, Any])
async def get_telegram_info(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает информацию о привязанном аккаунте Telegram.
    """
    if not current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram аккаунт не привязан"
        )
    
    result = await db.execute(
        """
        SELECT username, first_name, last_name, is_active, created_at
        FROM telegram_users
        WHERE user_id = :user_id
        """,
        {"user_id": current_user.id}
    )
    
    telegram_data = result.mappings().first()
    if not telegram_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация о Telegram аккаунте не найдена"
        )
    
    return {
        "telegram_id": current_user.telegram_id,
        **dict(telegram_data)
    }

@router.delete("/unlink", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_telegram_account(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Отвязывает аккаунт Telegram от текущего пользователя.
    """
    if not current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram аккаунт не привязан"
        )
    
    await db.execute(
        "DELETE FROM telegram_users WHERE user_id = :user_id",
        {"user_id": current_user.id}
    )
    await db.commit()
    
    return None
