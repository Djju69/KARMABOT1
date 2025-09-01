from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"

class MediaBase(BaseModel):
    """Base media schema"""
    file_id: str = Field(..., description="Идентификатор файла в хранилище")
    file_type: str = Field(..., description="MIME-тип файла")
    url: HttpUrl = Field(..., description="URL для доступа к файлу")
    is_cover: bool = Field(False, description="Является ли обложкой")

class MediaCreate(MediaBase):
    """Schema for creating media"""
    place_id: int = Field(..., description="ID заведения, к которому привязан медиафайл")

class MediaInDB(MediaBase):
    """Media schema for database operations"""
    id: int
    place_id: int
    uploaded_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class MediaResponse(BaseModel):
    """Response schema for a single media file"""
    success: bool = True
    data: MediaInDB

class MediaListResponse(BaseModel):
    """Response schema for a list of media files"""
    success: bool = True
    data: List[MediaInDB]
    total: int
    page: int
    size: int
    pages: int

class MediaUpdate(BaseModel):
    """Schema for updating media"""
    is_cover: Optional[bool] = Field(None, description="Установить как обложку")

class MediaUploadResponse(BaseModel):
    """Response schema for successful media upload"""
    success: bool = True
    message: str = "Файл успешно загружен"
    data: MediaInDB
