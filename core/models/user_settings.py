"""
Модель настроек пользователя
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserSettings(Base):
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)  # Telegram user ID
    language = Column(String(10), default='ru')
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    privacy_level = Column(String(20), default='standard')  # standard, private, public
    theme = Column(String(20), default='light')  # light, dark, auto
    timezone = Column(String(50), default='UTC')
    currency = Column(String(3), default='RUB')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Дополнительные настройки в JSON
    additional_settings = Column(JSON, default=dict)
