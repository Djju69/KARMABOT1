import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional, Dict, List

from core.config import settings
from core.database import get_db
from core.schemas.auth import (
    Token, UserCreate, UserResponse, Message, UserUpdate, 
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest,
    UserInDB, TokenData
)
from core.services.auth_service import AuthService
from core.repositories.auth_repository import AuthRepository

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    try:
        user = await auth_service.register_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    user = await auth_service.authenticate_user(
        email=form_data.username,  # username is email in our case
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = await auth_service.create_tokens(user.id)
    
    # Get user agent for session tracking
    user_agent = request.headers.get("user-agent", "")
    
    # Create a session
    await auth_repo.create_user_session(
        user_id=user.id,
        session_id=secrets.token_urlsafe(32),
        user_agent=user_agent,
        ip_address=request.client.host if request.client else None
    )
    
    return tokens

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using a refresh token
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    return await auth_service.refresh_tokens(refresh_token)

@router.post("/password-reset-request", response_model=Message)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request a password reset
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    await auth_service.request_password_reset(request.email)
    
    return {"message": "If an account with that email exists, a password reset link has been sent"}

@router.post("/password-reset-confirm", response_model=Message)
async def reset_password_confirm(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password using a token
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    try:
        await auth_service.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        return {"message": "Password has been reset successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not reset password"
        )

@router.post("/verify-email", response_model=Message)
async def verify_email(
    verification: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify user's email using a token
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    try:
        payload = jwt.decode(
            verification.token,
            settings.auth.secret_key,
            algorithms=[settings.auth.algorithm]
        )
        
        token_type = payload.get("type")
        user_id = int(payload.get("sub"))
        
        if token_type != "verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
            
        # Get user and update verification status
        user = await auth_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        if user.is_verified:
            return {"message": "Email is already verified"}
            
        # Update user verification status
        user.is_verified = True
        user.status = "active"
        await db.commit()
        
        return {"message": "Email verified successfully"}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserInDB = Depends(AuthService.get_current_user)
) -> Any:
    """
    Get current user information
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update current user information
    """
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    
    try:
        updated_user = await auth_repo.update_user(current_user.id, user_update)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/me", response_model=Message)
async def delete_user_me(
    current_user: UserInDB = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete current user account
    """
    auth_repo = AuthRepository(db)
    
    # In a real app, you might want to soft delete or anonymize the user data
    # instead of hard deleting it
    deleted = await auth_repo.delete_user(current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User account deleted successfully"}
