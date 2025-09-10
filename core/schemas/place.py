from pydantic import BaseModel, Field, HttpUrl, validator, conint, confloat
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class WeekDay(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class WorkingHours(BaseModel):
    """Working hours for a single day"""
    open: str = Field(..., description="Opening time in HH:MM format")
    close: str = Field(..., description="Closing time in HH:MM format")
    is_closed: bool = Field(False, description="Whether the place is closed this day")

class PlaceBase(BaseModel):
    """Base place schema"""
    name: str = Field(..., max_length=200, description="Название заведения")
    description: Optional[str] = Field(None, description="Описание заведения")
    address: str = Field(..., max_length=500, description="Адрес заведения")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Широта")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Долгота")
    phone: Optional[str] = Field(None, max_length=50, description="Контактный телефон")
    email: Optional[str] = Field(None, max_length=100, description="Email для связи")
    website: Optional[HttpUrl] = Field(None, description="Сайт заведения")
    working_hours: Optional[Dict[WeekDay, WorkingHours]] = Field(
        None,
        description="График работы по дням недели"
    )
    category_ids: List[int] = Field(
        default_factory=list,
        description="Список ID категорий, к которым относится заведение"
    )

    @validator('working_hours', pre=True)
    def validate_working_hours(cls, v):
        if v is None:
            return None
            
        if not isinstance(v, dict):
            raise ValueError("Working hours must be a dictionary")
            
        # Check that all keys are valid week days
        valid_days = {day.value for day in WeekDay}
        for day in v.keys():
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}. Must be one of {valid_days}")
                
        return v

class PlaceCreate(PlaceBase):
    """Schema for creating a place"""
    pass

class PlaceUpdate(BaseModel):
    """Schema for updating a place"""
    name: Optional[str] = Field(None, max_length=200, description="Название заведения")
    description: Optional[str] = Field(None, description="Описание заведения")
    address: Optional[str] = Field(None, max_length=500, description="Адрес заведения")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Широта")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Долгота")
    phone: Optional[str] = Field(None, max_length=50, description="Контактный телефон")
    email: Optional[str] = Field(None, max_length=100, description="Email для связи")
    website: Optional[HttpUrl] = Field(None, description="Сайт заведения")
    working_hours: Optional[Dict[WeekDay, WorkingHours]] = Field(
        None,
        description="График работы по дням недели"
    )
    category_ids: Optional[List[int]] = Field(
        None,
        description="Список ID категорий, к которым относится заведение"
    )
    is_active: Optional[bool] = Field(None, description="Активно ли заведение")
    is_verified: Optional[bool] = Field(None, description="Подтверждено ли заведение")

class PlaceInDB(PlaceBase):
    """Place schema for database operations"""
    id: int
    rating: float = Field(0.0, ge=0, le=5, description="Рейтинг заведения (0-5)")
    reviews_count: int = Field(0, ge=0, description="Количество отзывов")
    is_active: bool = Field(True, description="Активно ли заведение")
    is_verified: bool = Field(False, description="Подтверждено ли заведение")
    owner_id: Optional[int] = Field(None, description="ID владельца заведения")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        from_attributes = True

class PlaceResponse(BaseModel):
    """Response schema for a single place"""
    success: bool = True
    data: PlaceInDB

class PlaceListResponse(BaseModel):
    """Response schema for a list of places"""
    success: bool = True
    data: list[PlaceInDB]
    total: int
    page: int
    size: int
    pages: int
