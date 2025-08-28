"""
Partner cabinet API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_active_user

router = APIRouter(
    prefix="/api/partner",
    tags=["partner"],
    responses={404: {"description": "Not found"}},
)

@router.get("/cards/", response_model=List[schemas.CardPublic])
async def get_partner_cards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Partner = Depends(get_current_active_user)
):
    """Get all cards for current partner."""
    cards = db.query(models.Card)\
        .filter(models.Card.partner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return cards

@router.post("/cards/", response_model=schemas.CardPublic, status_code=status.HTTP_201_CREATED)
async def create_partner_card(
    card: schemas.CardCreate,
    db: Session = Depends(get_db),
    current_user: models.Partner = Depends(get_current_active_user)
):
    """Create a new card for current partner."""
    db_card = models.Card(
        **card.dict(),
        partner_id=current_user.id,
        status=models.CardStatus.DRAFT
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@router.get("/cards/{card_id}", response_model=schemas.CardPublic)
async def get_partner_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: models.Partner = Depends(get_current_active_user)
):
    """Get a specific card by ID."""
    card = db.query(models.Card)\
        .filter(
            models.Card.id == card_id,
            models.Card.partner_id == current_user.id
        )\
        .first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card

@router.put("/cards/{card_id}", response_model=schemas.CardPublic)
async def update_partner_card(
    card_id: int,
    card_update: schemas.CardUpdate,
    db: Session = Depends(get_db),
    current_user: models.Partner = Depends(get_current_active_user)
):
    """Update a card."""
    db_card = db.query(models.Card)\
        .filter(
            models.Card.id == card_id,
            models.Card.partner_id == current_user.id
        )\
        .first()
    
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    update_data = card_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_card, field, value)
    
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partner_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: models.Partner = Depends(get_current_active_user)
):
    """Delete a card."""
    card = db.query(models.Card)\
        .filter(
            models.Card.id == card_id,
            models.Card.partner_id == current_user.id
        )\
        .first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    db.delete(card)
    db.commit()
    return None

@router.post("/cards/{card_id}/image", response_model=schemas.ImageUploadResponse)
async def upload_card_image(
    card_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Partner = Depends(get_current_active_user)
):
    """Upload an image for a card."""
    # Verify card exists and belongs to user
    card = db.query(models.Card)\
        .filter(
            models.Card.id == card_id,
            models.Card.partner_id == current_user.id
        )\
        .first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # TODO: Implement image upload to storage (e.g., S3, local filesystem)
    # This is a placeholder implementation
    file_content = await file.read()
    file_size = len(file_content)
    
    # In a real app, you would save the file to storage and get a URL
    image_url = f"https://example.com/uploads/{file.filename}"
    
    # Update card with image URL
    card.image_url = image_url
    db.add(card)
    db.commit()
    
    return {
        "url": image_url,
        "filename": file.filename,
        "size": file_size,
        "content_type": file.content_type
    }
