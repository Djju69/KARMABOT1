from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey('partners.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contact = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    google_maps_url = Column(String(500), nullable=True)
    photo_file_id = Column(String(255), nullable=True)
    discount_text = Column(Text, nullable=True)
    status = Column(String(50), default='draft', nullable=False)  # draft, pending, published, rejected
    priority_level = Column(Integer, default=0)
    subcategory_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)
    area_id = Column(Integer, ForeignKey('areas.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    partner = relationship("Partner", back_populates="cards")
    category = relationship("Category", foreign_keys=[category_id])
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    photos = relationship("CardPhoto", back_populates="card", order_by="CardPhoto.position")
    qr_codes = relationship("QRCode", back_populates="card")
    moderation_logs = relationship("ModerationLog", back_populates="card")

class CardPhoto(Base):
    __tablename__ = 'card_photos'
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'), nullable=False)
    file_id = Column(String(255), nullable=False)
    position = Column(Integer, default=0)
    
    # Relationships
    card = relationship("Card", back_populates="photos")

class QRCode(Base):
    __tablename__ = 'qr_codes'
    
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    is_redeemed = Column(Boolean, default=False)
    redeemed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    card = relationship("Card", back_populates="qr_codes")
