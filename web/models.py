"""
Data models for KarmaBot web application.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class CardStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class CardBase(BaseModel):
    """Base model for partner card."""
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=1000)
    category_id: int
    partner_id: int
    is_active: bool = True
    status: CardStatus = CardStatus.DRAFT
    
class CardCreate(CardBase):
    """Model for creating a new card."""
    pass

class CardUpdate(BaseModel):
    """Model for updating a card."""
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[CardStatus] = None

class CardInDB(CardBase):
    """Database model for card."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class CardPublic(CardInDB):
    """Public model for card (API response)."""
    image_url: Optional[HttpUrl] = None
    
class CardListResponse(BaseModel):
    """Response model for list of cards."""
    items: List[CardPublic]
    total: int
    page: int
    size: int

class ImageUploadResponse(BaseModel):
    """Response model for image upload."""
    url: HttpUrl
    filename: str
    size: int
    content_type: str
