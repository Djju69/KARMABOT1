"""
Profile service for user profile management
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, List, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.exc import SQLAlchemyError

from core.models.loyalty_models import (
    LoyaltyTransaction,
    LoyaltyBalance,
    ActivityType,
    UserActivityLog
)
from core.database import get_db
from core.logger import get_logger
from core.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

class ProfileService:
    """Service for managing user profiles and settings"""
    
    def __init__(self):
        self.db = None
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Получение полного профиля пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с информацией о профиле
        """
        try:
            async with get_db() as db:
                # Получаем базовую информацию о пользователе
                # TODO: Добавить запрос к таблице users когда она будет готова
                profile = {
                    "user_id": user_id,
                    "username": f"user_{user_id}",
                    "first_name": "Пользователь",
                    "last_name": "",
                    "email": None,
                    "phone": None,
                    "avatar_url": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "is_active": True,
                    "is_verified": False
                }
                
                # Получаем статистику лояльности
                loyalty_stats = await self._get_loyalty_stats(user_id, db)
                profile.update(loyalty_stats)
                
                return profile
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting user profile for {user_id}: {e}")
            raise
    
    async def _get_loyalty_stats(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Получение статистики лояльности пользователя"""
        try:
            # Получаем баланс
            balance_query = await db.execute(
                select(LoyaltyBalance)
                .where(LoyaltyBalance.user_id == user_id)
            )
            balance = balance_query.scalar_one_or_none()
            
            # Получаем количество транзакций
            transactions_count_query = await db.execute(
                select(func.count(LoyaltyTransaction.id))
                .where(LoyaltyTransaction.user_id == user_id)
            )
            transactions_count = transactions_count_query.scalar() or 0
            
            # Получаем количество активностей
            activities_count_query = await db.execute(
                select(func.count(UserActivityLog.id))
                .where(UserActivityLog.user_id == user_id)
            )
            activities_count = activities_count_query.scalar() or 0
            
            return {
                "loyalty_balance": {
                    "total_points": balance.total_points if balance else 0,
                    "available_points": balance.available_points if balance else 0,
                    "last_updated": balance.last_updated.isoformat() if balance else None
                },
                "stats": {
                    "transactions_count": transactions_count,
                    "activities_count": activities_count,
                    "level": self._calculate_user_level(transactions_count)
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting loyalty stats for {user_id}: {e}")
            return {
                "loyalty_balance": {"total_points": 0, "available_points": 0, "last_updated": None},
                "stats": {"transactions_count": 0, "activities_count": 0, "level": 1}
            }
    
    def _calculate_user_level(self, transactions_count: int) -> int:
        """Вычисляет уровень пользователя на основе количества транзакций"""
        if transactions_count >= 100:
            return 5  # VIP
        elif transactions_count >= 50:
            return 4  # Gold
        elif transactions_count >= 20:
            return 3  # Silver
        elif transactions_count >= 5:
            return 2  # Bronze
        else:
            return 1  # Newbie
    
    async def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Получение настроек пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Настройки пользователя
        """
        try:
            # TODO: Добавить таблицу user_settings когда будет готова
            # Пока возвращаем дефолтные настройки
            return {
                "language": "ru",
                "notifications": {
                    "email": True,
                    "push": True,
                    "sms": False
                },
                "privacy": {
                    "show_profile": True,
                    "show_activities": False,
                    "allow_messages": True
                },
                "preferences": {
                    "theme": "light",
                    "timezone": "UTC+7",
                    "currency": "VND"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user settings for {user_id}: {e}")
            raise
    
    async def update_user_settings(
        self, 
        user_id: str, 
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обновление настроек пользователя.
        
        Args:
            user_id: ID пользователя
            settings: Новые настройки
            
        Returns:
            Обновленные настройки
        """
        try:
            # TODO: Добавить сохранение в БД когда таблица будет готова
            # Пока просто возвращаем обновленные настройки
            current_settings = await self.get_user_settings(user_id)
            
            # Обновляем настройки
            for key, value in settings.items():
                if key in current_settings:
                    if isinstance(current_settings[key], dict) and isinstance(value, dict):
                        current_settings[key].update(value)
                    else:
                        current_settings[key] = value
            
            return current_settings
            
        except Exception as e:
            logger.error(f"Error updating user settings for {user_id}: {e}")
            raise
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получение уведомлений пользователя.
        
        Args:
            user_id: ID пользователя
            limit: Количество записей
            offset: Смещение
            unread_only: Только непрочитанные
            
        Returns:
            Список уведомлений
        """
        try:
            # TODO: Добавить таблицу notifications когда будет готова
            # Пока возвращаем моковые данные
            notifications = [
                {
                    "id": 1,
                    "title": "Добро пожаловать!",
                    "message": "Спасибо за регистрацию в нашей системе лояльности",
                    "type": "welcome",
                    "is_read": False,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": 2,
                    "title": "Новые баллы",
                    "message": "Вы получили 50 баллов за регистрацию",
                    "type": "loyalty",
                    "is_read": True,
                    "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
                }
            ]
            
            if unread_only:
                notifications = [n for n in notifications if not n["is_read"]]
            
            return notifications[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error getting user notifications for {user_id}: {e}")
            raise
    
    async def get_user_notifications_count(
        self,
        user_id: str,
        unread_only: bool = False
    ) -> int:
        """
        Получение количества уведомлений пользователя.
        
        Args:
            user_id: ID пользователя
            unread_only: Только непрочитанные
            
        Returns:
            Количество уведомлений
        """
        try:
            notifications = await self.get_user_notifications(user_id, limit=1000)
            
            if unread_only:
                return len([n for n in notifications if not n["is_read"]])
            
            return len(notifications)
            
        except Exception as e:
            logger.error(f"Error getting user notifications count for {user_id}: {e}")
            return 0
    
    async def mark_notification_read(
        self,
        user_id: str,
        notification_id: int
    ) -> bool:
        """
        Отметка уведомления как прочитанного.
        
        Args:
            user_id: ID пользователя
            notification_id: ID уведомления
            
        Returns:
            True если успешно, False если не найдено
        """
        try:
            # TODO: Добавить обновление в БД когда таблица будет готова
            # Пока просто возвращаем True
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read for {user_id}: {e}")
            return False
    
    async def create_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Создание профиля пользователя.
        
        Args:
            user_id: ID пользователя
            profile_data: Данные профиля
            
        Returns:
            Созданный профиль
        """
        try:
            # TODO: Добавить создание в БД когда таблица будет готова
            profile = {
                "user_id": user_id,
                "username": profile_data.get("username", f"user_{user_id}"),
                "first_name": profile_data.get("first_name", ""),
                "last_name": profile_data.get("last_name", ""),
                "email": profile_data.get("email"),
                "phone": profile_data.get("phone"),
                "avatar_url": profile_data.get("avatar_url"),
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "is_verified": False
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile for {user_id}: {e}")
            raise
    
    async def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обновление профиля пользователя.
        
        Args:
            user_id: ID пользователя
            profile_data: Новые данные профиля
            
        Returns:
            Обновленный профиль
        """
        try:
            # TODO: Добавить обновление в БД когда таблица будет готова
            current_profile = await self.get_user_profile(user_id)
            
            # Обновляем поля
            for key, value in profile_data.items():
                if key in current_profile and value is not None:
                    current_profile[key] = value
            
            current_profile["updated_at"] = datetime.utcnow().isoformat()
            
            return current_profile
            
        except Exception as e:
            logger.error(f"Error updating user profile for {user_id}: {e}")
            raise

# Singleton instance
profile_service = ProfileService()
