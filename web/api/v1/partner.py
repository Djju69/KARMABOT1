"""
Partner API endpoints for KarmaBot web application.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from web.database import get_db
from web.routes_cabinet import (
    get_current_claims,
    CardCreate,
    CardUpdate,
    Card as CardModel,
    CardsResponse,
    CardImage,
    DeleteRequestCreate
)

router = APIRouter()

# --- Partner Cards ---

@router.get("/cards/", response_model=CardsResponse)
async def get_partner_cards(
    status: Optional[str] = None,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    after_id: Optional[int] = None,
    limit: int = 20,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Get all cards for the current partner.
    """
    from web.routes_cabinet import partner_cards
    
    try:
        response = await partner_cards(
            status=status,
            q=q,
            category_id=category_id,
            after_id=after_id,
            limit=limit,
            claims=claims
        )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/cards/", response_model=CardModel, status_code=status.HTTP_201_CREATED)
async def create_partner_card(
    card: CardCreate,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Create a new card for the current partner.
    """
    from web.routes_cabinet import partner_cards_create
    
    try:
        response = await partner_cards_create(payload=card, claims=claims)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/cards/{card_id}", response_model=CardModel)
async def get_partner_card(
    card_id: int = Path(..., ge=1, description="The ID of the card to retrieve"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Get a specific card by ID.
    """
    from web.routes_cabinet import partner_cards
    
    try:
        # Get all cards and filter by ID
        response = await partner_cards(claims=claims)
        for card in response.items:
            if card.id == card_id:
                return card
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/cards/{card_id}", response_model=CardModel)
async def update_partner_card(
    card_id: int = Path(..., ge=1, description="The ID of the card to update"),
    card_update: CardUpdate = None,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Update a card.
    """
    from web.routes_cabinet import partner_cards_update
    
    try:
        if card_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
            
        response = await partner_cards_update(
            payload=card_update,
            card_id=card_id,
            claims=claims
        )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partner_card(
    card_id: int = Path(..., ge=1, description="The ID of the card to delete"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Delete a card (soft delete).
    """
    from web.routes_cabinet import partner_cards_hide
    
    try:
        await partner_cards_hide(card_id=card_id, claims=claims)
        return None
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# --- Card Images ---

@router.get("/cards/{card_id}/images", response_model=List[CardImage])
async def get_card_images(
    card_id: int = Path(..., ge=1, description="The ID of the card"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Get all images for a card.
    """
    from web.routes_cabinet import partner_card_images
    
    try:
        response = await partner_card_images(card_id=card_id, claims=claims)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/cards/{card_id}/images", response_model=List[CardImage])
async def upload_card_images(
    card_id: int = Path(..., ge=1, description="The ID of the card"),
    files: List[UploadFile] = File(..., description="Images to upload"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Upload images for a card.
    """
    from web.routes_cabinet import partner_card_images_upload
    
    try:
        response = await partner_card_images_upload(
            card_id=card_id,
            files=files,
            claims=claims
        )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/cards/{card_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card_image(
    card_id: int = Path(..., ge=1, description="The ID of the card"),
    image_id: int = Path(..., ge=1, description="The ID of the image to delete"),
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Delete an image from a card.
    """
    from web.routes_cabinet import partner_card_image_delete
    
    try:
        await partner_card_image_delete(
            card_id=card_id,
            image_id=image_id,
            claims=claims
        )
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# --- Card Delete Requests ---

@router.post("/cards/{card_id}/delete-request", status_code=status.HTTP_202_ACCEPTED)
async def request_card_deletion(
    card_id: int = Path(..., ge=1, description="The ID of the card to delete"),
    payload: DeleteRequestCreate = None,
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db)
):
    """
    Request deletion of a card.
    """
    from web.routes_cabinet import partner_card_delete_request
    
    try:
        response = await partner_card_delete_request(
            card_id=card_id,
            payload=payload,
            claims=claims
        )
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
