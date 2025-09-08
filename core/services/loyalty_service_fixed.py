"""
ИСПРАВЛЕННЫЙ Loyalty Service - система баллов лояльности
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ЛИБО ТРАТИШЬ, ЛИБО НАКАПЛИВАЕШЬ
"""
import math
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LoyaltyService:
    """ИСПРАВЛЕННЫЙ сервис для работы с системой баллов лояльности"""
    
    def __init__(self):
        self.redeem_rate = 5000.0  # 1 балл = 5000 VND
        self.max_accrual_percent = 20.00  # Максимальный % начисления
        self.rounding_rule = 'bankers'  # Банковское округление
        self.min_purchase_for_points = 10000  # Минимальная покупка для начисления
        self.max_discount_percent = 40.0  # Максимальная скидка за баллы
    
    async def get_user_points_balance(self, user_id: int) -> int:
        """Получить баланс баллов пользователя"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute(
                    "SELECT points_balance FROM users WHERE telegram_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting user points balance: {e}")
            return 0
    
    async def update_user_points_balance(self, user_id: int, change_amount: int) -> bool:
        """Обновить баланс баллов пользователя"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Обновляем баланс
                conn.execute(
                    "UPDATE users SET points_balance = points_balance + ?, updated_at = ? WHERE telegram_id = ?",
                    (change_amount, datetime.now().isoformat(), user_id)
                )
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating user points balance: {e}")
            return False
    
    async def add_points_history(self, user_id: int, change_amount: int, reason: str, 
                                transaction_type: str, sale_id: Optional[int] = None, 
                                admin_id: Optional[int] = None) -> bool:
        """Добавить запись в историю баллов"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO points_history 
                    (user_id, change_amount, reason, transaction_type, sale_id, admin_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, change_amount, reason, transaction_type, sale_id, admin_id, datetime.now().isoformat()))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding points history: {e}")
            return False

    def calculate_points_transaction(self, amount_gross: float, accrual_pct: float, 
                                   redeem_rate: float, points_to_spend: int = 0) -> Dict[str, Any]:
        """
        ИСПРАВЛЕННЫЙ метод для правильного расчета баллов
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ЛИБО ТРАТИШЬ, ЛИБО НАКАПЛИВАЕШЬ
        """
        
        if points_to_spend > 0:
            # Тратим баллы = НЕТ начисления
            return {
                'points_spent': points_to_spend,
                'points_earned': 0,
                'net_change': -points_to_spend,
                'operation_type': 'spending_only'
            }
        else:
            # Не тратим баллы = ЕСТЬ начисление
            if amount_gross >= self.min_purchase_for_points:
                points_value = amount_gross * (accrual_pct / 100)
                points_earned = math.floor(points_value / redeem_rate)
            else:
                points_earned = 0
            
            return {
                'points_spent': 0,
                'points_earned': points_earned,
                'net_change': points_earned,
                'operation_type': 'earning_only'
            }

    async def calculate_purchase_benefits(self, user_id: int, place_id: int, 
                                        amount_gross: float, points_to_spend: int = 0) -> Dict[str, Any]:
        """
        ИСПРАВЛЕННЫЙ расчет льгот по формуле B + E:
        B = базовая скидка партнера
        E = дополнительная скидка за баллы
        
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ЛИБО ТРАТИШЬ, ЛИБО НАКАПЛИВАЕШЬ
        """
        try:
            # Получаем данные пользователя
            user_points = await self.get_user_points_balance(user_id)
            
            # Получаем данные заведения
            place_data = await self._get_place_data(place_id)
            if not place_data:
                raise ValueError("Заведение не найдено")
            
            # Получаем конфигурацию системы
            config = await self._get_loyalty_config()
            
            # B: базовая скидка партнера
            base_discount_pct = place_data.get('base_discount_pct', 0.0)
            base_discount_amount = amount_gross * base_discount_pct / 100
            
            # E: дополнительная скидка за баллы
            max_extra_value = amount_gross * place_data.get('max_percent_per_bill', 50.0) / 100
            available_extra_value = min(user_points * config['redeem_rate'], max_extra_value)
            
            if points_to_spend > 0:
                # Пользователь указал конкретную сумму баллов
                extra_value = min(points_to_spend * config['redeem_rate'], max_extra_value)
                points_spent = points_to_spend
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: При трате баллов начисления НЕТ
                points_earned = 0
                operation_type = "spending_only"
            else:
                # Автоматический расчет максимальной скидки
                extra_value = available_extra_value
                points_spent = math.ceil(extra_value / config['redeem_rate'])
                # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Начисление только если НЕ тратим баллы
                min_purchase_for_points = place_data.get('min_redeem', 0)
                if amount_gross >= min_purchase_for_points:
                    accrual_pct = place_data.get('loyalty_accrual_pct', 5.0)
                    points_earned = math.floor((amount_gross * accrual_pct / 100) / config['redeem_rate'])
                else:
                    points_earned = 0
                operation_type = "earning_only"
            
            # Финальные расчеты
            extra_discount_pct = (extra_value / amount_gross) * 100 if amount_gross > 0 else 0
            amount_partner_due = amount_gross - base_discount_amount
            amount_user_subsidy = extra_value
            final_user_price = amount_gross - base_discount_amount - extra_value
            
            return {
                'base_discount_pct': base_discount_pct,
                'extra_discount_pct': extra_discount_pct,
                'total_discount_pct': base_discount_pct + extra_discount_pct,
                'amount_partner_due': amount_partner_due,
                'amount_user_subsidy': amount_user_subsidy,
                'final_user_price': final_user_price,
                'points_spent': points_spent,
                'points_earned': points_earned,
                'user_points_balance': user_points,
                'available_points_value': available_extra_value,
                'operation_type': operation_type,
                'net_points_change': points_earned - points_spent
            }
            
        except Exception as e:
            logger.error(f"Error calculating purchase benefits: {e}")
            raise
    
    async def _get_place_data(self, place_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные заведения"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT base_discount_pct, loyalty_accrual_pct, min_redeem, max_percent_per_bill, title
                    FROM partner_places 
                    WHERE id = ? AND status = 'published'
                """, (place_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'base_discount_pct': result[0] or 0.0,
                        'loyalty_accrual_pct': result[1] or 5.0,
                        'min_redeem': result[2] or 0,
                        'max_percent_per_bill': result[3] or 50.0,
                        'title': result[4]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting place data: {e}")
            return None
    
    async def _get_loyalty_config(self) -> Dict[str, Any]:
        """Получить конфигурацию системы лояльности"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT redeem_rate, rounding_rule, max_accrual_percent
                    FROM platform_loyalty_config 
                    ORDER BY id DESC LIMIT 1
                """)
                result = cursor.fetchone()
                
                if result:
                    return {
                        'redeem_rate': result[0] or 5000.0,
                        'rounding_rule': result[1] or 'bankers',
                        'max_accrual_percent': result[2] or 20.0
                    }
                else:
                    # Возвращаем значения по умолчанию
                    return {
                        'redeem_rate': 5000.0,
                        'rounding_rule': 'bankers',
                        'max_accrual_percent': 20.0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting loyalty config: {e}")
            return {
                'redeem_rate': 5000.0,
                'rounding_rule': 'bankers',
                'max_accrual_percent': 20.0
            }
    
    async def get_points_history(self, user_id: int, limit: int = 20) -> list:
        """Получить историю баллов пользователя"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT change_amount, reason, transaction_type, created_at
                    FROM points_history 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                return [
                    {
                        'change_amount': row[0],
                        'reason': row[1],
                        'transaction_type': row[2],
                        'created_at': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting points history: {e}")
            return []
    
    async def process_points_transaction(self, user_id: int, change_amount: int, 
                                       reason: str, transaction_type: str,
                                       sale_id: Optional[int] = None,
                                       admin_id: Optional[int] = None) -> bool:
        """Обработать транзакцию баллов (списание или начисление)"""
        try:
            # Обновляем баланс
            success = await self.update_user_points_balance(user_id, change_amount)
            if not success:
                return False
            
            # Добавляем в историю
            success = await self.add_points_history(
                user_id, change_amount, reason, transaction_type, sale_id, admin_id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing points transaction: {e}")
            return False

    async def update_loyalty_config(self, redeem_rate: Optional[float] = None,
                                  min_purchase_for_points: Optional[int] = None,
                                  max_discount_percent: Optional[float] = None,
                                  admin_id: int = None) -> bool:
        """Обновить конфигурацию системы лояльности"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Обновляем конфигурацию
                updates = []
                params = []
                
                if redeem_rate is not None:
                    updates.append("redeem_rate = ?")
                    params.append(redeem_rate)
                
                if min_purchase_for_points is not None:
                    updates.append("min_purchase_for_points = ?")
                    params.append(min_purchase_for_points)
                
                if max_discount_percent is not None:
                    updates.append("max_discount_percent = ?")
                    params.append(max_discount_percent)
                
                if updates:
                    params.extend([admin_id, datetime.now().isoformat()])
                    conn.execute(f"""
                        UPDATE platform_loyalty_config 
                        SET {', '.join(updates)}, updated_by = ?, updated_at = ?
                        WHERE id = (SELECT id FROM platform_loyalty_config ORDER BY id DESC LIMIT 1)
                    """, params)
                    conn.commit()
                    
                    # Обновляем локальные значения
                    if redeem_rate is not None:
                        self.redeem_rate = redeem_rate
                    if min_purchase_for_points is not None:
                        self.min_purchase_for_points = min_purchase_for_points
                    if max_discount_percent is not None:
                        self.max_discount_percent = max_discount_percent
                    
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating loyalty config: {e}")
            return False

# Глобальный экземпляр сервиса
loyalty_service = LoyaltyService()
