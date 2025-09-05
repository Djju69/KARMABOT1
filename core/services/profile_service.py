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
from core.common.exceptions import NotFoundError, ValidationError

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
                # Получаем базовую информацию о пользователе из таблицы users
                from core.models.user import User
                from sqlalchemy import select
                
                result = await db.execute(
                    select(User).where(User.tg_user_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    profile = {
                        "user_id": user_id,
                        "username": user.username or f"user_{user_id}",
                        "first_name": user.first_name or "Пользователь",
                        "last_name": user.last_name or "",
                        "email": None,  # Пока нет поля email в модели
                        "phone": None,  # Пока нет поля phone в модели
                        "avatar_url": None,  # Пока нет поля avatar в модели
                        "created_at": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
                        "last_activity": user.updated_at.isoformat() if user.updated_at else datetime.utcnow().isoformat(),
                        "is_active": not user.is_banned,
                        "is_verified": False  # Пока нет поля verified в модели
                    }
                else:
                    # Если пользователь не найден, создаем базовый профиль
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
            async with get_db() as db:
                from core.models.user_settings import UserSettings
                from sqlalchemy import select
                
                result = await db.execute(
                    select(UserSettings).where(UserSettings.user_id == user_id)
                )
                settings = result.scalar_one_or_none()
                
                if settings:
                    return {
                        "language": settings.language,
                        "notifications": {
                            "email": settings.email_notifications,
                            "push": settings.push_notifications,
                            "sms": False  # Пока не реализовано
                        },
                        "privacy": {
                            "show_profile": settings.privacy_level != "private",
                            "show_activities": settings.privacy_level == "public",
                            "allow_messages": True
                        },
                        "preferences": {
                            "theme": settings.theme,
                            "timezone": settings.timezone,
                            "currency": settings.currency
                        }
                    }
                else:
                    # Возвращаем дефолтные настройки если пользователь не найден
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
            async with get_db() as db:
                from core.models.user_settings import UserSettings
                from sqlalchemy import select
                
                result = await db.execute(
                    select(UserSettings).where(UserSettings.user_id == user_id)
                )
                user_settings = result.scalar_one_or_none()
                
                if user_settings:
                    # Обновляем существующие настройки
                    if "language" in settings:
                        user_settings.language = settings["language"]
                    if "notifications" in settings:
                        notifications = settings["notifications"]
                        user_settings.email_notifications = notifications.get("email", user_settings.email_notifications)
                        user_settings.push_notifications = notifications.get("push", user_settings.push_notifications)
                    if "privacy" in settings:
                        privacy = settings["privacy"]
                        if privacy.get("show_profile") and not privacy.get("show_activities"):
                            user_settings.privacy_level = "standard"
                        elif privacy.get("show_activities"):
                            user_settings.privacy_level = "public"
                        else:
                            user_settings.privacy_level = "private"
                    if "preferences" in settings:
                        preferences = settings["preferences"]
                        user_settings.theme = preferences.get("theme", user_settings.theme)
                        user_settings.timezone = preferences.get("timezone", user_settings.timezone)
                        user_settings.currency = preferences.get("currency", user_settings.currency)
                    
                    user_settings.updated_at = datetime.utcnow()
                    await db.commit()
                else:
                    # Создаем новые настройки
                    new_settings = UserSettings(
                        user_id=user_id,
                        language=settings.get("language", "ru"),
                        email_notifications=settings.get("notifications", {}).get("email", True),
                        push_notifications=settings.get("notifications", {}).get("push", True),
                        privacy_level="standard",
                        theme=settings.get("preferences", {}).get("theme", "light"),
                        timezone=settings.get("preferences", {}).get("timezone", "UTC+7"),
                        currency=settings.get("preferences", {}).get("currency", "VND")
                    )
                    db.add(new_settings)
                    await db.commit()
                
                # Возвращаем обновленные настройки
                return await self.get_user_settings(user_id)
            
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
        """Получение уведомлений пользователя из БД."""
        try:
            from core.services.notification_service import notification_service
            items = notification_service.list_notifications(int(user_id), limit=limit, offset=offset, unread_only=unread_only)
            for n in items:
                if hasattr(n.get("created_at"), 'isoformat'):
                    n["created_at"] = n["created_at"].isoformat()
                if n.get("read_at") and hasattr(n.get("read_at"), 'isoformat'):
                    n["read_at"] = n["read_at"].isoformat()
            return items
        except Exception as e:
            logger.error(f"Error getting user notifications for {user_id}: {e}")
            raise
    
    async def get_user_notifications_count(
        self,
        user_id: str,
        unread_only: bool = False
    ) -> int:
        """Количество уведомлений пользователя из БД."""
        try:
            from core.services.notification_service import notification_service
            return notification_service.count_notifications(int(user_id), unread_only=unread_only)
        except Exception as e:
            logger.error(f"Error getting user notifications count for {user_id}: {e}")
            return 0

    async def mark_notification_read(
        self,
        user_id: str,
        notification_id: int
    ) -> bool:
        """Отметить уведомление как прочитанное."""
        try:
            from core.services.notification_service import notification_service
            return notification_service.mark_read(int(user_id), notification_id)
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read for {user_id}: {e}")
            return False
    
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
            async with get_db() as db:
                from core.models.notification import Notification
                from sqlalchemy import select, update
                
                # Обновляем статус уведомления на "прочитано"
                await db.execute(
                    update(Notification)
                    .where(Notification.user_id == user_id)
                    .where(Notification.id == notification_id)
                    .values(is_read=True, read_at=datetime.utcnow())
                )
                await db.commit()
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
            async with get_db() as db:
                from core.models.user import User
                
                # Создаем нового пользователя в БД
                new_user = User(
                    tg_user_id=user_id,
                    username=profile_data.get("username"),
                    first_name=profile_data.get("first_name", ""),
                    last_name=profile_data.get("last_name", ""),
                    language_code=profile_data.get("language", "ru"),
                    is_admin=False,
                    is_banned=False
                )
                
                db.add(new_user)
                await db.commit()
                
                # Возвращаем созданный профиль
                return await self.get_user_profile(user_id)
            
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
            async with get_db() as db:
                from core.models.user import User
                from sqlalchemy import select, update
                
                # Обновляем данные пользователя в БД
                update_data = {}
                if "username" in profile_data:
                    update_data["username"] = profile_data["username"]
                if "first_name" in profile_data:
                    update_data["first_name"] = profile_data["first_name"]
                if "last_name" in profile_data:
                    update_data["last_name"] = profile_data["last_name"]
                if "language" in profile_data:
                    update_data["language_code"] = profile_data["language"]
                
                if update_data:
                    update_data["updated_at"] = datetime.utcnow()
                    await db.execute(
                        update(User)
                        .where(User.tg_user_id == user_id)
                        .values(**update_data)
                    )
                    await db.commit()
                
                # Возвращаем обновленный профиль
                return await self.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user profile for {user_id}: {e}")
            raise

# Singleton instance
profile_service = ProfileService()
