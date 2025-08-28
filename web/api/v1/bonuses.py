"""
API endpoints for managing partner bonuses.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session

from web import models
from web.database import get_db
from web.routes_cabinet import get_current_claims

router = APIRouter(
    prefix="/bonuses",
    tags=["bonuses"],
    responses={404: {"description": "Not found"}},
)

# --- Models ---
class BonusBase(BaseModel):
    """Base model for bonus."""
    title: str
    description: Optional[str] = None
    points_required: int
    is_active: bool = True

class BonusCreate(BonusBase):
    """Model for creating a new bonus."""
    pass

class BonusUpdate(BaseModel):
    """Model for updating a bonus."""
    title: Optional[str] = None
    description: Optional[str] = None
    points_required: Optional[int] = None
    is_active: Optional[bool] = None

class BonusInDB(BonusBase):
    """Database model for bonus."""
    id: int
    partner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# --- Endpoints ---

@router.get("/", response_model=List[BonusInDB])
async def get_bonuses(
    is_active: Optional[bool] = None,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Get all bonuses for the current partner.
    """
    query = db.query(models.Bonus).filter(
        models.Bonus.partner_id == claims.get("partner_id")
    )
    
    if is_active is not None:
        query = query.filter(models.Bonus.is_active == is_active)
        
    return query.order_by(models.Bonus.points_required).all()

@router.post("/", response_model=BonusInDB, status_code=status.HTTP_201_CREATED)
async def create_bonus(
    bonus: BonusCreate,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Create a new bonus for the current partner.
    """
    db_bonus = models.Bonus(
        **bonus.dict(),
        partner_id=claims.get("partner_id")
    )
    
    db.add(db_bonus)
    db.commit()
    db.refresh(db_bonus)
    
    return db_bonus

@router.get("/{bonus_id}", response_model=BonusInDB)
async def get_bonus(
    bonus_id: int = Path(..., ge=1, description="The ID of the bonus to retrieve"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Get a specific bonus by ID.
    """
    bonus = db.query(models.Bonus).filter(
        models.Bonus.id == bonus_id,
        models.Bonus.partner_id == claims.get("partner_id")
    ).first()
    
    if not bonus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bonus not found"
        )
        
    return bonus

@router.put("/{bonus_id}", response_model=BonusInDB)
async def update_bonus(
    bonus_id: int = Path(..., ge=1, description="The ID of the bonus to update"),
    bonus_update: BonusUpdate = None,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Update a bonus.
    """
    if bonus_update is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    # Get existing bonus
    db_bonus = db.query(models.Bonus).filter(
        models.Bonus.id == bonus_id,
        models.Bonus.partner_id == claims.get("partner_id")
    ).first()
    
    if not db_bonus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bonus not found"
        )
    
    # Update fields
    update_data = bonus_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bonus, field, value)
    
    db.add(db_bonus)
    db.commit()
    db.refresh(db_bonus)
    
    return db_bonus

@router.delete("/{bonus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bonus(
    bonus_id: int = Path(..., ge=1, description="The ID of the bonus to delete"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Delete a bonus.
    """
    bonus = db.query(models.Bonus).filter(
        models.Bonus.id == bonus_id,
        models.Bonus.partner_id == claims.get("partner_id")
    ).first()
    
    if not bonus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bonus not found"
        )
    
    db.delete(bonus)
    db.commit()
    
    return None
