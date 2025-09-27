"""
Расширенный сервис достижений с геймификацией
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncpg
import os
import json
from core.utils.logger import get_logger
from core.models.achievement_models import (
    Achievement, AchievementType, AchievementRarity, UserAchievement,
    DEFAULT_ACHIEVEMENTS, RARITY_COLORS, get_progress_bar, format_achievement_progress
)

logger = get_logger(__name__)

class GamificationService:
    """Расширенный сервис геймификации и достижений"""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
        self.achievements = DEFAULT_ACHIEVEMENTS
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def get_user_achievements(
        self, 
        user_id: int, 
        limit: int = 20, 
        offset: int = 0,
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить достижения пользователя с прогрессом
        
        Args:
            user_id: Telegram user ID
            limit: Количество достижений
            offset: Смещение для пагинации
            show_progress: Показывать ли прогресс
            
        Returns:
            list: Список достижений с прогрессом
        """
        try:
            conn = await self.get_connection()
            try:
                # Получаем достижения пользователя
                achievements = await conn.fetch("""
                    SELECT id, achievement_type, achievement_data, earned_at, is_notified
                    FROM user_achievements 
                    WHERE user_id = $1
                    ORDER BY earned_at DESC
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                result = []
                for achievement in achievements:
                    data = json.loads(achievement['achievement_data']) if achievement['achievement_data'] else {}
                    achievement_type = AchievementType(achievement['achievement_type'])
                    
                    # Получаем информацию о достижении
                    achievement_info = self.achievements.get(achievement_type)
                    
                    result.append({
                        'id': achievement['id'],
                        'achievement_type': achievement['achievement_type'],
                        'achievement_data': data,
                        'earned_at': achievement['earned_at'],
                        'is_notified': achievement['is_notified'],
                        'name': achievement_info.name if achievement_info else achievement_type.value,
                        'description': achievement_info.description if achievement_info else "",
                        'icon': achievement_info.icon if achievement_info else "🏆",
                        'rarity': achievement_info.rarity.value if achievement_info else AchievementRarity.COMMON.value,
                        'points_reward': achievement_info.points_reward if achievement_info else 0
                    })
                
                return result
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {str(e)}")
            return []
    
    async def get_achievement_progress(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получить прогресс по всем достижениям
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: Список достижений с прогрессом
        """
        try:
            conn = await self.get_connection()
            try:
                result = []
                
                for achievement_type, achievement in self.achievements.items():
                    # Получаем текущий прогресс
                    current, target = await self._calculate_progress(conn, user_id, achievement_type)
                    
                    # Проверяем, получено ли достижение
                    earned = await conn.fetchrow("""
                        SELECT earned_at FROM user_achievements 
                        WHERE user_id = $1 AND achievement_type = $2
                    """, user_id, achievement_type.value)
                    
                    progress_data = {
                        'achievement_type': achievement_type.value,
                        'name': achievement.name,
                        'description': achievement.description,
                        'icon': achievement.icon,
                        'rarity': achievement.rarity.value,
                        'rarity_color': RARITY_COLORS[achievement.rarity],
                        'points_reward': achievement.points_reward,
                        'current': current,
                        'target': target,
                        'progress_percentage': min(int((current / target) * 100), 100) if target > 0 else 100,
                        'progress_bar': get_progress_bar(current, target),
                        'is_earned': earned is not None,
                        'earned_at': earned['earned_at'] if earned else None
                    }
                    
                    result.append(progress_data)
                
                # Сортируем по редкости и прогрессу
                rarity_order = {
                    AchievementRarity.COMMON: 0,
                    AchievementRarity.RARE: 1,
                    AchievementRarity.EPIC: 2,
                    AchievementRarity.LEGENDARY: 3
                }
                
                result.sort(key=lambda x: (
                    rarity_order[AchievementRarity(x['rarity'])],
                    -x['progress_percentage']
                ))
                
                return result
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting achievement progress for user {user_id}: {str(e)}")
            return []
    
    async def _calculate_progress(self, conn: asyncpg.Connection, user_id: int, achievement_type: AchievementType) -> Tuple[int, int]:
        """Вычислить прогресс по достижению"""
        try:
            if achievement_type == AchievementType.LEVEL_UP:
                # Получаем уровень пользователя
                level_result = await conn.fetchrow("""
                    SELECT karma_points FROM users WHERE telegram_id = $1
                """, user_id)
                current_level = self._calculate_level(level_result['karma_points'] if level_result else 0)
                return current_level, 10  # Максимум 10 уровней
            
            elif achievement_type == AchievementType.KARMA_MILESTONE:
                # Получаем карму пользователя
                karma_result = await conn.fetchrow("""
                    SELECT karma_points FROM users WHERE telegram_id = $1
                """, user_id)
                current_karma = karma_result['karma_points'] if karma_result else 0
                return current_karma, 25000  # Максимум 25000 кармы
            
            elif achievement_type == AchievementType.DAILY_STREAK:
                # Получаем текущую серию ежедневных входов
                streak_result = await conn.fetchrow("""
                    SELECT COUNT(*) as streak FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND created_at >= CURRENT_DATE - INTERVAL '7 days'
                """, user_id)
                current_streak = streak_result['streak'] if streak_result else 0
                return current_streak, 7
            
            elif achievement_type == AchievementType.REFERRAL_MASTER:
                # Получаем количество рефералов
                referrals_result = await conn.fetchrow("""
                    SELECT COUNT(*) as count FROM referrals WHERE inviter_id = $1
                """, user_id)
                current_referrals = referrals_result['count'] if referrals_result else 0
                return current_referrals, 10
            
            elif achievement_type == AchievementType.CARD_COLLECTOR:
                # Получаем количество карт
                cards_result = await conn.fetchrow("""
                    SELECT COUNT(*) as count FROM user_cards WHERE user_id = $1
                """, user_id)
                current_cards = cards_result['count'] if cards_result else 0
                return current_cards, 5
            
            elif achievement_type == AchievementType.EXPLORER:
                # Получаем количество уникальных мест
                places_result = await conn.fetchrow("""
                    SELECT COUNT(DISTINCT place_id) as count FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'geo_checkin'
                """, user_id)
                current_places = places_result['count'] if places_result else 0
                return current_places, 10
            
            elif achievement_type == AchievementType.LOYALTY_CHAMPION:
                # Получаем баллы лояльности
                loyalty_result = await conn.fetchrow("""
                    SELECT points_balance FROM users WHERE telegram_id = $1
                """, user_id)
                current_loyalty = loyalty_result['points_balance'] if loyalty_result else 0
                return current_loyalty, 5000
            
            elif achievement_type == AchievementType.EARLY_BIRD:
                # Получаем количество ранних входов
                early_result = await conn.fetchrow("""
                    SELECT COUNT(*) as count FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND EXTRACT(HOUR FROM created_at) BETWEEN 6 AND 9
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """, user_id)
                current_early = early_result['count'] if early_result else 0
                return current_early, 5
            
            elif achievement_type == AchievementType.NIGHT_OWL:
                # Получаем количество поздних входов
                night_result = await conn.fetchrow("""
                    SELECT COUNT(*) as count FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND (EXTRACT(HOUR FROM created_at) BETWEEN 22 AND 23 
                         OR EXTRACT(HOUR FROM created_at) BETWEEN 0 AND 2)
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """, user_id)
                current_night = night_result['count'] if night_result else 0
                return current_night, 5
            
            elif achievement_type == AchievementType.WEEKEND_WARRIOR:
                # Получаем количество выходных дней
                weekend_result = await conn.fetchrow("""
                    SELECT COUNT(DISTINCT DATE(created_at)) as count FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND EXTRACT(DOW FROM created_at) IN (0, 6)  -- Воскресенье и суббота
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """, user_id)
                current_weekend = weekend_result['count'] if weekend_result else 0
                return current_weekend, 4
            
            elif achievement_type == AchievementType.MONTHLY_CHALLENGER:
                # Получаем количество дней в текущем месяце
                monthly_result = await conn.fetchrow("""
                    SELECT COUNT(DISTINCT DATE(created_at)) as count FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """, user_id)
                current_monthly = monthly_result['count'] if monthly_result else 0
                return current_monthly, 25
            
            elif achievement_type == AchievementType.YEARLY_LEGEND:
                # Получаем количество дней в текущем году
                yearly_result = await conn.fetchrow("""
                    SELECT COUNT(DISTINCT DATE(created_at)) as count FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND created_at >= DATE_TRUNC('year', CURRENT_DATE)
                """, user_id)
                current_yearly = yearly_result['count'] if yearly_result else 0
                return current_yearly, 300
            
            else:
                return 0, 1
                
        except Exception as e:
            logger.error(f"Error calculating progress for {achievement_type}: {str(e)}")
            return 0, 1
    
    def _calculate_level(self, karma_points: int) -> int:
        """Вычислить уровень на основе кармы"""
        if karma_points < 100:
            return 1
        elif karma_points < 300:
            return 2
        elif karma_points < 600:
            return 3
        elif karma_points < 1000:
            return 4
        elif karma_points < 1500:
            return 5
        elif karma_points < 2200:
            return 6
        elif karma_points < 3000:
            return 7
        elif karma_points < 4000:
            return 8
        elif karma_points < 5000:
            return 9
        else:
            return 10
    
    async def check_and_award_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Проверить и наградить достижения
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: Список новых достижений
        """
        try:
            conn = await self.get_connection()
            try:
                new_achievements = []
                
                for achievement_type, achievement in self.achievements.items():
                    # Проверяем, получено ли уже достижение
                    existing = await conn.fetchrow("""
                        SELECT id FROM user_achievements 
                        WHERE user_id = $1 AND achievement_type = $2
                    """, user_id, achievement_type.value)
                    
                    if existing:
                        continue
                    
                    # Вычисляем прогресс
                    current, target = await self._calculate_progress(conn, user_id, achievement_type)
                    
                    # Проверяем, достигнута ли цель
                    if current >= target:
                        # Награждаем достижением
                        await conn.execute("""
                            INSERT INTO user_achievements (user_id, achievement_type, achievement_data, earned_at)
                            VALUES ($1, $2, $3, NOW())
                        """, user_id, achievement_type.value, json.dumps({"target": target, "achieved": current}))
                        
                        # Добавляем уведомление
                        await conn.execute("""
                            INSERT INTO user_notifications (user_id, message, notification_type, created_at)
                            VALUES ($1, $2, 'achievement', NOW())
                        """, user_id, f"🎉 {achievement.icon} {achievement.name}!")
                        
                        new_achievements.append({
                            'achievement_type': achievement_type.value,
                            'name': achievement.name,
                            'description': achievement.description,
                            'icon': achievement.icon,
                            'rarity': achievement.rarity.value,
                            'points_reward': achievement.points_reward
                        })
                        
                        logger.info(f"New achievement awarded: {achievement.name} to user {user_id}")
                
                return new_achievements
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error checking achievements for user {user_id}: {str(e)}")
            return []
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получить статистику пользователя для геймификации
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Статистика пользователя
        """
        try:
            conn = await self.get_connection()
            try:
                # Получаем базовую статистику
                user_result = await conn.fetchrow("""
                    SELECT karma_points, points_balance, created_at FROM users WHERE telegram_id = $1
                """, user_id)
                
                if not user_result:
                    return {}
                
                # Вычисляем уровень
                level = self._calculate_level(user_result['karma_points'])
                
                # Получаем количество достижений
                achievements_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_achievements WHERE user_id = $1
                """, user_id)
                
                # Получаем количество рефералов
                referrals_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM referrals WHERE inviter_id = $1
                """, user_id)
                
                # Получаем количество карт
                cards_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_cards WHERE user_id = $1
                """, user_id)
                
                # Получаем текущую серию ежедневных входов
                streak_result = await conn.fetchrow("""
                    SELECT COUNT(*) as streak FROM user_activities 
                    WHERE user_id = $1 AND activity_type = 'daily_checkin' 
                    AND created_at >= CURRENT_DATE - INTERVAL '7 days'
                """, user_id)
                current_streak = streak_result['streak'] if streak_result else 0
                
                return {
                    'level': level,
                    'karma_points': user_result['karma_points'],
                    'loyalty_points': user_result['points_balance'],
                    'achievements_count': achievements_count,
                    'referrals_count': referrals_count,
                    'cards_count': cards_count,
                    'current_streak': current_streak,
                    'member_since': user_result['created_at']
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting user stats for user {user_id}: {str(e)}")
            return {}

# Создаем экземпляр сервиса
gamification_service = GamificationService()
