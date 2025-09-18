from pydantic import BaseModel, Field, validator, conint
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    """Base review schema"""
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5 звезд")
    comment: Optional[str] = Field(None, max_length=2000, description="Текст отзыва")

class ReviewCreate(ReviewBase):
    """Schema for creating a review"""
    place_id: int = Field(..., description="ID заведения, к которому относится отзыв")

class ReviewUpdate(BaseModel):
    """Schema for updating a review"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Оценка от 1 до 5 звезд")
    comment: Optional[str] = Field(None, max_length=2000, description="Текст отзыва")

class ReviewInDB(ReviewBase):
    """Review schema for database operations"""
    id: int
    place_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        from_attributes = True

class ReviewResponse(BaseModel):
    """Response schema for a single review"""
    success: bool = True
    data: ReviewInDB

class ReviewListResponse(BaseModel):
    """Response schema for a list of reviews"""
    success: bool = True
    data: list[ReviewInDB]
    total: int
    page: int
    size: int
    pages: int

class ReviewWithUser(ReviewInDB):
    """Review schema with user information"""
    user_name: str = Field(..., description="Имя пользователя, оставившего отзыв")
    user_avatar: Optional[str] = Field(None, description="Аватар пользователя")

class ReviewStats(BaseModel):
    """Review statistics for a place"""
    average_rating: float = Field(..., ge=0, le=5, description="Средний рейтинг")
    total_reviews: int = Field(..., ge=0, description="Общее количество отзывов")
    rating_distribution: dict[int, int] = Field(
        ...,
        description="Распределение оценок (ключ - оценка, значение - количество)"
    )

class ReviewStatsResponse(BaseModel):
    """Response schema for review statistics"""
    success: bool = True
    data: ReviewStats
