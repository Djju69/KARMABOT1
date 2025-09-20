"""
User routes for personal cabinet and user management
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from core.database import get_db
from core.security.deps import get_current_user
from core.security.roles import Role
from core.logger import get_logger
from core.services.profile import profile_service
from core.services.loyalty_service import loyalty_service
from core.services.referral_service import referral_service
from core.models.loyalty_models import LoyaltyTransaction, LoyaltyBalance, ActivityType

logger = get_logger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/profile")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение профиля пользователя с полной информацией.
    
    Returns:
        Полная информация о пользователе включая статистику
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Получаем базовую информацию о пользователе
        profile_data = await profile_service.get_user_profile(user_id)
        
        # Получаем статистику лояльности
        loyalty_stats = await loyalty_service.get_user_stats(user_id)
        
        # Получаем статистику рефералов
        referral_stats = await referral_service.get_referral_stats(user_id)
        
        # Получаем последние активности
        recent_activities = await loyalty_service.get_user_activities(
            user_id=user_id,
            limit=5
        )
        
        return {
            "status": "success",
            "data": {
                "profile": profile_data,
                "loyalty": loyalty_stats,
                "referrals": referral_stats,
                "recent_activities": recent_activities,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении профиля пользователя"
        )

@router.get("/loyalty/balance")
async def get_loyalty_balance(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение баланса лояльности пользователя.
    
    Returns:
        Информация о балансе и доступных баллах
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        balance = await loyalty_service.get_user_balance(user_id)
        
        return {
            "status": "success",
            "data": {
                "balance": balance,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting loyalty balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении баланса лояльности"
        )

@router.get("/loyalty/transactions")
async def get_loyalty_transactions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    transaction_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории транзакций лояльности.
    
    Args:
        limit: Количество записей для возврата
        offset: Смещение для пагинации
        transaction_type: Фильтр по типу транзакции
        
    Returns:
        Список транзакций с пагинацией
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        transactions = await loyalty_service.get_user_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset,
            transaction_type=transaction_type
        )
        
        total_count = await loyalty_service.get_user_transactions_count(
            user_id=user_id,
            transaction_type=transaction_type
        )
        
        return {
            "status": "success",
            "data": {
                "transactions": transactions,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting loyalty transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении истории транзакций"
        )

@router.get("/referrals")
async def get_user_referrals(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о рефералах пользователя.
    
    Returns:
        Статистика рефералов и реферальное дерево
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Получаем статистику рефералов
        referral_stats = await referral_service.get_referral_stats(user_id)
        
        # Получаем дерево рефералов
        referral_tree = await referral_service.get_referral_tree(user_id, max_depth=3)
        
        # Получаем доходы от рефералов
        referral_earnings = await referral_service.get_referral_earnings(user_id, days=30)
        
        return {
            "status": "success",
            "data": {
                "stats": referral_stats,
                "tree": referral_tree,
                "earnings": referral_earnings,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user referrals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении информации о рефералах"
        )

@router.post("/referrals/create-code")
async def create_referral_code(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание реферального кода для пользователя.
    
    Returns:
        Созданный реферальный код
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        referral_code = await referral_service.create_referral_code(user_id)
        
        return {
            "status": "success",
            "data": {
                "referral_code": referral_code,
                "referral_link": f"https://t.me/your_bot?start=ref{referral_code}",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating referral code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании реферального кода"
        )

@router.get("/activities")
async def get_user_activities(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    activity_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение активности пользователя.
    
    Args:
        limit: Количество записей для возврата
        offset: Смещение для пагинации
        activity_type: Фильтр по типу активности
        
    Returns:
        Список активностей пользователя
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        activities = await loyalty_service.get_user_activities(
            user_id=user_id,
            limit=limit,
            offset=offset,
            activity_type=activity_type
        )
        
        total_count = await loyalty_service.get_user_activities_count(
            user_id=user_id,
            activity_type=activity_type
        )
        
        return {
            "status": "success",
            "data": {
                "activities": activities,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении активности пользователя"
        )

@router.post("/activities/claim")
async def claim_activity(
    activity_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Выполнение активности для получения баллов.
    
    Args:
        activity_type: Тип активности для выполнения
        
    Returns:
        Результат выполнения активности
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Проверяем, что тип активности существует
        if activity_type not in [e.value for e in ActivityType]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid activity type: {activity_type}"
            )
        
        # Выполняем активность
        result = await loyalty_service.perform_activity(
            user_id=user_id,
            activity_type=ActivityType(activity_type)
        )
        
        return {
            "status": "success",
            "data": {
                "activity_type": activity_type,
                "points_awarded": result.get("points_awarded", 0),
                "message": result.get("message", "Активность выполнена успешно"),
                "performed_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error claiming activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выполнении активности"
        )

@router.get("/settings")
async def get_user_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение настроек пользователя.
    
    Returns:
        Настройки пользователя
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        settings = await profile_service.get_user_settings(user_id)
        
        return {
            "status": "success",
            "data": {
                "settings": settings,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении настроек пользователя"
        )

@router.put("/settings")
async def update_user_settings(
    settings_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление настроек пользователя.
    
    Args:
        settings_data: Новые настройки пользователя
        
    Returns:
        Обновленные настройки
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        updated_settings = await profile_service.update_user_settings(
            user_id=user_id,
            settings=settings_data
        )
        
        return {
            "status": "success",
            "data": {
                "settings": updated_settings,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении настроек пользователя"
        )

@router.get("/notifications")
async def get_user_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение уведомлений пользователя.
    
    Args:
        limit: Количество записей для возврата
        offset: Смещение для пагинации
        unread_only: Показывать только непрочитанные
        
    Returns:
        Список уведомлений пользователя
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        notifications = await profile_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        total_count = await profile_service.get_user_notifications_count(
            user_id=user_id,
            unread_only=unread_only
        )
        
        return {
            "status": "success",
            "data": {
                "notifications": notifications,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении уведомлений"
        )

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Отметка уведомления как прочитанного.
    
    Args:
        notification_id: ID уведомления
        
    Returns:
        Результат операции
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        success = await profile_service.mark_notification_read(
            user_id=user_id,
            notification_id=notification_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Уведомление не найдено или не принадлежит пользователю"
            )
        
        return {
            "status": "success",
            "data": {
                "notification_id": notification_id,
                "marked_read_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отметке уведомления как прочитанного"
        )
