"""
Сервис для работы с профилями пользователей и системой уровней
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from core.models.user_profile import UserProfile, UserLevel, UserActivityLog, UserAchievement
from core.models.user_settings import UserSettings
from core.models.loyalty_models import LoyaltyBalance, LoyaltyTransaction
from core.database import get_db, execute_in_transaction
from core.logger import get_logger
from core.common.exceptions import NotFoundError, ValidationError, BusinessLogicError

logger = get_logger(__name__)

class UserProfileService:
    """
    Сервис для управления профилями пользователей
    """
    
    def __init__(self):
        # Пороги для уровней
        self.level_thresholds = {
            UserLevel.BRONZE: 0,
            UserLevel.SILVER: 1000,
            UserLevel.GOLD: 5000,
            UserLevel.PLATINUM: 15000
        }
        
        # Бонусы за уровни
        self.level_bonuses = {
            UserLevel.BRONZE: {"discount": 0.05, "points_multiplier": 1.0},
            UserLevel.SILVER: {"discount": 0.10, "points_multiplier": 1.2},
            UserLevel.GOLD: {"discount": 0.15, "points_multiplier": 1.5},
            UserLevel.PLATINUM: {"discount": 0.20, "points_multiplier": 2.0}
        }

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Получение полного профиля пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Полный профиль пользователя
        """
        try:
            async with get_db() as db:
                # Получаем основной профиль
                result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = result.scalar_one_or_none()
                
                if not profile:
                    # Создаем новый профиль
                    profile = await self.create_user_profile(user_id, db)
                
                # Получаем баланс лояльности
                balance_result = await db.execute(
                    select(LoyaltyBalance).where(LoyaltyBalance.user_id == user_id)
                )
                balance = balance_result.scalar_one_or_none()
                
                # Получаем настройки
                settings_result = await db.execute(
                    select(UserSettings).where(UserSettings.user_id == user_id)
                )
                settings = settings_result.scalar_one_or_none()
                
                # Получаем последние достижения
                achievements_result = await db.execute(
                    select(UserAchievement)
                    .where(UserAchievement.user_id == user_id)
                    .order_by(desc(UserAchievement.unlocked_at))
                    .limit(5)
                )
                achievements = achievements_result.scalars().all()
                
                return {
                    "user_id": profile.user_id,
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "display_name": profile.display_name,
                    "phone": profile.phone,
                    "email": profile.email,
                    
                    # Система уровней
                    "level": profile.level.value,
                    "level_points": profile.level_points,
                    "level_progress": float(profile.level_progress),
                    "next_level": self._get_next_level(profile.level),
                    "level_benefits": self.level_bonuses[profile.level],
                    
                    # Статистика
                    "total_visits": profile.total_visits,
                    "total_reviews": profile.total_reviews,
                    "total_qr_scans": profile.total_qr_scans,
                    "total_purchases": profile.total_purchases,
                    "total_spent": float(profile.total_spent),
                    "total_referrals": profile.total_referrals,
                    "referral_earnings": float(profile.referral_earnings),
                    
                    # Баланс и настройки
                    "loyalty_balance": float(balance.balance) if balance else 0.0,
                    "loyalty_points": balance.total_points if balance else 0,
                    
                    # Настройки
                    "notifications_enabled": profile.notifications_enabled,
                    "email_notifications": profile.email_notifications,
                    "push_notifications": profile.push_notifications,
                    "privacy_level": profile.privacy_level,
                    "language": profile.language,
                    "timezone": profile.timezone,
                    
                    # Дополнительная информация
                    "bio": profile.bio,
                    "avatar_url": profile.avatar_url,
                    "created_at": profile.created_at.isoformat(),
                    "last_activity": profile.last_activity.isoformat(),
                    
                    # Достижения
                    "recent_achievements": [
                        {
                            "type": ach.achievement_type,
                            "name": ach.achievement_name,
                            "description": ach.achievement_description,
                            "points": ach.points_reward,
                            "unlocked_at": ach.unlocked_at.isoformat()
                        }
                        for ach in achievements
                    ]
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения профиля пользователя {user_id}: {e}")
            raise

    async def create_user_profile(self, user_id: int, db: AsyncSession = None) -> UserProfile:
        """
        Создание нового профиля пользователя
        
        Args:
            user_id: ID пользователя
            db: Сессия базы данных (опционально)
            
        Returns:
            Созданный профиль
        """
        try:
            if db is None:
                async with get_db() as db:
                    return await self.create_user_profile(user_id, db)
            
            profile = UserProfile(
                user_id=user_id,
                level=UserLevel.BRONZE,
                level_points=0,
                level_progress=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            
            logger.info(f"Создан новый профиль для пользователя {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Ошибка создания профиля для пользователя {user_id}: {e}")
            raise

    async def update_user_profile(
        self, 
        user_id: int, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обновление профиля пользователя
        
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
            
        Returns:
            Обновленный профиль
        """
        try:
            async with get_db() as db:
                # Получаем текущий профиль
                result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = result.scalar_one_or_none()
                
                if not profile:
                    profile = await self.create_user_profile(user_id, db)
                
                # Обновляем поля
                allowed_fields = [
                    'username', 'first_name', 'last_name', 'phone', 'email',
                    'bio', 'avatar_url', 'timezone', 'language',
                    'notifications_enabled', 'email_notifications', 'push_notifications',
                    'privacy_level'
                ]
                
                for field, value in update_data.items():
                    if field in allowed_fields and hasattr(profile, field):
                        setattr(profile, field, value)
                
                profile.updated_at = datetime.utcnow()
                
                await db.commit()
                await db.refresh(profile)
                
                logger.info(f"Обновлен профиль пользователя {user_id}")
                
                return await self.get_user_profile(user_id)
                
        except Exception as e:
            logger.error(f"Ошибка обновления профиля пользователя {user_id}: {e}")
            raise

    async def log_user_activity(
        self, 
        user_id: int, 
        activity_type: str, 
        points_earned: int = 0,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Логирование активности пользователя
        
        Args:
            user_id: ID пользователя
            activity_type: Тип активности
            points_earned: Заработанные очки
            activity_data: Дополнительные данные
        """
        try:
            async with get_db() as db:
                # Создаем запись активности
                activity_log = UserActivityLog(
                    user_id=user_id,
                    activity_type=activity_type,
                    points_earned=points_earned,
                    activity_data=str(activity_data) if activity_data else None,
                    created_at=datetime.utcnow()
                )
                
                db.add(activity_log)
                await db.commit()
                
                logger.info(f"Записана активность пользователя {user_id}: {activity_type}")
                
        except Exception as e:
            logger.error(f"Ошибка записи активности пользователя {user_id}: {e}")

    async def get_user_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Получение статистики пользователя за период
        
        Args:
            user_id: ID пользователя
            days: Количество дней для статистики
            
        Returns:
            Статистика пользователя
        """
        try:
            async with get_db() as db:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                # Статистика активности
                activity_result = await db.execute(
                    select(
                        UserActivityLog.activity_type,
                        func.count(UserActivityLog.id).label('count'),
                        func.sum(UserActivityLog.points_earned).label('total_points')
                    )
                    .where(
                        and_(
                            UserActivityLog.user_id == user_id,
                            UserActivityLog.created_at >= since_date
                        )
                    )
                    .group_by(UserActivityLog.activity_type)
                )
                activity_stats = activity_result.fetchall()
                
                # Статистика транзакций
                transactions_result = await db.execute(
                    select(
                        LoyaltyTransaction.transaction_type,
                        func.count(LoyaltyTransaction.id).label('count'),
                        func.sum(LoyaltyTransaction.points).label('total_points')
                    )
                    .where(
                        and_(
                            LoyaltyTransaction.user_id == user_id,
                            LoyaltyTransaction.created_at >= since_date
                        )
                    )
                    .group_by(LoyaltyTransaction.transaction_type)
                )
                transaction_stats = transactions_result.fetchall()
                
                return {
                    "period_days": days,
                    "activity_stats": [
                        {
                            "type": stat.activity_type,
                            "count": stat.count,
                            "points": stat.total_points or 0
                        }
                        for stat in activity_stats
                    ],
                    "transaction_stats": [
                        {
                            "type": stat.transaction_type,
                            "count": stat.count,
                            "points": stat.total_points or 0
                        }
                        for stat in transaction_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
            raise

    async def unlock_achievement(
        self, 
        user_id: int, 
        achievement_type: str, 
        achievement_name: str,
        achievement_description: str = None,
        points_reward: int = 0
    ) -> bool:
        """
        Разблокировка достижения для пользователя
        
        Args:
            user_id: ID пользователя
            achievement_type: Тип достижения
            achievement_name: Название достижения
            achievement_description: Описание достижения
            points_reward: Награда в очках
            
        Returns:
            True если достижение разблокировано
        """
        try:
            async with get_db() as db:
                # Проверяем, есть ли уже такое достижение
                existing_result = await db.execute(
                    select(UserAchievement).where(
                        and_(
                            UserAchievement.user_id == user_id,
                            UserAchievement.achievement_type == achievement_type,
                            UserAchievement.achievement_name == achievement_name
                        )
                    )
                )
                
                if existing_result.scalar_one_or_none():
                    return False  # Достижение уже есть
                
                # Создаем новое достижение
                achievement = UserAchievement(
                    user_id=user_id,
                    achievement_type=achievement_type,
                    achievement_name=achievement_name,
                    achievement_description=achievement_description,
                    points_reward=points_reward,
                    unlocked_at=datetime.utcnow()
                )
                
                db.add(achievement)
                
                # Добавляем очки к профилю
                if points_reward > 0:
                    await self.log_user_activity(
                        user_id=user_id,
                        activity_type="achievement",
                        points_earned=points_reward,
                        activity_data={"achievement": achievement_name}
                    )
                
                await db.commit()
                
                logger.info(f"Разблокировано достижение для пользователя {user_id}: {achievement_name}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка разблокировки достижения для пользователя {user_id}: {e}")
            raise

    def _get_next_level(self, current_level: UserLevel) -> Optional[str]:
        """Получение следующего уровня"""
        level_order = [UserLevel.BRONZE, UserLevel.SILVER, UserLevel.GOLD, UserLevel.PLATINUM]
        try:
            current_index = level_order.index(current_level)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1].value
        except ValueError:
            pass
        return None

# Создаем экземпляр сервиса
user_profile_service = UserProfileService()
