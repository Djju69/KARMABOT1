from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"

class TokenData(BaseModel):
    """Данные, хранимые в JWT токене"""
    sub: str  # user_id
    type: TokenType
    exp: datetime
    jti: str
    scopes: list[str] = []

class Token(BaseModel):
    """Модель ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration

class UserBase(BaseModel):
    """Базовая модель пользователя"""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False

class UserCreate(UserBase):
    """Модель для создания пользователя"""
    password: str = Field(..., min_length=8, max_length=72)

class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=72)
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    """Модель пользователя из БД"""
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
        from_attributes = True

class UserResponse(UserBase):
    """Модель ответа с данными пользователя"""
    id: int
    created_at: datetime

class LoginRequest(BaseModel):
    """Модель запроса на вход"""
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordResetRequest(BaseModel):
    """Модель запроса на сброс пароля"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Модель подтверждения сброса пароля"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=72)

class EmailVerificationRequest(BaseModel):
    """Модель запроса верификации email"""
    token: str
