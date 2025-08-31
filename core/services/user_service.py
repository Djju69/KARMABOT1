"""
User service module for handling user-related operations.
Including balance management, level calculation, and transaction history.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import User, Transaction


async def get_user_balance(user_id: int) -> int:
    """
    Get current user balance.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        int: User's current balance in points
    """
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        return user.balance if user else 0


async def get_user_level(user_id: int) -> str:
    """
    Calculate user level based on their balance.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        str: User level (Bronze, Silver, Gold)
    """
    balance = await get_user_balance(user_id)
    if balance >= 1000:
        return "Gold"
    elif balance >= 500:
        return "Silver"
    return "Bronze"


async def get_user_history(user_id: int, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
    """
    Get paginated transaction history for a user.
    
    Args:
        user_id: Telegram user ID
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dict containing transactions and pagination info
    """
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return {"transactions": [], "total_pages": 0, "current_page": page}
            
        query = db.query(Transaction).filter(Transaction.user_id == user.id)
        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        
        transactions = (
            query.order_by(Transaction.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        
        return {
            "transactions": transactions,
            "total_pages": total_pages,
            "current_page": page,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }


async def spend_points(user_id: int, amount: int, description: str = "") -> bool:
    """
    Deduct points from user's balance.
    
    Args:
        user_id: Telegram user ID
        amount: Points to spend (positive number)
        description: Optional description of the transaction
        
    Returns:
        bool: True if successful, False if insufficient balance
    """
    if amount <= 0:
        return False
        
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).with_for_update().first()
        if not user or user.balance < amount:
            return False
            
        user.balance -= amount
        
        # Record the transaction
        transaction = Transaction(
            user_id=user.id,
            amount=-amount,
            description=description,
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        return True


async def add_points(user_id: int, amount: int, description: str = "") -> bool:
    """
    Add points to user's balance.
    
    Args:
        user_id: Telegram user ID
        amount: Points to add (positive number)
        description: Optional description of the transaction
        
    Returns:
        bool: True if successful
    """
    if amount <= 0:
        return False
        
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).with_for_update().first()
        if not user:
            return False
            
        user.balance += amount
        
        # Record the transaction
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            description=description,
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        return True


async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    lang_code: str = "ru"
) -> User:
    """
    Get existing user or create a new one.
    
    Args:
        telegram_id: Telegram user ID
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
        lang_code: Preferred language code
        
    Returns:
        User: The user object
    """
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                lang_code=lang_code,
                balance=0,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        return user
