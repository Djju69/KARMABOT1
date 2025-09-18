"""
Модель многоуровневой реферальной системы
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, BigInteger, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ReferralTree(Base):
    """
    Модель многоуровневого дерева рефералов
    Поддерживает до 3 уровней рефералов с автоматическим начислением бонусов
    """
    __tablename__ = 'referral_tree'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True, comment="ID пользователя")
    referrer_id = Column(BigInteger, nullable=True, index=True, comment="ID того, кто пригласил")
    level = Column(Integer, default=1, comment="Уровень в дереве (1-3)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Дата создания записи")
    total_earnings = Column(Numeric(10, 2), default=0, comment="Общие заработанные бонусы")
    total_referrals = Column(Integer, default=0, comment="Общее количество рефералов")
    active_referrals = Column(Integer, default=0, comment="Активные рефералы")
    
    # Связи
    referrer = relationship("ReferralTree", 
                          foreign_keys=[referrer_id],
                          back_populates="referrals",
                          remote_side=[id])
    referrals = relationship("ReferralTree", 
                            foreign_keys=[referrer_id],
                            back_populates="referrer")
    
    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('idx_user_referrer', 'user_id', 'referrer_id'),
        Index('idx_referrer_level', 'referrer_id', 'level'),
        Index('idx_created_at', 'created_at'),
    )

class ReferralBonus(Base):
    """
    Модель для отслеживания начисленных бонусов по уровням
    """
    __tablename__ = 'referral_bonuses'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BigInteger, nullable=False, index=True, comment="ID получателя бонуса")
    referred_id = Column(BigInteger, nullable=False, index=True, comment="ID реферала")
    level = Column(Integer, nullable=False, comment="Уровень реферала (1-3)")
    bonus_amount = Column(Numeric(10, 2), nullable=False, comment="Размер бонуса")
    source_transaction_id = Column(Integer, nullable=True, comment="ID исходной транзакции")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Дата начисления")
    
    # Индексы
    __table_args__ = (
        Index('idx_referrer_level', 'referrer_id', 'level'),
        Index('idx_referred_level', 'referred_id', 'level'),
        Index('idx_created_at', 'created_at'),
    )

class ReferralStats(Base):
    """
    Модель для агрегированной статистики рефералов
    """
    __tablename__ = 'referral_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    
    # Статистика по уровням
    level_1_count = Column(Integer, default=0, comment="Количество рефералов 1-го уровня")
    level_2_count = Column(Integer, default=0, comment="Количество рефералов 2-го уровня")
    level_3_count = Column(Integer, default=0, comment="Количество рефералов 3-го уровня")
    
    # Доходы по уровням
    level_1_earnings = Column(Numeric(10, 2), default=0, comment="Доходы с 1-го уровня")
    level_2_earnings = Column(Numeric(10, 2), default=0, comment="Доходы со 2-го уровня")
    level_3_earnings = Column(Numeric(10, 2), default=0, comment="Доходы с 3-го уровня")
    
    # Общая статистика
    total_referrals = Column(Integer, default=0, comment="Общее количество рефералов")
    total_earnings = Column(Numeric(10, 2), default=0, comment="Общие доходы")
    
    # Временные метки
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
