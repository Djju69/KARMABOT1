"""
Payment Service - обработка платежей с ИСПРАВЛЕННОЙ логикой баллов
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ЛИБО ТРАТИШЬ, ЛИБО НАКАПЛИВАЕШЬ
"""
import math
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentService:
    """Сервис для обработки платежей с исправленной логикой баллов"""
    
    def __init__(self):
        self.redeem_rate = 5000.0  # 1 балл = 5000 VND
        self.min_purchase_for_points = 10000  # Минимальная покупка для начисления
        self.max_discount_percent = 40.0  # Максимальная скидка за баллы
    
    async def process_sale(self, partner_id: int, place_id: int, operator_id: int,
                          user_id: int, amount_gross: float, points_to_spend: int = 0,
                          qr_token: str = None) -> Dict[str, Any]:
        """
        Обработка продажи с ИСПРАВЛЕННОЙ логикой баллов
        КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ЛИБО ТРАТИШЬ, ЛИБО НАКАПЛИВАЕШЬ
        """
        try:
            from core.services.loyalty_service import loyalty_service
            from core.database.db_v2 import get_connection
            
            # Получаем данные заведения
            place_data = await self._get_place_data(place_id)
            if not place_data:
                raise ValueError("Заведение не найдено")
            
            # Получаем конфигурацию системы
            config = await self._get_loyalty_config()
            
            # ИСПРАВЛЕННАЯ логика начисления
            points_transaction = self.calculate_points_transaction(
                amount_gross=amount_gross,
                accrual_pct=place_data.get('loyalty_accrual_pct', 5.0),
                redeem_rate=config['redeem_rate'],
                points_to_spend=points_to_spend
            )
            
            # Рассчитываем льготы
            calculation = await loyalty_service.calculate_purchase_benefits(
                user_id, place_id, amount_gross, points_to_spend
            )
            
            with get_connection() as conn:
                try:
                    # Создаем продажу
                    sale_id = await self._create_partner_sale(
                        partner_id=partner_id,
                        place_id=place_id,
                        operator_telegram_id=operator_id,
                        user_telegram_id=user_id,
                        amount_gross=amount_gross,
                        base_discount_pct=calculation['base_discount_pct'],
                        extra_discount_pct=calculation['extra_discount_pct'],
                        extra_value=calculation['amount_user_subsidy'],
                        amount_partner_due=calculation['amount_partner_due'],
                        amount_user_subsidy=calculation['amount_user_subsidy'],
                        points_spent=points_transaction['points_spent'],
                        points_earned=points_transaction['points_earned'],  # Может быть 0!
                        redeem_rate=config['redeem_rate'],
                        qr_token=qr_token,
                        conn=conn
                    )
                    
                    # Обновляем баланс баллов ТОЛЬКО ОДИН РАЗ
                    net_points_change = points_transaction['net_change']  # earned - spent
                    
                    if net_points_change != 0:
                        await loyalty_service.update_user_points_balance(user_id, net_points_change)
                    
                    # Логируем операции отдельно для прозрачности
                    if points_transaction['points_spent'] > 0:
                        await loyalty_service.add_points_history(
                            user_id=user_id,
                            change_amount=-points_transaction['points_spent'],
                            reason=f"Оплата в {place_data['title']}",
                            transaction_type="spent",
                            sale_id=sale_id
                        )
                    
                    # НАЧИСЛЯЕМ ТОЛЬКО ЕСЛИ НЕ ТРАТИЛИ
                    if points_transaction['points_earned'] > 0:
                        await loyalty_service.add_points_history(
                            user_id=user_id,
                            change_amount=points_transaction['points_earned'],
                            reason=f"Покупка в {place_data['title']} (+{place_data.get('loyalty_accrual_pct', 5.0)}%) БЕЗ трат",
                            transaction_type="earned",
                            sale_id=sale_id
                        )
                    
                    # Уведомляем с КОРРЕКТНОЙ информацией
                    notification_text = self.format_sale_notification(
                        place=place_data,
                        amount_gross=amount_gross,
                        calculation=calculation,
                        points_transaction=points_transaction
                    )
                    
                    await self._add_notification(user_id, notification_text, "points_change", conn)
                    
                    conn.commit()
                    return {
                        'sale_id': sale_id,
                        'calculation': calculation,
                        'points_transaction': points_transaction,
                        'notification': notification_text
                    }
                    
                except Exception as e:
                    conn.rollback()
                    raise e
                    
        except Exception as e:
            logger.error(f"Error processing sale: {e}")
            raise
    
    def calculate_points_transaction(self, amount_gross: float, accrual_pct: float, 
                                   redeem_rate: float, points_to_spend: int = 0) -> Dict[str, Any]:
        """
        НОВЫЙ метод для правильного расчета баллов
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
    
    def format_sale_notification(self, place: Dict[str, Any], amount_gross: float, 
                               calculation: Dict[str, Any], points_transaction: Dict[str, Any]) -> str:
        """Форматирование уведомления с корректной логикой"""
        
        text = f"🛒 Покупка в {place['title']}\n"
        text += f"💰 Сумма: {amount_gross:,.0f}₫\n"
        text += f"🎁 Скидка: {calculation['total_discount_pct']:.1f}%\n"
        text += f"💸 К доплате: {calculation['final_user_price']:,.0f}₫\n"
        
        if points_transaction['operation_type'] == 'spending_only':
            text += f"💎 Списано: {points_transaction['points_spent']} баллов\n"
            text += f"ℹ️ Начисление отменено (использовали баллы)"
            
        elif points_transaction['operation_type'] == 'earning_only':
            if points_transaction['points_earned'] > 0:
                text += f"🎁 Начислено: +{points_transaction['points_earned']} баллов"
            else:
                text += f"ℹ️ Сумма меньше минимума для начисления"
        
        return text
    
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
    
    async def _create_partner_sale(self, partner_id: int, place_id: int, operator_telegram_id: int,
                                 user_telegram_id: int, amount_gross: float, base_discount_pct: float,
                                 extra_discount_pct: float, extra_value: float, amount_partner_due: float,
                                 amount_user_subsidy: float, points_spent: int, points_earned: int,
                                 redeem_rate: float, qr_token: str, conn) -> int:
        """Создать запись о продаже"""
        try:
            cursor = conn.execute("""
                INSERT INTO partner_sales (
                    partner_id, place_id, operator_telegram_id, user_telegram_id,
                    amount_gross, base_discount_pct, extra_discount_pct, extra_value,
                    amount_partner_due, amount_user_subsidy, points_spent, points_earned,
                    redeem_rate, qr_token, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                partner_id, place_id, operator_telegram_id, user_telegram_id,
                amount_gross, base_discount_pct, extra_discount_pct, extra_value,
                amount_partner_due, amount_user_subsidy, points_spent, points_earned,
                redeem_rate, qr_token, datetime.now().isoformat()
            ))
            
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error creating partner sale: {e}")
            raise
    
    async def _add_notification(self, user_id: int, message: str, notification_type: str, conn):
        """Добавить уведомление пользователю"""
        try:
            conn.execute("""
                INSERT INTO user_notifications (user_id, message, notification_type, is_read, created_at)
                VALUES (?, ?, ?, 0, ?)
            """, (user_id, message, notification_type, datetime.now().isoformat()))
            
        except Exception as e:
            logger.error(f"Error adding notification: {e}")
            raise

# Глобальный экземпляр сервиса
payment_service = PaymentService()
