"""
Referral service: manage user referrals and rewards
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

from ..database.db_v2 import db_v2
from .cache import cache_service

logger = logging.getLogger(__name__)

class ReferralService:
    """Service for managing user referrals and rewards"""
    
    def __init__(self):
        self.referral_bonus = 100  # Бонус за приглашение
        self.levels = {
            1: 0.10,  # 10% от покупок реферала 1-го уровня
            2: 0.05,  # 5% от покупок реферала 2-го уровня
            3: 0.02   # 2% от покупок реферала 3-го уровня
        }
    
    async def get_referral_stats(self, user_id: int) -> Dict:
        """Get user's referral statistics"""
        cache_key = f"referral:stats:{user_id}"
        cached_stats = await cache_service.get(cache_key)
        
        if cached_stats and isinstance(cached_stats, dict):
            return cached_stats
            
        with db_v2.get_connection() as conn:
            # Get direct referrals count
            direct_refs = conn.execute(
                """
                SELECT COUNT(*) FROM referrals 
                WHERE referrer_id = ? AND status = 'active'
                """,
                (user_id,)
            ).fetchone()[0]
            
            # Get total earnings
            total_earned = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) FROM referral_earnings 
                WHERE referrer_id = ?
                """,
                (user_id,)
            ).fetchone()[0]
            
            # Get referral link
            referral_link = f"https://t.me/your_bot?start=ref{user_id}"
            
            stats = {
                'total_referrals': direct_refs,
                'total_earned': total_earned,
                'referral_link': referral_link,
                'referral_bonus': self.referral_bonus
            }
            
            # Cache for 1 hour
            await cache_service.set(cache_key, stats, expire=3600)
            
            return stats
    
    async def process_referral_signup(self, referrer_id: int, referred_id: int) -> bool:
        """Process new user signup with referral"""
        try:
            with db_v2.get_connection() as conn:
                # Check if referral already exists
                existing = conn.execute(
                    "SELECT id FROM referrals WHERE referred_id = ?",
                    (referred_id,)
                ).fetchone()
                
                if existing:
                    return False
                
                # Create new referral
                conn.execute(
                    """
                    INSERT INTO referrals 
                    (referrer_id, referred_id, status, created_at)
                    VALUES (?, ?, 'active', CURRENT_TIMESTAMP)
                    """,
                    (referrer_id, referred_id)
                )
                
                # Add bonus to referrer
                conn.execute(
                    """
                    UPDATE loyalty_wallets 
                    SET balance_pts = balance_pts + ?
                    WHERE user_id = ?
                    """,
                    (self.referral_bonus, referrer_id)
                )
                
                # Log the bonus
                conn.execute(
                    """
                    INSERT INTO loyalty_transactions 
                    (user_id, amount, transaction_type, description, created_at)
                    VALUES (?, ?, 'referral_bonus', 'Bonus for referring a friend', CURRENT_TIMESTAMP)
                    """,
                    (referrer_id, self.referral_bonus)
                )
                
                # Invalidate cache
                await cache_service.delete(f"referral:stats:{referrer_id}")
                await cache_service.delete(f"loyalty:balance:{referrer_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            return False

# Singleton instance
referral_service = ReferralService()
