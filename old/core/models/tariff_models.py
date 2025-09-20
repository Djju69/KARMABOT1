"""
Модели для тарифной системы KARMABOT1
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

class TariffType(Enum):
    """Типы тарифов"""
    FREE_STARTER = "free_starter"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class TariffStatus(Enum):
    """Статусы тарифа"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class Tariff:
    """Модель тарифа"""
    id: int
    name: str
    tariff_type: TariffType
    monthly_price_vnd: int
    commission_percent: float
    transaction_limit: Optional[int]  # None = безлимит
    features: List[str]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class PartnerTariff:
    """Тариф партнера"""
    id: int
    partner_id: int
    tariff_id: int
    status: TariffStatus
    start_date: datetime
    end_date: Optional[datetime]
    auto_renew: bool = True
    payment_method: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class TariffUsage:
    """Использование тарифа"""
    id: int
    partner_id: int
    tariff_id: int
    month: int
    year: int
    transactions_count: int
    transactions_limit: int
    commission_earned: float
    created_at: Optional[datetime] = None

# Дефолтные тарифы
DEFAULT_TARIFFS = [
    Tariff(
        id=1,
        name="FREE STARTER",
        tariff_type=TariffType.FREE_STARTER,
        monthly_price_vnd=0,
        commission_percent=12.0,
        transaction_limit=15,
        features=[
            "Базовые карты лояльности",
            "QR-коды для скидок",
            "Простая аналитика",
            "Email поддержка"
        ]
    ),
    Tariff(
        id=2,
        name="BUSINESS",
        tariff_type=TariffType.BUSINESS,
        monthly_price_vnd=490000,
        commission_percent=6.0,
        transaction_limit=100,
        features=[
            "Расширенные карты лояльности",
            "QR-коды с кастомизацией",
            "Детальная аналитика",
            "Приоритетная поддержка",
            "API доступ (ограниченный)",
            "Интеграция с CRM"
        ]
    ),
    Tariff(
        id=3,
        name="ENTERPRISE",
        tariff_type=TariffType.ENTERPRISE,
        monthly_price_vnd=960000,
        commission_percent=4.0,
        transaction_limit=None,  # Безлимит
        features=[
            "Полный функционал карт",
            "Кастомные QR-коды",
            "Продвинутая аналитика",
            "Выделенный менеджер",
            "Полный API доступ",
            "Кастомные интеграции",
            "Белый лейбл",
            "Приоритетная разработка"
        ]
    )
]
