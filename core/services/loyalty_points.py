"""Loyalty points service for managing user points and transactions."""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from core.database.db_v2 import db_v2 as db
from core.services.cache import cache_service

logger = logging.getLogger(__name__)

# Ключ для кэширования баланса пользователя (TTL 1 час)
BALANCE_CACHE_TTL = 3600
BALANCE_CACHE_KEY = "loyalty:balance:{user_id}"


class LoyaltyService:
    """Service for managing loyalty points and transactions."""

    @staticmethod
    def add_transaction(
        user_id: int, rule_code: str, points: int, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a loyalty points transaction and return the new balance.
        
        Args:
            user_id: Telegram user ID
            rule_code: Activity rule code (e.g., 'checkin', 'geocheckin')
            points: Points to add (can be negative)
            metadata: Optional metadata for the transaction
            
        Returns:
            Dict with new balance and transaction ID
            {
                "balance": int,
                "transaction_id": int,
                "points_awarded": int
            }
        """
        if points == 0:
            raise ValueError("Points cannot be zero")

        # 1. Записываем транзакцию в БД
        query = """
        INSERT INTO loyalty_points_tx (user_id, rule_code, points, metadata, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        RETURNING id, created_at
        """
        try:
            # Use execute for SQLite
            cursor = db.get_connection().cursor()
            cursor.execute(query, (user_id, rule_code, points, str(metadata) if metadata else None))
            row = cursor.fetchone()
            transaction_id = row[0] if row else None
            
            if not transaction_id:
                raise ValueError("Failed to get transaction ID after insert")
                
            # Commit the transaction
            db.get_connection().commit()
            
            # 2. Инвалидируем кэш баланса (синхронно)
            cache_key = BALANCE_CACHE_KEY.format(user_id=user_id)
            try:
                cache_service.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to delete cache key {cache_key}: {str(e)}")
            
            # 3. Возвращаем новый баланс
            balance = LoyaltyService.get_balance(user_id, use_cache=False)
            
            logger.info(
                "Loyalty points transaction created",
                extra={
                    "user_id": user_id,
                    "rule_code": rule_code,
                    "points": points,
                    "new_balance": balance,
                    "transaction_id": transaction_id
                }
            )
            
            return {
                "balance": balance,
                "transaction_id": transaction_id,
                "points_awarded": points
            }
            
        except Exception as e:
            db.get_connection().rollback()
            logger.error(
                "Failed to create loyalty transaction",
                extra={"user_id": user_id, "rule_code": rule_code, "error": str(e)}
            )
            raise

    @staticmethod
    def get_balance(user_id: int, use_cache: bool = True) -> int:
        """
        Get current user's loyalty points balance.
        
        Args:
            user_id: Telegram user ID
            use_cache: Whether to use cached balance if available
            
        Returns:
            Current balance (sum of all transactions)
        """
        cache_key = BALANCE_CACHE_KEY.format(user_id=user_id)
        
        # Пытаемся получить из кэша (синхронно)
        if use_cache:
            try:
                cached = cache_service.get(cache_key)
                if cached is not None and cached != 'None':  # Проверяем на строку 'None'
                    return int(cached)
            except Exception as e:
                logger.warning("Failed to get balance from cache", extra={"user_id": user_id, "error": str(e)})
        
        # Если не в кэше или ошибка, считаем из БД
        query = """
        SELECT COALESCE(SUM(points), 0) as balance
        FROM loyalty_points_tx
        WHERE user_id = ?
        """
        try:
            cursor = db.get_connection().cursor()
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            balance = int(row[0]) if row and row[0] is not None else 0
            
            # Кэшируем результат (синхронно)
            try:
                cache_service.set(cache_key, str(balance), ex=BALANCE_CACHE_TTL)
            except Exception as e:
                logger.warning("Failed to cache balance", extra={"user_id": user_id, "error": str(e)})
                
            return balance
            
        except Exception as e:
            logger.error("Failed to get balance from DB", extra={"user_id": user_id, "error": str(e)})
            raise

    @staticmethod
    def get_recent_transactions(
        user_id: int, limit: int = 10, days: Optional[int] = None
    ) -> list[dict]:
        """
        Get recent transactions for a user.
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of transactions to return
            days: Optional filter for last N days
            
        Returns:
            List of transaction dicts with keys: id, rule_code, points, created_at, metadata
        """
        query = """
        SELECT id, rule_code, points, created_at, metadata
        FROM loyalty_points_tx
        WHERE user_id = ?
        """
        params = [user_id]
        
        if days is not None:
            query += " AND created_at >= datetime('now', ?)"
            params.append(f"-{days} days")
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        try:
            cursor = db.get_connection().cursor()
            cursor.execute(query, params)
            
            # Convert rows to list of dicts
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(
                "Failed to fetch recent transactions",
                extra={"user_id": user_id, "error": str(e)}
            )
            return []


# Синглтон для удобного импорта
loyalty_service = LoyaltyService()
