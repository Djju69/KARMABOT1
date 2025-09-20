"""
Сервис для управления тарифной системой
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from core.models.tariff_models import Tariff, TariffType, TariffStatus, PartnerTariff, TariffUsage, DEFAULT_TARIFFS

logger = logging.getLogger(__name__)

class TariffService:
    """Сервис для управления тарифами"""
    
    def __init__(self):
        self.tariffs = {t.id: t for t in DEFAULT_TARIFFS}
    
    async def get_all_tariffs(self) -> List[Tariff]:
        """Получить все доступные тарифы"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, name, tariff_type, monthly_price_vnd, commission_percent, 
                           transaction_limit, features, is_active, created_at, updated_at
                    FROM tariffs 
                    WHERE is_active = 1
                    ORDER BY monthly_price_vnd ASC
                """)
                rows = cursor.fetchall()
                
                if rows:
                    tariffs = []
                    for row in rows:
                        features = eval(row[6]) if row[6] else []
                        tariff = Tariff(
                            id=row[0],
                            name=row[1],
                            tariff_type=TariffType(row[2]),
                            monthly_price_vnd=row[3],
                            commission_percent=row[4],
                            transaction_limit=row[5],
                            features=features,
                            is_active=bool(row[7]),
                            created_at=row[8],
                            updated_at=row[9]
                        )
                        tariffs.append(tariff)
                    return tariffs
                else:
                    # Возвращаем дефолтные тарифы если БД пустая
                    return list(self.tariffs.values())
                    
        except Exception as e:
            logger.error(f"Error getting tariffs: {e}")
            return list(self.tariffs.values())
    
    async def get_tariff_by_id(self, tariff_id: int) -> Optional[Tariff]:
        """Получить тариф по ID"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, name, tariff_type, monthly_price_vnd, commission_percent, 
                           transaction_limit, features, is_active, created_at, updated_at
                    FROM tariffs 
                    WHERE id = ? AND is_active = 1
                """, (tariff_id,))
                row = cursor.fetchone()
                
                if row:
                    features = eval(row[6]) if row[6] else []
                    return Tariff(
                        id=row[0],
                        name=row[1],
                        tariff_type=TariffType(row[2]),
                        monthly_price_vnd=row[3],
                        commission_percent=row[4],
                        transaction_limit=row[5],
                        features=features,
                        is_active=bool(row[7]),
                        created_at=row[8],
                        updated_at=row[9]
                    )
                else:
                    return self.tariffs.get(tariff_id)
                    
        except Exception as e:
            logger.error(f"Error getting tariff by ID: {e}")
            return self.tariffs.get(tariff_id)
    
    async def get_partner_tariff(self, partner_id: int) -> Optional[PartnerTariff]:
        """Получить текущий тариф партнера"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, partner_id, tariff_id, status, start_date, end_date, 
                           auto_renew, payment_method, created_at, updated_at
                    FROM partner_tariffs 
                    WHERE partner_id = ? AND status = 'active'
                    ORDER BY start_date DESC LIMIT 1
                """, (partner_id,))
                row = cursor.fetchone()
                
                if row:
                    return PartnerTariff(
                        id=row[0],
                        partner_id=row[1],
                        tariff_id=row[2],
                        status=TariffStatus(row[3]),
                        start_date=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                        end_date=datetime.fromisoformat(row[5]) if row[5] else None,
                        auto_renew=bool(row[6]),
                        payment_method=row[7],
                        created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                        updated_at=datetime.fromisoformat(row[9]) if row[9] else None
                    )
                else:
                    # Возвращаем FREE STARTER по умолчанию
                    return PartnerTariff(
                        id=0,
                        partner_id=partner_id,
                        tariff_id=1,  # FREE STARTER
                        status=TariffStatus.ACTIVE,
                        start_date=datetime.now(),
                        end_date=None,
                        auto_renew=True
                    )
                    
        except Exception as e:
            logger.error(f"Error getting partner tariff: {e}")
            # Возвращаем FREE STARTER по умолчанию
            return PartnerTariff(
                id=0,
                partner_id=partner_id,
                tariff_id=1,  # FREE STARTER
                status=TariffStatus.ACTIVE,
                start_date=datetime.now(),
                end_date=None,
                auto_renew=True
            )
    
    async def upgrade_partner_tariff(self, partner_id: int, new_tariff_id: int, payment_method: str = None) -> Dict[str, Any]:
        """Обновить тариф партнера"""
        try:
            from core.database.db_v2 import get_connection
            
            # Получаем новый тариф
            new_tariff = await self.get_tariff_by_id(new_tariff_id)
            if not new_tariff:
                return {"success": False, "error": "Тариф не найден"}
            
            # Получаем текущий тариф партнера
            current_tariff = await self.get_partner_tariff(partner_id)
            
            with get_connection() as conn:
                # Деактивируем текущий тариф
                if current_tariff and current_tariff.id > 0:
                    conn.execute("""
                        UPDATE partner_tariffs 
                        SET status = 'cancelled', updated_at = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), current_tariff.id))
                
                # Создаем новый тариф
                start_date = datetime.now()
                end_date = start_date + timedelta(days=30)  # Месячная подписка
                
                conn.execute("""
                    INSERT INTO partner_tariffs (partner_id, tariff_id, status, start_date, end_date, auto_renew, payment_method, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    partner_id, new_tariff_id, TariffStatus.ACTIVE.value,
                    start_date.isoformat(), end_date.isoformat(),
                    True, payment_method, datetime.now().isoformat()
                ))
                
                conn.commit()
                
                return {
                    "success": True,
                    "message": f"Тариф успешно обновлен на {new_tariff.name}",
                    "tariff": {
                        "name": new_tariff.name,
                        "price": new_tariff.monthly_price_vnd,
                        "commission": new_tariff.commission_percent,
                        "limit": new_tariff.transaction_limit,
                        "features": new_tariff.features
                    }
                }
                
        except Exception as e:
            logger.error(f"Error upgrading partner tariff: {e}")
            return {"success": False, "error": "Ошибка при обновлении тарифа"}
    
    async def get_tariff_usage(self, partner_id: int, month: int = None, year: int = None) -> Dict[str, Any]:
        """Получить использование тарифа за период"""
        try:
            from core.database.db_v2 import get_connection
            
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            with get_connection() as conn:
                # Получаем текущий тариф партнера
                partner_tariff = await self.get_partner_tariff(partner_id)
                tariff = await self.get_tariff_by_id(partner_tariff.tariff_id)
                
                # Получаем статистику использования
                cursor = conn.execute("""
                    SELECT COUNT(*) as transactions_count, SUM(amount) as total_amount
                    FROM transactions 
                    WHERE partner_id = ? AND strftime('%m', created_at) = ? AND strftime('%Y', created_at) = ?
                """, (partner_id, f"{month:02d}", str(year)))
                
                usage_data = cursor.fetchone()
                transactions_count = usage_data[0] if usage_data else 0
                total_amount = usage_data[1] if usage_data and usage_data[1] else 0
                
                # Рассчитываем комиссию
                commission_earned = float(total_amount) * (tariff.commission_percent / 100) if total_amount else 0
                
                # Проверяем лимиты
                limit_reached = False
                if tariff.transaction_limit and transactions_count >= tariff.transaction_limit:
                    limit_reached = True
                
                return {
                    "tariff": {
                        "name": tariff.name,
                        "limit": tariff.transaction_limit,
                        "commission_percent": tariff.commission_percent
                    },
                    "usage": {
                        "transactions_count": transactions_count,
                        "total_amount": total_amount,
                        "commission_earned": commission_earned,
                        "limit_reached": limit_reached,
                        "remaining_transactions": tariff.transaction_limit - transactions_count if tariff.transaction_limit else None
                    },
                    "period": {
                        "month": month,
                        "year": year
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting tariff usage: {e}")
            return {"error": "Ошибка при получении статистики использования"}
    
    async def check_tariff_limits(self, partner_id: int) -> Dict[str, Any]:
        """Проверить лимиты тарифа"""
        try:
            usage = await self.get_tariff_usage(partner_id)
            
            if "error" in usage:
                return usage
            
            tariff = usage["tariff"]
            usage_data = usage["usage"]
            
            warnings = []
            errors = []
            
            # Проверяем лимит транзакций
            if tariff["limit"] and usage_data["limit_reached"]:
                errors.append(f"Достигнут лимит транзакций: {usage_data['transactions_count']}/{tariff['limit']}")
            elif tariff["limit"] and usage_data["transactions_count"] >= tariff["limit"] * 0.8:
                warnings.append(f"Приближается лимит транзакций: {usage_data['transactions_count']}/{tariff['limit']}")
            
            return {
                "status": "ok" if not errors else "error",
                "warnings": warnings,
                "errors": errors,
                "usage": usage_data
            }
            
        except Exception as e:
            logger.error(f"Error checking tariff limits: {e}")
            return {"error": "Ошибка при проверке лимитов"}

# Создаем экземпляр сервиса
tariff_service = TariffService()
