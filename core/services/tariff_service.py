"""
Сервис управления тарифной системой для партнеров
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from core.models.tariff_models import Tariff, TariffType, TariffFeatures, DEFAULT_TARIFFS
from core.database.db_adapter import db_v2

logger = logging.getLogger(__name__)

class TariffService:
    """Сервис управления тарифами партнеров"""
    
    def __init__(self):
        self.default_tariffs = DEFAULT_TARIFFS
    
    def get_all_tariffs(self) -> List[Tariff]:
        """Получить все доступные тарифы"""
        try:
            query = """
                SELECT id, name, tariff_type, price_vnd, max_transactions_per_month,
                       commission_rate, analytics_enabled, priority_support,
                       api_access, custom_integrations, dedicated_manager,
                       description, is_active, created_at, updated_at
                FROM partner_tariffs 
                WHERE is_active = TRUE
                ORDER BY price_vnd ASC
            """
            
            rows = db_v2.fetch_all(query)
            
            tariffs = []
            for row in rows:
                features = TariffFeatures(
                    max_transactions_per_month=row[4],
                    commission_rate=float(row[5]),
                    analytics_enabled=bool(row[6]),
                    priority_support=bool(row[7]),
                    api_access=bool(row[8]),
                    custom_integrations=bool(row[9]),
                    dedicated_manager=bool(row[10])
                )
                
                tariff = Tariff(
                    id=row[0],
                    name=row[1],
                    tariff_type=TariffType(row[2]),
                    price_vnd=row[3],
                    features=features,
                    description=row[11],
                    is_active=bool(row[12]),
                    created_at=row[13],
                    updated_at=row[14]
                )
                tariffs.append(tariff)
            
            return tariffs
            
        except Exception as e:
            logger.error(f"❌ Error getting tariffs: {e}")
            return []
    
    def get_tariff_by_type(self, tariff_type: TariffType) -> Optional[Tariff]:
        """Получить тариф по типу"""
        try:
            query = """
                SELECT id, name, tariff_type, price_vnd, max_transactions_per_month,
                       commission_rate, analytics_enabled, priority_support,
                       api_access, custom_integrations, dedicated_manager,
                       description, is_active, created_at, updated_at
                FROM partner_tariffs 
                WHERE tariff_type = $1 AND is_active = TRUE
            """
            
            row = db_v2.fetch_one(query, (tariff_type.value,))
            
            if not row:
                return None
            
            features = TariffFeatures(
                max_transactions_per_month=row[4],
                commission_rate=float(row[5]),
                analytics_enabled=row[6],
                priority_support=row[7],
                api_access=row[8],
                custom_integrations=row[9],
                dedicated_manager=row[10]
            )
            
            return Tariff(
                id=row[0],
                name=row[1],
                tariff_type=TariffType(row[2]),
                price_vnd=row[3],
                features=features,
                description=row[11],
                is_active=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting tariff by type {tariff_type}: {e}")
            return None
    
    def get_partner_current_tariff(self, partner_id: int) -> Optional[Tariff]:
        """Получить текущий тариф партнера"""
        try:
            query = """
                SELECT t.id, t.name, t.tariff_type, t.price_vnd, t.max_transactions_per_month,
                       t.commission_rate, t.analytics_enabled, t.priority_support,
                       t.api_access, t.custom_integrations, t.dedicated_manager,
                       t.description, t.is_active, t.created_at, t.updated_at
                FROM partner_tariff_subscriptions s
                JOIN partner_tariffs t ON s.tariff_id = t.id
                WHERE s.partner_id = $1 AND s.is_active = TRUE
                AND (s.expires_at IS NULL OR s.expires_at > NOW())
            """
            
            row = db_v2.fetch_one(query, (partner_id,))
            
            if not row:
                # Возвращаем FREE STARTER по умолчанию
                return self.get_tariff_by_type(TariffType.FREE_STARTER)
            
            features = TariffFeatures(
                max_transactions_per_month=row[4],
                commission_rate=float(row[5]),
                analytics_enabled=row[6],
                priority_support=row[7],
                api_access=row[8],
                custom_integrations=row[9],
                dedicated_manager=row[10]
            )
            
            return Tariff(
                id=row[0],
                name=row[1],
                tariff_type=TariffType(row[2]),
                price_vnd=row[3],
                features=features,
                description=row[11],
                is_active=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting partner tariff for {partner_id}: {e}")
            return self.get_tariff_by_type(TariffType.FREE_STARTER)
    
    def subscribe_partner_to_tariff(
        self, 
        partner_id: int, 
        tariff_type: TariffType,
        duration_months: int = 1
    ) -> bool:
        """Подписать партнера на тариф"""
        try:
            # Получаем тариф
            tariff = self.get_tariff_by_type(tariff_type)
            if not tariff:
                logger.error(f"❌ Tariff {tariff_type} not found")
                return False
            
            # Деактивируем текущую подписку
            deactivate_query = """
                UPDATE partner_tariff_subscriptions 
                SET is_active = FALSE, updated_at = NOW()
                WHERE partner_id = $1 AND is_active = TRUE
            """
            db_v2.execute(deactivate_query, (partner_id,))
            
            # Создаем новую подписку
            expires_at = datetime.now() + timedelta(days=duration_months * 30)
            
            subscribe_query = """
                INSERT INTO partner_tariff_subscriptions 
                (partner_id, tariff_id, started_at, expires_at, is_active, auto_renew, payment_status)
                VALUES ($1, $2, NOW(), $3, TRUE, FALSE, 'paid')
            """
            
            db_v2.execute(subscribe_query, (partner_id, tariff.id, expires_at))
            
            logger.info(f"✅ Partner {partner_id} subscribed to {tariff_type.value} tariff")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error subscribing partner {partner_id} to {tariff_type}: {e}")
            return False
    
    def check_transaction_limit(self, partner_id: int) -> Dict[str, Any]:
        """Проверить лимит транзакций партнера"""
        try:
            # Получаем текущий тариф
            tariff = self.get_partner_current_tariff(partner_id)
            if not tariff:
                return {"allowed": False, "reason": "No tariff found"}
            
            # Если безлимит
            if tariff.features.max_transactions_per_month == -1:
                return {"allowed": True, "remaining": -1, "tariff": tariff.name}
            
            # Считаем транзакции за текущий месяц
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            query = """
                SELECT COUNT(*) 
                FROM loyalty_transactions 
                WHERE partner_id = $1 
                AND created_at >= $2
                AND transaction_type = 'purchase'
            """
            
            used_transactions = db_v2.fetch_one(query, (partner_id, current_month_start))[0]
            remaining = tariff.features.max_transactions_per_month - used_transactions
            
            return {
                "allowed": remaining > 0,
                "remaining": max(0, remaining),
                "used": used_transactions,
                "limit": tariff.features.max_transactions_per_month,
                "tariff": tariff.name
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking transaction limit for partner {partner_id}: {e}")
            return {"allowed": False, "reason": "Database error"}
    
    async def get_tariff_commission_rate(self, partner_id: int) -> float:
        """Получить процент комиссии для партнера"""
        try:
            tariff = await self.get_partner_current_tariff(partner_id)
            if not tariff:
                return 0.12  # Дефолтная комиссия 12%
            
            return tariff.features.commission_rate
            
        except Exception as e:
            logger.error(f"❌ Error getting commission rate for partner {partner_id}: {e}")
            return 0.12
    
    async def get_partner_tariff_features(self, partner_id: int) -> Dict[str, Any]:
        """Получить функции тарифа партнера"""
        try:
            tariff = await self.get_partner_current_tariff(partner_id)
            if not tariff:
                return {
                    "analytics_enabled": False,
                    "priority_support": False,
                    "api_access": False,
                    "custom_integrations": False,
                    "dedicated_manager": False
                }
            
            return {
                "analytics_enabled": tariff.features.analytics_enabled,
                "priority_support": tariff.features.priority_support,
                "api_access": tariff.features.api_access,
                "custom_integrations": tariff.features.custom_integrations,
                "dedicated_manager": tariff.features.dedicated_manager,
                "tariff_name": tariff.name,
                "commission_rate": tariff.features.commission_rate
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting tariff features for partner {partner_id}: {e}")
            return {
                "analytics_enabled": False,
                "priority_support": False,
                "api_access": False,
                "custom_integrations": False,
                "dedicated_manager": False
            }

# Глобальный экземпляр сервиса
tariff_service = TariffService()