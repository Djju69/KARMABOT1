"""
Referral service: manage user referrals and rewards
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, List, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text, literal_column
from sqlalchemy.exc import SQLAlchemyError

from core.models.loyalty_models import (
    Referral,
    ReferralLink,
    LoyaltyTransaction,
    LoyaltyBalance,
    LoyaltyTransactionType
)
from core.database import get_db, execute_in_transaction
from core.services.loyalty_service import LoyaltyService # Changed import
from core.logger import get_logger
from sqlalchemy.orm import aliased
from core.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

class ReferralService:
    """Service for managing user referrals and rewards"""

    def __init__(self):
        self.referrer_bonus = 100  # Бонус приглашающему
        self.referee_bonus = 50    # Бонус приглашенному
        self.levels = {
            1: 0.10,  # 10% от покупок реферала 1-го уровня
            2: 0.05,  # 5% от покупок реферала 2-го уровня
            3: 0.02   # 2% от покупок реферала 3-го уровня
        }

    async def create_referral_code(self, user_id: UUID) -> str:
        """Создать реферальный код для пользователя"""
        try:
            async with get_db() as db:
                # Проверяем, есть ли уже код
                existing_link = await db.execute(
                    select(ReferralLink).where(ReferralLink.user_id == user_id)
                )
                if existing_link.scalar_one_or_none():
                    return existing_link.scalar_one().referral_code

                # Генерируем уникальный код
                referral_code = f"REF{user_id.hex[:8].upper()}"

                # Создаем запись
                referral_link = ReferralLink(
                    user_id=user_id,
                    referral_code=referral_code,
                    is_active=True
                )

                db.add(referral_link)
                await db.commit()

                logger.info(f"Created referral code {referral_code} for user {user_id}")
                return referral_code

        except SQLAlchemyError as e:
            logger.error(f"Error creating referral code for user {user_id}: {e}")
            raise
    
    async def get_referral_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's referral statistics"""
        try:
            async with get_db() as db:
                # Get direct referrals count
                direct_refs_query = await db.execute(
                    select(func.count(Referral.id))
                    .where(and_(
                        Referral.referrer_id == user_id,
                        Referral.referrer_bonus_awarded == True
                    ))
                )
                direct_refs = direct_refs_query.scalar() or 0

                # Get total earnings from referrals
                earnings_query = await db.execute(
                    select(func.coalesce(func.sum(LoyaltyTransaction.points), 0))
                    .where(and_(
                        LoyaltyTransaction.user_id == user_id,
                        LoyaltyTransaction.transaction_type == LoyaltyTransactionType.REFERRAL_BONUS
                    ))
                )
                total_earned = earnings_query.scalar() or 0

                # Get referral link
                link_query = await db.execute(
                    select(ReferralLink.referral_code)
                    .where(ReferralLink.user_id == user_id)
                )
                referral_code = link_query.scalar_one_or_none()

                if not referral_code:
                    referral_code = await self.create_referral_code(user_id)

                referral_link = f"https://t.me/your_bot?start=ref{referral_code}"

                # Get monthly stats
                month_ago = datetime.utcnow() - timedelta(days=30)
                monthly_refs_query = await db.execute(
                    select(func.count(Referral.id))
                    .where(and_(
                        Referral.referrer_id == user_id,
                        Referral.created_at >= month_ago
                    ))
                )
                monthly_refs = monthly_refs_query.scalar() or 0

                stats = {
                    'total_referrals': direct_refs,
                    'monthly_referrals': monthly_refs,
                    'total_earned': total_earned,
                    'referral_link': referral_link,
                    'referral_code': referral_code,
                    'referrer_bonus': self.referrer_bonus,
                    'referee_bonus': self.referee_bonus
                }

                return stats

        except SQLAlchemyError as e:
            logger.error(f"Error getting referral stats for user {user_id}: {e}")
            raise

    async def process_referral_signup(
        self,
        referrer_id: UUID,
        referee_id: UUID,
        referral_code: str
    ) -> Dict[str, Any]:
        """Process new user signup with referral"""
        try:
            async with get_db() as db:
                # Инициализируем сервис лояльности внутри транзакции
                loyalty_service = LoyaltyService(db)
                await loyalty_service.initialize() # Важно для загрузки правил

                # Проверяем, что пользователь не приглашал сам себя
                if referrer_id == referee_id:
                    raise ValidationError("Нельзя пригласить самого себя")
                
                # Проверяем, что реферальный код существует и активен
                link_query = await db.execute(
                    select(ReferralLink)
                    .where(and_(
                        ReferralLink.referral_code == referral_code,
                        ReferralLink.is_active == True
                    ))
                )
                referral_link = link_query.scalar_one_or_none()

                if not referral_link:
                    raise ValidationError("Недействительный реферальный код")

                if referral_link.user_id != referrer_id:
                    raise ValidationError("Реферальный код принадлежит другому пользователю")

                # Проверяем, что реферал еще не зарегистрирован
                existing_query = await db.execute(
                    select(Referral.id)
                    .where(Referral.referee_id == referee_id)
                )
                if existing_query.scalar_one_or_none():
                    raise ValidationError("Пользователь уже зарегистрирован по реферальной ссылке")

                # Создаем запись о реферале
                referral = Referral(
                    referrer_id=referrer_id,
                    referee_id=referee_id,
                    referral_code=referral_code,
                    referrer_bonus_awarded=False,
                    referee_bonus_awarded=False
                )

                db.add(referral)
                await db.flush()  # Получаем ID

                # Бонус приглашающему
                referrer_transaction = await loyalty_service.add_points( # Исправлен вызов на add_points
                    user_id=referrer_id,
                    points=self.referrer_bonus,
                    transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
                    description=f"Бонус за приглашение пользователя {referee_id}",
                    reference_id=referral.id
                )

                # Бонус приглашенному
                referee_transaction = await loyalty_service.add_points( # Исправлен вызов на add_points
                    user_id=referee_id,
                    points=self.referee_bonus,
                    transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
                    description=f"Бонус за регистрацию по реферальной ссылке",
                    reference_id=referral.id
                )

                # Обновляем статус начисления бонусов
                referral.referrer_bonus_awarded = True
                referral.referee_bonus_awarded = True
                referral.bonus_awarded_at = datetime.utcnow()

                await db.commit()

                logger.info(f"Processed referral: {referrer_id} -> {referee_id} (code: {referral_code})")

                return {
                    'success': True,
                    'referral_id': referral.id,
                    'referrer_bonus': self.referrer_bonus,
                    'referee_bonus': self.referee_bonus,
                    'referrer_transaction_id': referrer_transaction.id,
                    'referee_transaction_id': referee_transaction.id
                }

        except SQLAlchemyError as e:
            logger.error(f"Error processing referral: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing referral: {e}")
            raise

    async def get_referral_tree(self, user_id: UUID, max_depth: int = 3) -> Dict[str, Any]:
        """Получить дерево рефералов пользователя"""
        try:
            async with get_db() as db:
                # SQLAlchemy-native recursive CTE
                referral_alias = aliased(Referral)

                # Base case: direct referrals
                base_query = (
                    select(
                        referral_alias.referrer_id,
                        referral_alias.referee_id,
                        referral_alias.created_at,
                        literal_column("1").label("level"),
                    )
                    .where(referral_alias.referrer_id == user_id)
                    .cte("referral_tree", recursive=True)
                )

                # Recursive part
                recursive_alias = aliased(base_query)
                referral_recursive_alias = aliased(Referral)
                recursive_query = base_query.union_all(
                    select(
                        referral_recursive_alias.referrer_id,
                        referral_recursive_alias.referee_id,
                        referral_recursive_alias.created_at,
                        (recursive_alias.c.level + 1).label("level"),
                    )
                    .join(recursive_alias, referral_recursive_alias.referrer_id == recursive_alias.c.referee_id)
                    .where(recursive_alias.c.level < max_depth)
                )

                final_query = select(recursive_query).order_by(recursive_query.c.level, recursive_query.c.created_at)
                result = await db.execute(final_query)

                tree_data = result.fetchall()

                # Формируем структуру дерева
                tree = {
                    'user_id': str(user_id),
                    'levels': {},
                    'total_referrals': 0
                }

                for row in tree_data:
                    level = row.level
                    if level not in tree['levels']:
                        tree['levels'][level] = []

                    tree['levels'][level].append({
                        'referee_id': str(row.referee_id),
                        'created_at': row.created_at.isoformat()
                    })
                    tree['total_referrals'] += 1

                return tree

        except SQLAlchemyError as e:
            logger.error(f"Error getting referral tree for user {user_id}: {e}")
            raise
    
    async def get_referral_earnings(self, user_id: UUID, days: int = 30) -> List[Dict[str, Any]]:
        """Получить доходы от рефералов за период"""
        try:
            async with get_db() as db:
                since_date = datetime.utcnow() - timedelta(days=days)

                query = await db.execute(
                    select(
                        Referral.id,
                        Referral.referee_id,
                        Referral.created_at,
                        LoyaltyTransaction.points,
                        LoyaltyTransaction.created_at.label('bonus_date')
                    )
                    .join(LoyaltyTransaction, LoyaltyTransaction.reference_id == Referral.id)
                    .where(and_(
                        Referral.referrer_id == user_id,
                        Referral.referrer_bonus_awarded == True,
                        LoyaltyTransaction.created_at >= since_date
                    ))
                    .order_by(LoyaltyTransaction.created_at.desc())
                )

                earnings = []
                for row in query.fetchall():
                    earnings.append({
                        'referral_id': str(row.id),
                        'referee_id': str(row.referee_id),
                        'referral_date': row.created_at.isoformat(),
                        'bonus_amount': row.points,
                        'bonus_date': row.bonus_date.isoformat()
                    })

                return earnings

        except SQLAlchemyError as e:
            logger.error(f"Error getting referral earnings for user {user_id}: {e}")
            raise

# Singleton instance
# referral_service = ReferralService() # This should be instantiated with dependencies where needed