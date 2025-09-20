from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., max_length=100, description="Название категории")
    slug: str = Field(..., max_length=100, regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', 
                     description="URL-совместимый идентификатор категории (латиница, цифры, дефисы)")
    description: Optional[str] = Field(None, max_length=500, description="Описание категории")
    is_active: bool = Field(True, description="Активна ли категория")

class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass

class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, max_length=100, description="Название категории")
    slug: Optional[str] = Field(None, max_length=100, regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
                              description="URL-совместимый идентификатор категории")
    description: Optional[str] = Field(None, max_length=500, description="Описание категории")
    is_active: Optional[bool] = Field(None, description="Активна ли категория")

class CategoryInDB(CategoryBase):
    """Category schema for database operations"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        from_attributes = True

class CategoryResponse(BaseModel):
    """Response schema for a single category"""
    success: bool = True
    data: CategoryInDB

class CategoryListResponse(BaseModel):
    """Response schema for a list of categories"""
    success: bool = True
    data: list[CategoryInDB]
    total: int
    page: int
    size: int
    pages: int
