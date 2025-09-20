from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.schemas import (
    CategoryCreate, CategoryInDB, CategoryUpdate,
    CategoryResponse, CategoryListResponse, SuccessResponse
)
from core.repositories.catalog_repository import CatalogRepository

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new category
    """
    repo = CatalogRepository(db)
    try:
        db_category = await repo.create_category(category)
        return CategoryResponse(data=db_category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a category by ID
    """
    repo = CatalogRepository(db)
    category = await repo.get_category(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return CategoryResponse(data=category)

@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all categories with pagination
    """
    repo = CatalogRepository(db)
    categories = await repo.list_categories(skip=skip, limit=limit, is_active=is_active)
    return CategoryListResponse(
        data=categories,
        total=len(categories),  # This should be replaced with actual count from DB
        page=skip // limit + 1,
        size=len(categories),
        pages=(len(categories) + limit - 1) // limit if limit > 0 else 1
    )

@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a category
    """
    repo = CatalogRepository(db)
    
    # Check if category exists
    existing_category = await repo.get_category(category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update category
    try:
        updated_category = await repo.update_category(category_id, category_update)
        return CategoryResponse(data=updated_category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{category_id}", response_model=SuccessResponse)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a category
    """
    repo = CatalogRepository(db)
    
    # Check if category exists
    existing_category = await repo.get_category(category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Delete category
    success = await repo.delete_category(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )
    
    return SuccessResponse(
        message="Category deleted successfully"
    )
