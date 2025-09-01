from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Text, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum

Base = declarative_base()

class UserRole(str, PyEnum):
    USER = "user"
    PARTNER = "partner"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "superadmin"

class UserStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class User(Base):
    __tablename__ = 'users_auth'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)  
    full_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Authentication fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # For password reset and email verification
    verification_token = Column(String(100), nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(100), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Additional fields
    avatar_url = Column(String(255), nullable=True)
    preferences = Column(JSON, default=dict, nullable=True)
    
    # Relationships
    owned_places = relationship("Place", back_populates="owner")
    reviews = relationship("Review", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    telegram_account = relationship(
        "TelegramUser", 
        uselist=False,  
        back_populates="user",
        cascade="all, delete-orphan"
    )
    telegram_auth_tokens = relationship(
        "TelegramAuthToken", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def has_telegram(self) -> bool:
        """Проверяет, привязан ли Telegram аккаунт"""
        return self.telegram_account is not None
    
    @property
    def telegram_id(self) -> Optional[int]:
        """Возвращает ID Telegram аккаунта, если он привязан"""
        return self.telegram_account.telegram_id if self.telegram_account else None
    
    @property
    def telegram_username(self) -> Optional[str]:
        """Возвращает username Telegram аккаунта, если он привязан"""
        return self.telegram_account.username if self.telegram_account else None
    
    @property
    def is_superuser(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_admin(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    @property
    def is_partner(self) -> bool:
        return self.role == UserRole.PARTNER
    
    @property
    def is_moderator(self) -> bool:
        return self.role == UserRole.MODERATOR
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        # In a real app, this would check against a permissions table
        if self.is_superuser:
            return True
        
        # Example permission check - extend as needed
        permissions = {
            UserRole.ADMIN: ["users:read", "users:write", "places:moderate"],
            UserRole.MODERATOR: ["places:moderate", "reviews:moderate"],
            UserRole.PARTNER: ["places:manage_own", "reviews:respond"],
            UserRole.USER: ["profile:read", "profile:update"]
        }
        
        return permission in permissions.get(self.role, [])

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users_auth.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    is_revoked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        return not (self.is_revoked or self.is_expired)

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users_auth.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired
