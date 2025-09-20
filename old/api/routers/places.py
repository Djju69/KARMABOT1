from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import json

from core.database import get_db
from core.schemas import (
    PlaceCreate, PlaceInDB, PlaceUpdate, PlaceResponse, 
    PlaceListResponse, MediaUploadResponse, SuccessResponse,
    ReviewCreate, ReviewResponse, ReviewListResponse, ReviewStatsResponse
)
from core.repositories.catalog_repository import CatalogRepository
from core.security import get_current_user

router = APIRouter(prefix="/api/v1/places", tags=["places"])

def parse_working_hours(working_hours_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse working hours from JSON string"""
    if not working_hours_str:
        return None
    try:
        return json.loads(working_hours_str)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid working_hours format. Must be a valid JSON string."
        )

@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_place(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    address: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    working_hours: Optional[str] = Form(None),
    category_ids: str = Form("[]"),  # JSON array of category IDs
    cover_image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new place
    """
    # Parse category IDs from JSON string
    try:
        category_ids_list = json.loads(category_ids)
        if not isinstance(category_ids_list, list):
            raise ValueError("category_ids must be a JSON array")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category_ids format. Must be a JSON array of integers."
        )
    
    # Parse working hours
    working_hours_dict = parse_working_hours(working_hours)
    
    # Create place data
    place_data = {
        "name": name,
        "description": description,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "phone": phone,
        "email": email,
        "website": website,
        "working_hours": working_hours_dict,
        "category_ids": category_ids_list
    }
    
    # Validate data using Pydantic model
    place_create = PlaceCreate(**place_data)
    
    # Create place in database
    repo = CatalogRepository(db)
    try:
        db_place = await repo.create_place(place_create, current_user["id"])
        
        # Handle cover image upload if provided
        if cover_image:
            # In a real app, you would upload the file to storage (S3, local storage, etc.)
            # and get back a URL and file ID
            file_id = f"file_{db_place.id}_cover"
            file_url = f"/media/places/{db_place.id}/cover.jpg"
            
            await repo.add_media(
                place_id=db_place.id,
                file_id=file_id,
                file_type=cover_image.content_type or "image/jpeg",
                url=file_url,
                uploaded_by=current_user["id"],
                is_cover=True
            )
            
            # Refresh place data to include the new media
            db_place = await repo.get_place(db_place.id)
        
        return PlaceResponse(data=db_place)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a place by ID
    """
    repo = CatalogRepository(db)
    place = await repo.get_place(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    return PlaceResponse(data=place)

@router.get("/", response_model=PlaceListResponse)
async def list_places(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all places with filtering and pagination
    """
    repo = CatalogRepository(db)
    places = await repo.list_places(
        skip=skip,
        limit=limit,
        category_id=category_id,
        search=search,
        is_verified=is_verified
    )
    
    # In a real app, you would get the total count from the database
    total = len(places)  # This should be replaced with actual count from DB
    
    return PlaceListResponse(
        data=places,
        total=total,
        page=skip // limit + 1,
        size=len(places),
        pages=(total + limit - 1) // limit if limit > 0 else 1
    )

@router.patch("/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: int,
    place_update: PlaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a place
    """
    repo = CatalogRepository(db)
    
    # Check if place exists and user has permission
    existing_place = await repo.get_place(place_id)
    if not existing_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    # Check if user is the owner or admin
    is_owner = existing_place.owner_id == current_user["id"]
    is_admin = current_user.get("role") in ["admin", "superadmin"]
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this place"
        )
    
    # Update place
    try:
        updated_place = await repo.update_place(
            place_id=place_id,
            place_data=place_update,
            owner_id=None if is_admin else current_user["id"]
        )
        return PlaceResponse(data=updated_place)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{place_id}", response_model=SuccessResponse)
async def delete_place(
    place_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a place
    """
    repo = CatalogRepository(db)
    
    # Check if place exists and user has permission
    existing_place = await repo.get_place(place_id)
    if not existing_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    # Check if user is the owner or admin
    is_owner = existing_place.owner_id == current_user["id"]
    is_admin = current_user.get("role") in ["admin", "superadmin"]
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this place"
        )
    
    # Delete place
    success = await repo.delete_place(
        place_id=place_id,
        owner_id=None if is_admin else current_user["id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete place"
        )
    
    return SuccessResponse(
        message="Place deleted successfully"
    )

@router.post("/{place_id}/media", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    place_id: int,
    file: UploadFile = File(...),
    is_cover: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload media for a place
    """
    repo = CatalogRepository(db)
    
    # Check if place exists and user has permission
    place = await repo.get_place(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    # Check if user is the owner or admin
    is_owner = place.owner_id == current_user["id"]
    is_admin = current_user.get("role") in ["admin", "superadmin"]
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to upload media for this place"
        )
    
    # In a real app, you would save the file to storage (S3, local storage, etc.)
    # and get back a URL and file ID
    file_id = f"file_{place_id}_{file.filename}"
    file_url = f"/media/places/{place_id}/{file.filename}"
    
    try:
        media = await repo.add_media(
            place_id=place_id,
            file_id=file_id,
            file_type=file.content_type or "application/octet-stream",
            url=file_url,
            uploaded_by=current_user["id"],
            is_cover=is_cover
        )
        
        return MediaUploadResponse(
            message="File uploaded successfully",
            data=media
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.post("/{place_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    place_id: int,
    review: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a review for a place
    """
    repo = CatalogRepository(db)
    
    # Check if place exists
    place = await repo.get_place(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    # Create review
    try:
        # In a real app, you would have a separate reviews repository
        # For now, we'll use the catalog repository
        db_review = await repo.create_review(
            place_id=place_id,
            user_id=current_user["id"],
            rating=review.rating,
            comment=review.comment
        )
        
        return ReviewResponse(data=db_review)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}"
        )

@router.get("/{place_id}/reviews", response_model=ReviewListResponse)
async def get_place_reviews(
    place_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reviews for a place
    """
    repo = CatalogRepository(db)
    
    # Check if place exists
    place = await repo.get_place(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    # In a real app, you would have a method to get paginated reviews
    # For now, we'll return all reviews
    reviews = place.reviews[skip:skip+limit]
    
    return ReviewListResponse(
        data=reviews,
        total=len(place.reviews),
        page=skip // limit + 1,
        size=len(reviews),
        pages=(len(place.reviews) + limit - 1) // limit if limit > 0 else 1
    )

@router.get("/{place_id}/stats", response_model=ReviewStatsResponse)
async def get_place_stats(
    place_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a place
    """
    repo = CatalogRepository(db)
    
    # Check if place exists
    place = await repo.get_place(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    # In a real app, you would calculate these statistics from the database
    # For now, we'll use placeholder values
    stats = {
        "average_rating": place.rating or 0,
        "total_reviews": place.reviews_count or 0,
        "rating_distribution": {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0
        }
    }
    
    # Calculate rating distribution from reviews
    for review in place.reviews:
        if 1 <= review.rating <= 5:
            stats["rating_distribution"][review.rating] += 1
    
    return ReviewStatsResponse(data=stats)
