"""
Многоуровневый реферальный сервис (3 уровня)
Поддерживает автоматическое начисление бонусов по уровням
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text, literal_column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from core.models.referral_tree import ReferralTree, ReferralBonus, ReferralStats
from core.models.loyalty_models import LoyaltyTransaction, LoyaltyBalance
from core.database import get_db, execute_in_transaction
from core.logger import get_logger
from core.common.exceptions import NotFoundError, ValidationError, BusinessLogicError

logger = get_logger(__name__)

class MultilevelReferralService:
    """
    Сервис многоуровневой реферальной системы
    
    Алгоритм распределения бонусов:
    - 1-й уровень: 50% от бонуса
    - 2-й уровень: 30% от бонуса  
    - 3-й уровень: 20% от бонуса
    """
    
    def __init__(self):
        # Проценты бонусов по уровням
        self.level_percentages = {
            1: 0.50,  # 50% для 1-го уровня
            2: 0.30,  # 30% для 2-го уровня
            3: 0.20   # 20% для 3-го уровня
        }
        
        # Минимальные суммы для начисления бонусов
        self.min_bonus_amounts = {
            1: Decimal('10.00'),  # Минимум 10 рублей для 1-го уровня
            2: Decimal('5.00'),   # Минимум 5 рублей для 2-го уровня
            3: Decimal('2.00')    # Минимум 2 рубля для 3-го уровня
        }

    async def add_referral(
        self, 
        user_id: int, 
        referrer_id: int
    ) -> Dict[str, Any]:
        """
        Добавление нового реферала в многоуровневую систему
        
        Args:
            user_id: ID нового пользователя
            referrer_id: ID того, кто пригласил
            
        Returns:
            Информация о созданной записи
        """
        try:
            async with get_db() as db:
                # Проверяем, что пользователь еще не в системе
                existing = await db.execute(
                    select(ReferralTree).where(ReferralTree.user_id == user_id)
                )
                if existing.scalar_one_or_none():
                    raise BusinessLogicError(f"Пользователь {user_id} уже в реферальной системе")
                
                # Определяем уровень нового реферала
                referrer_level = await self._get_user_level(referrer_id, db)
                new_level = min(referrer_level + 1, 3)  # Максимум 3 уровня
                
                # Создаем запись в дереве рефералов
                referral_record = ReferralTree(
                    user_id=user_id,
                    referrer_id=referrer_id,
                    level=new_level,
                    created_at=datetime.utcnow()
                )
                
                db.add(referral_record)
                await db.commit()
                
                # Обновляем статистику
                await self._update_referral_stats(referrer_id, db)
                
                logger.info(f"Добавлен реферал: пользователь {user_id}, реферер {referrer_id}, уровень {new_level}")
                
                return {
                    "user_id": user_id,
                    "referrer_id": referrer_id,
                    "level": new_level,
                    "created_at": referral_record.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Ошибка добавления реферала {user_id} к {referrer_id}: {e}")
            raise

    async def process_referral_bonus(
        self, 
        transaction_id: int,
        user_id: int,
        amount: Decimal
    ) -> Dict[str, Any]:
        """
        Обработка бонусов для рефералов при транзакции
        
        Args:
            transaction_id: ID транзакции
            user_id: ID пользователя, совершившего транзакцию
            amount: Сумма транзакции
            
        Returns:
            Информация о начисленных бонусах
        """
        try:
            async with get_db() as db:
                # Получаем дерево рефералов для пользователя
                referral_chain = await self._get_referral_chain(user_id, db)
                
                if not referral_chain:
                    return {"bonuses_processed": 0, "total_amount": Decimal('0')}
                
                bonuses_processed = 0
                total_bonus_amount = Decimal('0')
                
                # Начисляем бонусы по уровням
                for level, referrer_id in referral_chain.items():
                    if level > 3:  # Максимум 3 уровня
                        break
                        
                    bonus_percentage = self.level_percentages[level]
                    bonus_amount = amount * Decimal(str(bonus_percentage))
                    
                    # Проверяем минимальную сумму
                    min_amount = self.min_bonus_amounts[level]
                    if bonus_amount < min_amount:
                        continue
                    
                    # Создаем запись о бонусе
                    bonus_record = ReferralBonus(
                        referrer_id=referrer_id,
                        referred_id=user_id,
                        level=level,
                        bonus_amount=bonus_amount,
                        source_transaction_id=transaction_id,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(bonus_record)
                    
                    # Начисляем бонус на баланс лояльности
                    await self._add_loyalty_bonus(referrer_id, bonus_amount, db)
                    
                    bonuses_processed += 1
                    total_bonus_amount += bonus_amount
                    
                    logger.info(f"Начислен бонус {level}-го уровня: {bonus_amount} руб. пользователю {referrer_id}")
                
                await db.commit()
                
                return {
                    "bonuses_processed": bonuses_processed,
                    "total_amount": total_bonus_amount,
                    "transaction_id": transaction_id
                }
                
        except Exception as e:
            logger.error(f"Ошибка обработки реферальных бонусов для транзакции {transaction_id}: {e}")
            raise

    async def get_referral_tree(
        self, 
        user_id: int, 
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Получение дерева рефералов пользователя
        
        Args:
            user_id: ID пользователя
            max_depth: Максимальная глубина дерева
            
        Returns:
            Структурированное дерево рефералов
        """
        try:
            async with get_db() as db:
                # Получаем всех рефералов пользователя
                result = await db.execute(
                    select(ReferralTree)
                    .where(ReferralTree.referrer_id == user_id)
                    .order_by(ReferralTree.level, ReferralTree.created_at)
                )
                referrals = result.scalars().all()
                
                # Группируем по уровням
                tree = {
                    "user_id": user_id,
                    "levels": {},
                    "total_referrals": len(referrals),
                    "total_earnings": Decimal('0')
                }
                
                for referral in referrals:
                    level = referral.level
                    if level not in tree["levels"]:
                        tree["levels"][level] = {
                            "count": 0,
                            "referrals": [],
                            "total_earnings": Decimal('0')
                        }
                    
                    tree["levels"][level]["count"] += 1
                    tree["levels"][level]["total_earnings"] += referral.total_earnings
                    tree["levels"][level]["referrals"].append({
                        "user_id": referral.user_id,
                        "created_at": referral.created_at.isoformat(),
                        "total_earnings": float(referral.total_earnings),
                        "total_referrals": referral.total_referrals
                    })
                    
                    tree["total_earnings"] += referral.total_earnings
                
                return tree
                
        except Exception as e:
            logger.error(f"Ошибка получения дерева рефералов для пользователя {user_id}: {e}")
            raise

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получение статистики рефералов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Статистика рефералов
        """
        try:
            async with get_db() as db:
                result = await db.execute(
                    select(ReferralStats).where(ReferralStats.user_id == user_id)
                )
                stats = result.scalar_one_or_none()
                
                if not stats:
                    # Создаем пустую статистику
                    return {
                        "user_id": user_id,
                        "level_1": {"count": 0, "earnings": 0},
                        "level_2": {"count": 0, "earnings": 0},
                        "level_3": {"count": 0, "earnings": 0},
                        "total_referrals": 0,
                        "total_earnings": 0,
                        "last_updated": None
                    }
                
                return {
                    "user_id": user_id,
                    "level_1": {
                        "count": stats.level_1_count,
                        "earnings": float(stats.level_1_earnings)
                    },
                    "level_2": {
                        "count": stats.level_2_count,
                        "earnings": float(stats.level_2_earnings)
                    },
                    "level_3": {
                        "count": stats.level_3_count,
                        "earnings": float(stats.level_3_earnings)
                    },
                    "total_referrals": stats.total_referrals,
                    "total_earnings": float(stats.total_earnings),
                    "last_updated": stats.last_updated.isoformat() if stats.last_updated else None
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики рефералов для пользователя {user_id}: {e}")
            raise

    async def _get_user_level(self, user_id: int, db: AsyncSession) -> int:
        """Получение уровня пользователя в реферальной системе"""
        result = await db.execute(
            select(ReferralTree.level).where(ReferralTree.user_id == user_id)
        )
        level = result.scalar_one_or_none()
        return level if level else 0

    async def _get_referral_chain(self, user_id: int, db: AsyncSession) -> Dict[int, int]:
        """Получение цепочки рефералов для пользователя"""
        chain = {}
        current_user = user_id
        level = 1
        
        while level <= 3:
            result = await db.execute(
                select(ReferralTree.referrer_id)
                .where(ReferralTree.user_id == current_user)
            )
            referrer_id = result.scalar_one_or_none()
            
            if not referrer_id:
                break
                
            chain[level] = referrer_id
            current_user = referrer_id
            level += 1
        
        return chain

    async def _update_referral_stats(self, user_id: int, db: AsyncSession):
        """Обновление статистики рефералов"""
        # Статистика обновляется автоматически через триггеры
        pass

    async def _add_loyalty_bonus(self, user_id: int, amount: Decimal, db: AsyncSession):
        """Добавление бонуса на баланс лояльности"""
        # Получаем текущий баланс
        result = await db.execute(
            select(LoyaltyBalance).where(LoyaltyBalance.user_id == user_id)
        )
        balance = result.scalar_one_or_none()
        
        if balance:
            balance.balance += amount
            balance.updated_at = datetime.utcnow()
        else:
            # Создаем новый баланс
            new_balance = LoyaltyBalance(
                user_id=user_id,
                balance=amount,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_balance)
        
        # Создаем транзакцию
        transaction = LoyaltyTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type="referral_bonus",
            description=f"Реферальный бонус",
            created_at=datetime.utcnow()
        )
        db.add(transaction)

# Создаем экземпляр сервиса
multilevel_referral_service = MultilevelReferralService()
