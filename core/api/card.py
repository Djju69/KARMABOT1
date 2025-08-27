"""
API для работы со скидками по картам лояльности.
"""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.services import card_service, antifraud_service
from core.utils.telemetry import log_event
from core.utils.i18n import gettext as _

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/card", tags=["card"])

# Константы для антифрод-проверок
MAX_ATTEMPTS_PER_HOUR = 10  # Максимальное количество попыток верификации в час
BLOCK_DURATION = 3600  # 1 час в секундах

class CardRedeemRequest(BaseModel):
    """Модель запроса на погашение скидки по карте."""
    card_number: str = Field(..., min_length=8, max_length=50, description="Номер карты")
    pin: str = Field(..., min_length=4, max_length=6, description="PIN-код карты")
    listing_id: Optional[int] = Field(None, gt=0, description="ID предложения (опционально)")
    points: Optional[int] = Field(None, ge=1, description="Количество баллов для списания (опционально)")
    bill_amount: int = Field(..., gt=0, description="Сумма чека в копейках")
    partner_id: int = Field(..., gt=0, description="ID партнера")
    
    @validator('card_number')
    def validate_card_number(cls, v):
        """Валидация номера карты."""
        if not v.isdigit():
            raise ValueError("Номер карты должен содержать только цифры")
        return v.strip()
    
    @validator('pin')
    def validate_pin(cls, v):
        """Валидация PIN-кода."""
        if not v.isdigit():
            raise ValueError("PIN-код должен содержать только цифры")
        return v

@router.post("/verify", response_model=Dict[str, Any])
async def verify_card(
    request: Request,
    card_data: dict,
    x_forwarded_for: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Верификация карты по номеру и PIN-коду.
    
    Args:
        card_data: {
            "card_number": str,  # Номер карты
            "pin": str,          # PIN-код
            "partner_id": int    # ID партнера
        }
        
    Returns:
        {
            "status": "success"|"error",
            "user": {
                "id": int,
                "first_name": str,
                "last_name": str,
                "phone": str,
                "email": str
            },
            "loyalty": {
                "points_balance": int,
                "points_lifetime": int
            },
            "error"?: {
                "code": str,
                "message": str,
                "retry_after"?: int
            }
        }
    """
    try:
        # Получаем IP-адрес из заголовков
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.client.host
        )
        
        # Валидируем входные данные
        try:
            card_number = str(card_data.get('card_number', '')).strip()
            pin = str(card_data.get('pin', '')).strip()
            partner_id = int(card_data.get('partner_id', 0))
            
            if not card_number or not pin or not partner_id:
                raise ValueError("Неверные данные карты")
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid card verification data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_data", "message": "Неверный формат данных"}
            )
        
        # Проверяем карту
        try:
            result = await card_service.verify_card(
                card_number=card_number,
                pin=pin,
                partner_id=partner_id,
                ip_address=ip_address
            )
            
            return {
                "status": "success",
                "user": result.get("user", {}),
                "loyalty": result.get("loyalty", {})
            }
            
        except HTTPException as e:
            # Пробрасываем HTTP-исключения как есть
            raise
            
        except Exception as e:
            logger.error(f"Error verifying card: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error", "message": "Ошибка при верификации карты"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify_card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": "Внутренняя ошибка сервера"}
        )

@router.post("/redeem/points", response_model=Dict[str, Any])
async def redeem_points(
    request: Request,
    redeem_data: dict,
    x_forwarded_for: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Списание баллов с карты лояльности.
    
    Args:
        redeem_data: {
            "card_number": str,  # Номер карты
            "pin": str,          # PIN-код
            "points": int,       # Количество баллов для списания
            "partner_id": int,   # ID партнера
            "bill_amount": int   # Сумма чека в копейках
        }
        
    Returns:
        {
            "status": "success"|"error",
            "transaction_id": int,
            "points_redeemed": int,
            "new_balance": int,
            "error"?: {
                "code": str,
                "message": str,
                "retry_after"?: int
            }
        }
    """
    try:
        # Получаем IP-адрес из заголовков
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.client.host
        )
        
        # Валидируем входные данные
        try:
            card_number = str(redeem_data.get('card_number', '')).strip()
            pin = str(redeem_data.get('pin', '')).strip()
            points = int(redeem_data.get('points', 0))
            partner_id = int(redeem_data.get('partner_id', 0))
            bill_amount = int(redeem_data.get('bill_amount', 0))
            
            if not all([card_number, pin, points > 0, partner_id > 0, bill_amount > 0]):
                raise ValueError("Неверные данные для списания баллов")
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid points redemption data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_data", "message": "Неверный формат данных"}
            )
        
        # Проверяем карту и списываем баллы
        try:
            result = await card_service.redeem_points(
                card_number=card_number,
                points=points,
                partner_id=partner_id,
                ip_address=ip_address
            )
            
            # Логируем успешное списание
            await log_event(
                actor_id=partner_id,
                entity_type="points_redemption",
                entity_id=f"card_{card_number[-4:]}",
                action="success",
                details={
                    "points_redeemed": points,
                    "bill_amount": bill_amount,
                    "new_balance": result.get("new_balance", 0)
                }
            )
            
            return {
                "status": "success",
                "transaction_id": result.get("transaction_id"),
                "points_redeemed": result.get("points_redeemed", 0),
                "new_balance": result.get("new_balance", 0)
            }
            
        except HTTPException as e:
            # Логируем ошибку
            await log_event(
                actor_id=partner_id,
                entity_type="points_redemption",
                entity_id=f"card_{card_number[-4:]}",
                action="failed",
                details={
                    "error": e.detail.get("code", "unknown"),
                    "message": e.detail.get("message", str(e))
                }
            )
            raise
            
        except Exception as e:
            logger.error(f"Error redeeming points: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error", "message": "Ошибка при списании баллов"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in redeem_points: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": "Внутренняя ошибка сервера"}
        )

