"""
Сервис системы лояльности для расчета скидок и управления баллами
Реализует формулы B + E согласно ТЗ
"""

import asyncpg
import os
import logging
import math
import decimal
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class LoyaltyPointsService:
    """Сервис системы лояльности"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Получение соединения с PostgreSQL"""
        return await asyncpg.connect(self.database_url)
    
    async def get_loyalty_config(self) -> Dict[str, Any]:
        """Получение конфигурации лояльности"""
        try:
            conn = await self.get_connection()
            try:
                config = await conn.fetchrow(
                    "SELECT * FROM platform_loyalty_config ORDER BY id DESC LIMIT 1"
                )
                if config:
                    return {
                        'redeem_rate': float(config['redeem_rate']),
                        'rounding_rule': config['rounding_rule'],
                        'max_accrual_percent': float(config['max_accrual_percent'])
                    }
                else:
                    return {
                        'redeem_rate': 5000.0,  # 1 балл = 5000 VND
                        'rounding_rule': 'bankers',
                        'max_accrual_percent': 20.0
                    }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting loyalty config: {str(e)}")
            return {
                'redeem_rate': 5000.0,
                'rounding_rule': 'bankers',
                'max_accrual_percent': 20.0
            }
    
    async def get_user_points_balance(self, user_id: int) -> int:
        """Получение баланса баллов пользователя"""
        try:
            conn = await self.get_connection()
            try:
                result = await conn.fetchrow(
                    "SELECT points_balance FROM users WHERE telegram_id = $1",
                    user_id
                )
                return result['points_balance'] if result else 0
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting points balance for user {user_id}: {str(e)}")
            return 0
    
    async def get_place_info(self, place_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о заведении"""
        try:
            conn = await self.get_connection()
            try:
                place = await conn.fetchrow(
                    "SELECT * FROM partner_places WHERE id = $1",
                    place_id
                )
                if place:
                    return dict(place)
                return None
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting place {place_id}: {str(e)}")
            return None
    
    async def get_partner_info(self, partner_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о партнере"""
        try:
            conn = await self.get_connection()
            try:
                partner = await conn.fetchrow(
                    "SELECT * FROM partners WHERE id = $1",
                    partner_id
                )
                if partner:
                    return dict(partner)
                return None
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting partner {partner_id}: {str(e)}")
            return None
    
    def calculate_loyalty_benefits(self, amount_gross: float, base_discount_pct: float, 
                                 user_points_balance: int, redeem_rate: float, 
                                 max_percent_per_bill: float, points_to_spend: Optional[int] = None) -> Dict[str, Any]:
        """
        Расчет льгот согласно бизнес-логике ТЗ:
        B = базовая скидка партнера
        E = дополнительная скидка за баллы пользователя
        """
        
        # Базовая скидка партнера (B)
        base_discount_amount = amount_gross * base_discount_pct / 100
        
        # Максимально возможная дополнительная скидка
        max_extra_value = amount_gross * max_percent_per_bill / 100
        available_extra_value = min(user_points_balance * redeem_rate, max_extra_value)
        
        # Фактическая дополнительная скидка
        if points_to_spend is not None:
            extra_value = min(points_to_spend * redeem_rate, max_extra_value)
            points_spent = points_to_spend
        else:
            extra_value = available_extra_value
            points_spent = math.ceil(extra_value / redeem_rate) if redeem_rate > 0 else 0
        
        # Процент дополнительной скидки (E)
        extra_discount_pct = (extra_value / amount_gross) * 100 if amount_gross > 0 else 0
        
        # Итоговые суммы
        amount_partner_due = amount_gross - base_discount_amount  # G - G*B/100
        amount_user_subsidy = extra_value                        # G*E/100
        final_user_price = amount_gross - base_discount_amount - extra_value
        
        return {
            'amount_gross': amount_gross,
            'base_discount_pct': base_discount_pct,
            'extra_discount_pct': extra_discount_pct,
            'total_discount_pct': base_discount_pct + extra_discount_pct,
            'amount_partner_due': amount_partner_due,
            'amount_user_subsidy': amount_user_subsidy,
            'final_user_price': final_user_price,
            'points_spent': points_spent,
            'extra_value': extra_value,
            'user_total_saving': base_discount_amount + extra_value
        }
    
    def calculate_points_earned(self, amount_gross: float, accrual_percent: float, 
                              redeem_rate: float, min_purchase: float = 10000) -> int:
        """Расчет начисляемых баллов"""
        if amount_gross < min_purchase:
            return 0
        
        points_value = amount_gross * accrual_percent / 100
        points_earned = math.floor(points_value / redeem_rate)
        
        return points_earned
    
    def apply_bankers_rounding(self, value: float) -> float:
        """Банковское округление (к ближайшему четному)"""
        try:
            decimal_value = decimal.Decimal(str(value))
            rounded = decimal_value.quantize(
                decimal.Decimal('1'), 
                rounding=decimal.ROUND_HALF_EVEN
            )
            return float(rounded)
        except:
            return round(value)
    
    async def calculate_purchase_benefits(self, user_id: int, place_id: int, 
                                        amount_gross: float, points_to_spend: int = 0) -> Dict[str, Any]:
        """
        Расчет льгот по покупке согласно новой бизнес-логике
        """
        # Получаем данные
        user_points = await self.get_user_points_balance(user_id)
        place = await self.get_place_info(place_id)
        config = await self.get_loyalty_config()
        
        if not place:
            raise ValueError("Заведение не найдено")
        
        # Получаем информацию о партнере
        partner = await self.get_partner_info(place['partner_id']) if place['partner_id'] else None
        
        # Базовая скидка партнера (B)
        base_discount_pct = place.get('base_discount_pct') or (partner.get('base_discount_pct') if partner else 0) or 0
        
        # Параметры заведения
        loyalty_accrual_pct = place.get('loyalty_accrual_pct', 5.0)
        max_percent_per_bill = place.get('max_percent_per_bill', 50.0)
        
        # Рассчитываем льготы
        benefits = self.calculate_loyalty_benefits(
            amount_gross=amount_gross,
            base_discount_pct=base_discount_pct,
            user_points_balance=user_points,
            redeem_rate=config['redeem_rate'],
            max_percent_per_bill=max_percent_per_bill,
            points_to_spend=points_to_spend
        )
        
        # Расчет начисляемых баллов
        points_earned = self.calculate_points_earned(
            amount_gross=amount_gross,
            accrual_percent=loyalty_accrual_pct,
            redeem_rate=config['redeem_rate']
        )
        
        # Применяем правило округления
        if config['rounding_rule'] == 'bankers':
            benefits['final_user_price'] = self.apply_bankers_rounding(benefits['final_user_price'])
            benefits['amount_partner_due'] = self.apply_bankers_rounding(benefits['amount_partner_due'])
            benefits['amount_user_subsidy'] = self.apply_bankers_rounding(benefits['amount_user_subsidy'])
        
        benefits['points_earned'] = points_earned
        benefits['loyalty_accrual_pct'] = loyalty_accrual_pct
        
        return benefits

# Глобальный экземпляр сервиса
loyalty_points_service = LoyaltyPointsService()
