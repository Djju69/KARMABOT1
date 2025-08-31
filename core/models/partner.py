from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Partner(Base):
    __tablename__ = 'partners'
    
    id = Column(Integer, primary_key=True)
    tg_user_id = Column(Integer, unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cards = relationship("Card", back_populates="partner")
    moderation_actions = relationship("ModerationLog", back_populates="moderator")

class ModerationLog(Base):
    __tablename__ = 'moderation_logs'
    
    id = Column(Integer, primary_key=True)
    moderator_id = Column(Integer, ForeignKey('partners.id'), nullable=False)
    card_id = Column(Integer, ForeignKey('cards.id'), nullable=False)
    action = Column(String(50), nullable=False)  # 'approve', 'reject', 'edit', etc.
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    moderator = relationship("Partner", back_populates="moderation_actions")
    card = relationship("Card", back_populates="moderation_logs")