@router.post("/redeem/discount", response_model=Dict[str, Any])
async def redeem_discount(
    request: Request,
    redeem_data: dict,
    x_forwarded_for: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Погашение скидки по карте лояльности.
    
    Args:
        redeem_data: {
            "card_number": str,  # Номер карты
            "pin": str,          # PIN-код
            "listing_id": int,   # ID предложения
            "partner_id": int,   # ID партнера
            "bill_amount": int   # Сумма чека в копейках
        }
        
    Returns:
        {
            "status": "success"|"error",
            "discount_amount": int,  # Сумма скидки в копейках
            "final_amount": int,     # Итоговая сумма к оплате в копейках
            "listing_title": str,    # Название предложения
            "error"?: {
                "code": str,
                "message": str,
                "retry_after"?: int
            }
        }
    """
    try:
        # Получаем IP-адрес из заголовков
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.client.host
        )
        
        # Валидируем входные данные
        try:
            card_number = str(redeem_data.get('card_number', '')).strip()
            pin = str(redeem_data.get('pin', '')).strip()
            listing_id = int(redeem_data.get('listing_id', 0))
            partner_id = int(redeem_data.get('partner_id', 0))
            bill_amount = int(redeem_data.get('bill_amount', 0))
            
            if not all([card_number, pin, listing_id > 0, partner_id > 0, bill_amount > 0]):
                raise ValueError("Неверные данные для погашения скидки")
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid discount redemption data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_data", "message": "Неверный формат данных"}
            )
        
        try:
            # Сначала проверяем карту
            card_info = await card_service.verify_card(
                card_number=card_number,
                pin=pin,
                partner_id=partner_id,
                ip_address=ip_address
            )
            
            # Получаем информацию о предложении
            listing = await _get_listing(db, listing_id)
            if not listing or listing.get('moderation_status') != 'approved' or listing.get('is_hidden'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "invalid_listing", "message": "Недействительное предложение"}
                )
            
            # Рассчитываем скидку
            discount_amount = _calculate_discount(listing['offer_details'], bill_amount)
            final_amount = max(0, bill_amount - discount_amount)
            
            # Создаем запись о погашении
            receipt_data = {
                'listing_id': listing_id,
                'partner_profile_id': partner_id,
                'user_id': card_info['user']['id'],
                'bill_amount': bill_amount,
                'discount_rule': listing['offer_details'],
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'redemption_method': 'card'
            }
            
            # Сохраняем в базу
            result = await db.execute(
                """
                INSERT INTO redeem_receipts (
                    listing_id, partner_profile_id, user_id,
                    bill_amount, discount_rule, discount_amount,
                    final_amount, redemption_method, created_at
                ) VALUES (
                    :listing_id, :partner_profile_id, :user_id,
                    :bill_amount, :discount_rule, :discount_amount,
                    :final_amount, :redemption_method, NOW()
                )
                RETURNING id
                """,
                receipt_data
            )
            
            receipt_id = result.scalar()
            
            # Логируем успешное погашение
            await log_event(
                actor_id=partner_id,
                entity_type="discount_redemption",
                entity_id=f"receipt_{receipt_id}",
                action="success",
                details={
                    "card_number": f"****{card_number[-4:]}",
                    "listing_id": listing_id,
                    "discount_amount": discount_amount,
                    "bill_amount": bill_amount,
                    "final_amount": final_amount
                }
            )
            
            return {
                "status": "success",
                "discount_amount": discount_amount,
                "final_amount": final_amount,
                "listing_title": listing.get('title', 'Скидка')
            }
            
        except HTTPException as e:
            # Логируем ошибку
            await log_event(
                actor_id=partner_id,
                entity_type="discount_redemption",
                entity_id=f"card_{card_number[-4:]}",
                action="failed",
                details={
                    "error": e.detail.get("code", "unknown"),
                    "message": e.detail.get("message", str(e)),
                    "listing_id": listing_id
                }
            )
            raise
            
        except Exception as e:
            logger.error(f"Error redeeming discount: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error", "message": "Ошибка при погашении скидки"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in redeem_discount: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": "Внутренняя ошибка сервера"}
        )

async def _get_user_id_from_card(card_number: str, pin: str) -> Optional[int]:
    """Получает ID пользователя по номеру карты и PIN-коду."""
    # В реальном приложении здесь должна быть проверка хеша PIN-кода
    result = await get_db_session().execute(
        """
        SELECT user_id 
        FROM user_cards 
        WHERE card_uid = :card_number 
        AND status = 'active'
        """,
        {'card_number': card_number}
    )
    
    row = result.fetchone()
    return row[0] if row else None

async def _is_card_blocked(card_number: str) -> bool:
    """Проверяет, заблокирована ли карта."""
    result = await get_db_session().execute(
        """
        SELECT 1 
        FROM user_cards 
        WHERE card_uid = :card_number 
        AND status = 'blocked'
        """,
        {'card_number': card_number}
    )
    return result.rowcount > 0

async def _is_daily_limit_reached(user_id: int, listing_id: int) -> bool:
    """Проверяет, достигнут ли дневной лимит погашений."""
    # В реальном приложении здесь должна быть проверка лимитов
    # Например, не более 5 погашений в день на одного пользователя
    result = await get_db_session().execute(
        """
        SELECT COUNT(*) 
        FROM redeem_receipts 
        WHERE user_id = :user_id 
        AND listing_id = :listing_id
        AND created_at >= CURRENT_DATE
        """,
        {'user_id': user_id, 'listing_id': listing_id}
    )
    
    count = result.scalar() or 0
    return count >= 5  # Максимум 5 погашений в день

async def _get_listing(db: AsyncSession, listing_id: int) -> Optional[dict]:
    """Получает информацию о предложении."""
    result = await db.execute(
        """
        SELECT id, title, moderation_status, is_hidden, offer_details
        FROM listings
        WHERE id = :listing_id
        """,
        {'listing_id': listing_id}
    )
    return result.fetchone()._asdict() if result.rowcount > 0 else None

def _calculate_discount(offer_details: dict, bill_amount: int) -> int:
    """Рассчитывает размер скидки на основе правил предложения."""
    if not offer_details or 'type' not in offer_details:
        return 0
        
    discount_type = offer_details['type']
    value = offer_details.get('value', 0)
    
    if discount_type == 'fixed':
        return min(value * 100, bill_amount)  # value в рублях, переводим в копейки
    elif discount_type == 'percent':
        return int(bill_amount * (value / 100))
    return 0

async def _update_card_last_used(card_number: str) -> None:
    """Обновляет время последнего использования карты."""
    await get_db_session().execute(
        """
        UPDATE user_cards
        SET last_used_at = NOW()
        WHERE card_uid = :card_number
        """,
        {'card_number': card_number}
    )
