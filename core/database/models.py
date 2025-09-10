from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Table, Text, Enum, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# SQLAlchemy declarative base
Base = declarative_base()

# Базовый класс для всех моделей (теперь наследуется от SQLAlchemy Base)
class BaseModelMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Модель категорий заведений
class Category(Base, BaseModelMixin):
    __tablename__ = 'categories'

    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Отношения
    places = relationship("Place", secondary="place_categories", back_populates="categories")

# Модель заведений (партнеров)
class Place(Base, BaseModelMixin):
    __tablename__ = 'places'
    
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Время работы (можно хранить как JSON или отдельной таблицей)
    working_hours = Column(JSON, nullable=True)
    
    # Рейтинг и отзывы
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    
    # Статусы
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Внешние ключи и отношения
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    categories = relationship("Category", secondary="place_categories", back_populates="places")
    media = relationship("Media", back_populates="place")
    reviews = relationship("Review", back_populates="place")

# Связь многие-ко-многим между Place и Category
place_categories = Table(
    'place_categories',
    Base.metadata,
    Column('place_id', Integer, ForeignKey('places.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

# Модель для хранения медиа (фото, видео)
class Media(Base, BaseModelMixin):
    __tablename__ = 'media'
    
    file_id = Column(String(255), nullable=False)  # ID файла в хранилище
    file_type = Column(String(50), nullable=False)  # image/jpeg, video/mp4 и т.д.
    url = Column(String(500), nullable=False)  # URL для доступа к файлу
    is_cover = Column(Boolean, default=False)
    
    # Внешние ключи
    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Отношения
    place = relationship("Place", back_populates="media")

# Модель отзывов
class Review(Base, BaseModelMixin):
    __tablename__ = 'reviews'
    
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    
    # Внешние ключи
    place_id = Column(Integer, ForeignKey('places.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Отношения
    place = relationship("Place", back_populates="reviews")
    user = relationship("User")  # Упрощенная связь с пользователем

# Pydantic модели для валидации
class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    working_hours: Optional[dict] = None
    category_ids: List[int] = []

class PlaceCreate(PlaceBase):
    pass

class PlaceUpdate(PlaceBase):
    name: Optional[str] = None
    address: Optional[str] = None

class PlaceInDB(PlaceBase):
    id: int
    rating: float = 0.0
    reviews_count: int = 0
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Модели для категорий
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryInDB(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
