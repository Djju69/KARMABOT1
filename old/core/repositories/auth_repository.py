from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from core.models.auth_models import User, RefreshToken, UserSession, UserRole, UserStatus
from core.schemas.auth import UserCreate, UserUpdate, UserInDB, TokenData
from core.security import get_password_hash, verify_password
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # User operations
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            role=UserRole.USER,
            status=UserStatus.ACTIVE if user_data.is_active else UserStatus.INACTIVE
        )
        
        self.db.add(db_user)
        try:
            await self.db.commit()
            await self.db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            await self.db.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                if "email" in str(e):
                    raise ValueError("Email already registered")
                elif "username" in str(e):
                    raise ValueError("Username already taken")
            raise

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user data"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
            
        update_data = user_data.dict(exclude_unset=True)
        
        # Handle password update
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        
        # Update user fields
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                if "email" in str(e):
                    raise ValueError("Email already registered")
                elif "username" in str(e):
                    raise ValueError("Username already taken")
            raise

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        result = await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()
        return result.rowcount > 0

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    # Token operations
    async def create_refresh_token(
        self, 
        user_id: int, 
        user_agent: Optional[str] = None, 
        ip_address: Optional[str] = None
    ) -> RefreshToken:
        """Create a new refresh token"""
        token = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.auth.refresh_token_expire_days)
        
        db_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.db.add(db_token)
        await self.db.commit()
        await self.db.refresh(db_token)
        return db_token

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get a refresh token by token string"""
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token == token)
            .where(RefreshToken.is_revoked.is_(False))
        )
        return result.scalars().first()

    async def revoke_refresh_token(self, token_id: int) -> bool:
        """Revoke a refresh token"""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(is_revoked=True)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke_all_refresh_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user"""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self.db.commit()
        return result.rowcount

    # Session management
    async def create_user_session(
        self, 
        user_id: int, 
        session_id: str, 
        user_agent: Optional[str] = None, 
        ip_address: Optional[str] = None,
        expires_in_days: int = 30
    ) -> UserSession:
        """Create a new user session"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            last_activity=datetime.now(timezone.utc)
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get a user session by session ID"""
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.session_id == session_id)
            .where(UserSession.is_active.is_(True))
        )
        return result.scalars().first()

    async def update_session_activity(self, session_id: str) -> bool:
        """Update the last activity timestamp for a session"""
        result = await self.db.execute(
            update(UserSession)
            .where(UserSession.session_id == session_id)
            .values(last_activity=datetime.now(timezone.utc))
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a user session"""
        result = await self.db.execute(
            update(UserSession)
            .where(UserSession.session_id == session_id)
            .values(is_active=False)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke_all_sessions(self, user_id: int, exclude_session_id: Optional[str] = None) -> int:
        """Revoke all sessions for a user"""
        query = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_active.is_(True))
        )
        
        if exclude_session_id:
            query = query.where(UserSession.session_id != exclude_session_id)
        
        result = await self.db.execute(query.values(is_active=False))
        await self.db.commit()
        return result.rowcount

    # Utility methods
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return []
        
        # In a real app, this would come from a database
        permissions = {
            UserRole.SUPER_ADMIN: ["*"],  # All permissions
            UserRole.ADMIN: [
                "users:read", "users:write", "users:delete",
                "places:read", "places:write", "places:delete",
                "categories:manage", "reviews:moderate"
            ],
            UserRole.MODERATOR: [
                "places:read", "places:moderate",
                "reviews:read", "reviews:moderate"
            ],
            UserRole.PARTNER: [
                "profile:read", "profile:update",
                "places:manage_own", "reviews:respond"
            ],
            UserRole.USER: [
                "profile:read", "profile:update",
                "places:read", "reviews:write"
            ]
        }
        
        return permissions.get(user.role, ["profile:read"])

    async def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if a user has a specific permission"""
        permissions = await self.get_user_permissions(user_id)
        return "*" in permissions or permission in permissions
