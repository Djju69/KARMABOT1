"""
Модели для системы лояльности и реферальной программы.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class LoyaltyTransactionType(str, Enum):
    """Типы транзакций лояльности."""
    ACTIVITY = "activity"
    REFERRAL_BONUS = "referral_bonus"
    SPEND = "spend"
    MANUAL = "manual"


class ActivityType(str, Enum):
    """Типы активностей для начисления баллов."""
    DAILY_CHECKIN = "daily_checkin"
    PROFILE_COMPLETION = "profile_completion"
    CARD_BINDING = "card_binding"
    GEO_CHECKIN = "geo_checkin"
    REFERRAL_SIGNUP = "referral_signup"


class LoyaltyTransaction(BaseModel):
    """Модель транзакции лояльности."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    points: int
    transaction_type: LoyaltyTransactionType
    activity_type: Optional[ActivityType] = None
    reference_id: Optional[UUID] = None  # ID связанной сущности (например, реферала)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class LoyaltyBalance(BaseModel):
    """Текущий баланс лояльности пользователя."""
    user_id: UUID
    total_points: int = 0
    available_points: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ActivityRule(BaseModel):
    """Правила начисления баллов за активность."""
    activity_type: ActivityType
    points: int
    cooldown_hours: int  # Часы между начислениями
    daily_cap: Optional[int] = None  # Максимум в день (если None - без ограничений)
    is_active: bool = True

    class Config:
        from_attributes = True


class ReferralProgram(BaseModel):
    """Настройки реферальной программы."""
    referrer_bonus: int = 100  # Бонус пригласившему
    referee_bonus: int = 50    # Бонус приглашенному
    min_purchase_for_bonus: Optional[int] = None  # Минимальная сумма покупки для активации бонуса
    is_active: bool = True

    class Config:
        from_attributes = True


class ReferralLink(BaseModel):
    """Реферальная ссылка пользователя."""
    user_id: UUID
    referral_code: str  # Уникальный реферальный код
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        from_attributes = True


class Referral(BaseModel):
    """Запись о приглашении."""
    referrer_id: UUID  # Кто пригласил
    referee_id: UUID   # Кого пригласили
    referral_code: str
    referrer_bonus_awarded: bool = False
    referee_bonus_awarded: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    bonus_awarded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
