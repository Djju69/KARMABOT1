from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar

# Generic Type for pagination
T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    """Success response schema"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
