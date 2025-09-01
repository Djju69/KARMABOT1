from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from core.repositories.auth_repository import AuthRepository
from core.schemas.auth import Token, TokenData, UserCreate, UserInDB, UserUpdate
from core.config import settings
from core.security import get_password_hash, verify_password

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo
        self.oauth2_scheme = OAuth2PasswordBearer(
            tokenUrl=f"{settings.auth.api_v1_str}/auth/login"
        )

    # Authentication methods
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password"""
        user = await self.auth_repo.authenticate_user(email, password)
        if not user:
            return None
        
        # Update last login time
        user.last_login = datetime.now(timezone.utc)
        await self.auth_repo.db.commit()
        
        return UserInDB.from_orm(user)

    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(32)
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.auth.secret_key, 
            algorithm=settings.auth.algorithm
        )
        return encoded_jwt

    async def create_tokens(self, user_id: int) -> Token:
        """Create access and refresh tokens for a user"""
        # Create access token
        access_token_expires = timedelta(minutes=settings.auth.access_token_expire_minutes)
        access_token = await self.create_access_token(
            data={"sub": str(user_id), "type": "access"},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = await self.create_access_token(
            data={"sub": str(user_id), "type": "refresh"},
            expires_delta=timedelta(days=settings.auth.refresh_token_expire_days)
        )
        
        # Store refresh token in database
        await self.auth_repo.create_refresh_token(user_id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """Refresh access token using a refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.auth.secret_key,
                algorithms=[settings.auth.algorithm]
            )
            
            token_type = payload.get("type")
            user_id = int(payload.get("sub"))
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
                
            # Verify refresh token in database
            token_in_db = await self.auth_repo.get_refresh_token(refresh_token)
            if not token_in_db or token_in_db.is_revoked or token_in_db.is_expired:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
                
            # Create new tokens
            return await self.create_tokens(user_id)
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login"))) -> UserInDB:
        """Get the current authenticated user"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.auth.secret_key, 
                algorithms=[settings.auth.algorithm]
            )
            
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if user_id is None or token_type != "access":
                raise credentials_exception
                
            user = await self.auth_repo.get_user_by_id(int(user_id))
            if user is None:
                raise credentials_exception
                
            return UserInDB.from_orm(user)
            
        except JWTError:
            raise credentials_exception

    # User management
    async def register_user(self, user_data: UserCreate) -> UserInDB:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.auth_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if user_data.username:
            existing_username = await self.auth_repo.get_user_by_username(user_data.username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        db_user = await self.auth_repo.create_user(user_data)
        
        # Generate email verification token
        verification_token = await self.create_access_token(
            data={
                "sub": str(db_user.id),
                "type": "verification"
            },
            expires_delta=timedelta(hours=settings.auth.email_verification_token_expire_hours)
        )
        
        # TODO: Send verification email
        # await self._send_verification_email(db_user.email, verification_token)
        
        return UserInDB.from_orm(db_user)

    async def request_password_reset(self, email: str) -> None:
        """Request a password reset for a user"""
        user = await self.auth_repo.get_user_by_email(email)
        if not user:
            # Don't reveal that the user doesn't exist
            return
        
        # Generate password reset token
        reset_token = await self.create_access_token(
            data={
                "sub": str(user.id),
                "type": "password_reset"
            },
            expires_delta=timedelta(hours=settings.auth.email_reset_token_expire_hours)
        )
        
        # TODO: Send password reset email
        # await self._send_password_reset_email(user.email, reset_token)

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset a user's password using a token"""
        try:
            payload = jwt.decode(
                token,
                settings.auth.secret_key,
                algorithms=[settings.auth.algorithm]
            )
            
            token_type = payload.get("type")
            user_id = int(payload.get("sub"))
            
            if token_type != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
                
            # Update user's password
            await self.auth_repo.update_user(
                user_id,
                UserUpdate(password=new_password)
            )
            
            # Revoke all user's sessions
            await self.auth_repo.revoke_all_sessions(user_id)
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )

    # Helper methods
    async def _send_verification_email(self, email: str, token: str) -> None:
        """Send verification email (to be implemented)"""
        # TODO: Implement email sending
        verification_url = f"{settings.auth.frontend_url}/verify-email?token={token}"
        print(f"Verification URL for {email}: {verification_url}")

    async def _send_password_reset_email(self, email: str, token: str) -> None:
        """Send password reset email (to be implemented)"""
        # TODO: Implement email sending
        reset_url = f"{settings.auth.password_reset_url}?token={token}"
        print(f"Password reset URL for {email}: {reset_url}")
