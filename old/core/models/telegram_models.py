from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from core.database import Base

class TelegramUser(Base):
    """Модель для хранения привязки Telegram аккаунта к пользователю"""
    __tablename__ = "telegram_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users_auth.id', ondelete='CASCADE'), nullable=False)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), nullable=True)
    is_bot = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="telegram_account")
    
    def __repr__(self):
        return f"<TelegramUser {self.telegram_id} ({self.username or 'no username'})>"

class TelegramAuthToken(Base):
    """Модель для хранения токенов авторизации через Telegram"""
    __tablename__ = "telegram_auth_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users_auth.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="telegram_auth_tokens")
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<TelegramAuthToken {self.token[:8]}...>"
