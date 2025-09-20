"""
Referral Service - реферальная система
"""

from typing import List, Dict, Optional, Tuple
from core.database import db_v2
from core.services.points_service import points_service
import logging
import secrets
import string

logger = logging.getLogger(__name__)

class ReferralService:
    """Сервис для работы с реферальной системой"""
    
    # Настройки реферальной системы
    REFERRAL_REWARD = 100  # Баллы за приглашение
    REFERRED_REWARD = 50   # Баллы для приглашенного
    
    @staticmethod
    def generate_referral_link(user_id: int, bot_username: str) -> str:
        """Генерировать реферальную ссылку"""
        # Создаем уникальный код для пользователя
        referral_code = f"ref_{user_id}_{secrets.token_hex(4)}"
        return f"https://t.me/{bot_username}?start={referral_code}"
    
    @staticmethod
    async def process_referral(invited_user_id: int, referral_code: str) -> bool:
        """Обработать реферальное приглашение"""
        try:
            # Парсим код приглашения
            if not referral_code.startswith("ref_"):
                return False
            
            parts = referral_code.split("_")
            if len(parts) < 2:
                return False
            
            inviter_id = int(parts[1])
            
            # Проверяем, что пользователь не приглашает сам себя
            if inviter_id == invited_user_id:
                return False
            
            # Проверяем, что приглашающий существует
            inviter = db_v2.get_user_by_id(inviter_id)
            if not inviter:
                return False
            
            # Проверяем, что приглашенный еще не был в системе
            invited = db_v2.get_user_by_id(invited_user_id)
            if not invited:
                return False
            
            # Проверяем, что приглашенный еще не использовал реферальную систему
            existing_referral = db_v2.execute_query(
                "SELECT id FROM referrals WHERE invited_id = ?",
                (invited_user_id,)
            )
            if existing_referral and len(existing_referral) > 0:
                return False

                # Создаем запись о реферале
            db_v2.execute_query(
                """INSERT INTO referrals (inviter_id, invited_id, status, reward_points) 
                   VALUES (?, ?, 'completed', ?)""",
                (inviter_id, invited_user_id, ReferralService.REFERRAL_REWARD)
            )
            
            # Начисляем баллы приглашающему
            await points_service.add_points(
                inviter_id, 
                ReferralService.REFERRAL_REWARD,
                "referral_invite",
                f"Приглашение пользователя {invited_user_id}"
            )
            
            # Начисляем баллы приглашенному
            await points_service.add_points(
                invited_user_id,
                ReferralService.REFERRED_REWARD,
                "referral_bonus",
                f"Бонус за регистрацию по приглашению"
            )
            
            logger.info(f"Referral processed: {inviter_id} -> {invited_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            return False
    
    @staticmethod
    async def get_user_referrals(user_id: int) -> List[Dict]:
        """Получить список приглашенных пользователей"""
        try:
            query = """
                SELECT r.*, u.username, u.first_name, u.last_name, r.created_at
                FROM referrals r
                LEFT JOIN users u ON r.invited_id = u.id
                WHERE r.inviter_id = ?
                ORDER BY r.created_at DESC
            """
            
            referrals = db_v2.execute_query(query, (user_id,))
            return referrals
            
        except Exception as e:
            logger.error(f"Error getting user referrals: {e}")
            return []
    
    @staticmethod
    async def get_referral_stats(user_id: int) -> Dict:
        """Получить статистику рефералов"""
        try:
            # Общее количество приглашенных
            total_count_result = db_v2.execute_query(
                "SELECT COUNT(*) as count FROM referrals WHERE inviter_id = ?",
                (user_id,)
            )
            total_count = total_count_result[0]['count'] if total_count_result and len(total_count_result) > 0 else 0
            
            # Количество активных (за последние 30 дней)
            active_count_result = db_v2.execute_query(
                """SELECT COUNT(*) as count FROM referrals 
                   WHERE inviter_id = ? AND created_at > datetime('now', '-30 days')""",
                (user_id,)
            )
            active_count = active_count_result[0]['count'] if active_count_result and len(active_count_result) > 0 else 0
            
            # Общие доходы от рефералов
            total_earnings_result = db_v2.execute_query(
                """SELECT SUM(reward_points) as total FROM referrals 
                   WHERE inviter_id = ?""",
                (user_id,)
            )
            total_earnings = total_earnings_result[0]['total'] if total_earnings_result and len(total_earnings_result) > 0 and total_earnings_result[0]['total'] else 0
            
            return {
                'total_referrals': total_count,
                'active_referrals': active_count,
                'total_earnings': total_earnings
            }
            
        except Exception as e:
            logger.error(f"Error getting referral stats: {e}")
            return {
                'total_referrals': 0,
                'active_referrals': 0,
                'total_earnings': 0
            }
    
    @staticmethod
    async def get_referral_leaderboard(limit: int = 10) -> List[Dict]:
        """Получить таблицу лидеров по рефералам"""
        try:
            query = """
                SELECT inviter_id, COUNT(*) as referrals_count, SUM(reward_points) as total_earnings
                FROM referrals
                GROUP BY inviter_id
                ORDER BY referrals_count DESC, total_earnings DESC
                LIMIT ?
            """
            
            leaderboard = db_v2.execute_query(query, (limit,))
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting referral leaderboard: {e}")
            return []

# Создаем экземпляр сервиса
referral_service = ReferralService()