"""
Модель профиля пользователя с системой уровней и статистикой
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Numeric, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserLevel(Enum):
    """Уровни пользователей в системе лояльности"""
    BRONZE = "bronze"
    SILVER = "silver" 
    GOLD = "gold"
    PLATINUM = "platinum"

class UserProfile(Base):
    """
    Расширенный профиль пользователя с полной статистикой
    """
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True, comment="ID пользователя Telegram")
    
    # Основная информация
    username = Column(String(255), nullable=True, comment="Username в Telegram")
    first_name = Column(String(255), nullable=True, comment="Имя")
    last_name = Column(String(255), nullable=True, comment="Фамилия")
    phone = Column(String(20), nullable=True, comment="Номер телефона")
    email = Column(String(255), nullable=True, comment="Email")
    
    # Система уровней
    level = Column(SQLEnum(UserLevel), default=UserLevel.BRONZE, comment="Уровень пользователя")
    level_points = Column(Integer, default=0, comment="Очки для следующего уровня")
    level_progress = Column(Numeric(5, 2), default=0, comment="Прогресс до следующего уровня (%)")
    
    # Статистика активности
    total_visits = Column(Integer, default=0, comment="Общее количество посещений")
    total_reviews = Column(Integer, default=0, comment="Общее количество отзывов")
    total_qr_scans = Column(Integer, default=0, comment="Общее количество сканирований QR")
    total_purchases = Column(Integer, default=0, comment="Общее количество покупок")
    total_spent = Column(Numeric(10, 2), default=0, comment="Общая сумма потраченных средств")
    
    # Реферальная статистика
    total_referrals = Column(Integer, default=0, comment="Общее количество рефералов")
    referral_earnings = Column(Numeric(10, 2), default=0, comment="Доходы от рефералов")
    
    # Настройки профиля
    notifications_enabled = Column(Boolean, default=True, comment="Включены ли уведомления")
    email_notifications = Column(Boolean, default=True, comment="Email уведомления")
    push_notifications = Column(Boolean, default=True, comment="Push уведомления")
    privacy_level = Column(String(50), default='standard', comment="Уровень приватности")
    
    # Дополнительная информация
    bio = Column(Text, nullable=True, comment="Биография пользователя")
    avatar_url = Column(String(500), nullable=True, comment="URL аватара")
    timezone = Column(String(50), default='UTC+7', comment="Часовой пояс")
    language = Column(String(10), default='ru', comment="Предпочитаемый язык")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, comment="Дата создания профиля")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Дата последнего обновления")
    last_activity = Column(DateTime, default=datetime.utcnow, comment="Дата последней активности")
    
    # Связи
    user_settings = relationship("UserSettings", back_populates="profile", uselist=False)
    loyalty_balance = relationship("LoyaltyBalance", back_populates="profile", uselist=False)
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, level={self.level.value}, points={self.level_points})>"
    
    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.username or f"User {self.user_id}"
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя"""
        return self.username or self.full_name or f"User {self.user_id}"
    
    def calculate_level_progress(self) -> float:
        """Расчет прогресса до следующего уровня"""
        level_thresholds = {
            UserLevel.BRONZE: 0,
            UserLevel.SILVER: 1000,
            UserLevel.GOLD: 5000,
            UserLevel.PLATINUM: 15000
        }
        
        current_threshold = level_thresholds[self.level]
        next_level = self._get_next_level()
        next_threshold = level_thresholds[next_level] if next_level else level_thresholds[UserLevel.PLATINUM]
        
        if next_threshold == current_threshold:
            return 100.0
        
        progress = ((self.level_points - current_threshold) / (next_threshold - current_threshold)) * 100
        return min(100.0, max(0.0, progress))
    
    def _get_next_level(self) -> Optional[UserLevel]:
        """Получение следующего уровня"""
        level_order = [UserLevel.BRONZE, UserLevel.SILVER, UserLevel.GOLD, UserLevel.PLATINUM]
        try:
            current_index = level_order.index(self.level)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1]
        except ValueError:
            pass
        return None
    
    def can_level_up(self) -> bool:
        """Проверка возможности повышения уровня"""
        return self.calculate_level_progress() >= 100.0
    
    def level_up(self) -> bool:
        """Повышение уровня пользователя"""
        next_level = self._get_next_level()
        if next_level and self.can_level_up():
            self.level = next_level
            self.level_progress = 0.0
            return True
        return False

class UserActivityLog(Base):
    """
    Лог активности пользователя для отслеживания статистики
    """
    __tablename__ = 'user_activity_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, comment="Тип активности")
    activity_data = Column(Text, nullable=True, comment="Дополнительные данные активности")
    points_earned = Column(Integer, default=0, comment="Заработанные очки")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Дата активности")
    
    # Индексы для оптимизации
    __table_args__ = (
        {'comment': 'Лог активности пользователей для статистики и аналитики'},
    )

class UserAchievement(Base):
    """
    Достижения пользователей
    """
    __tablename__ = 'user_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    achievement_type = Column(String(50), nullable=False, comment="Тип достижения")
    achievement_name = Column(String(255), nullable=False, comment="Название достижения")
    achievement_description = Column(Text, nullable=True, comment="Описание достижения")
    points_reward = Column(Integer, default=0, comment="Награда в очках")
    unlocked_at = Column(DateTime, default=datetime.utcnow, comment="Дата получения")
    
    # Индексы
    __table_args__ = (
        {'comment': 'Достижения пользователей'},
    )
