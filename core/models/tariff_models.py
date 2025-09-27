"""
Модели тарифной системы для партнеров
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal

class TariffType(Enum):
    """Типы тарифов"""
    FREE_STARTER = "free_starter"
    BUSINESS = "business" 
    ENTERPRISE = "enterprise"

@dataclass
class TariffFeatures:
    """Функции тарифа"""
    max_transactions_per_month: int
    commission_rate: float  # Процент комиссии (0.12 = 12%)
    analytics_enabled: bool
    priority_support: bool
    api_access: bool
    custom_integrations: bool
    dedicated_manager: bool

@dataclass
class Tariff:
    """Модель тарифа"""
    id: Optional[int]
    name: str
    tariff_type: TariffType
    price_vnd: int  # Цена в вьетнамских донгах
    features: TariffFeatures
    description: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Предустановленные тарифы согласно документации
DEFAULT_TARIFFS = {
    TariffType.FREE_STARTER: Tariff(
        id=None,
        name="FREE STARTER",
        tariff_type=TariffType.FREE_STARTER,
        price_vnd=0,
        features=TariffFeatures(
            max_transactions_per_month=15,
            commission_rate=0.12,  # 12%
            analytics_enabled=False,
            priority_support=False,
            api_access=False,
            custom_integrations=False,
            dedicated_manager=False
        ),
        description="Базовые карты, QR-коды, лимит 15 транзакций в месяц"
    ),
    
    TariffType.BUSINESS: Tariff(
        id=None,
        name="BUSINESS",
        tariff_type=TariffType.BUSINESS,
        price_vnd=490000,  # 490,000 VND
        features=TariffFeatures(
            max_transactions_per_month=100,
            commission_rate=0.06,  # 6%
            analytics_enabled=True,
            priority_support=True,
            api_access=False,
            custom_integrations=False,
            dedicated_manager=False
        ),
        description="Расширенная аналитика, приоритетная поддержка, лимит 100 транзакций"
    ),
    
    TariffType.ENTERPRISE: Tariff(
        id=None,
        name="ENTERPRISE", 
        tariff_type=TariffType.ENTERPRISE,
        price_vnd=960000,  # 960,000 VND
        features=TariffFeatures(
            max_transactions_per_month=-1,  # Безлимит
            commission_rate=0.04,  # 4%
            analytics_enabled=True,
            priority_support=True,
            api_access=True,
            custom_integrations=True,
            dedicated_manager=True
        ),
        description="API доступ, кастомные интеграции, выделенный менеджер, безлимит транзакций"
    )
}