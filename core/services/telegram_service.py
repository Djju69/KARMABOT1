"""
Сервис для работы с Telegram-интеграцией.
Обеспечивает привязку аккаунта Telegram к пользователю, аутентификацию через Telegram
и управление сессиями.
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models.telegram_models import TelegramUser, TelegramAuthToken
from core.schemas.auth import UserInDB
from core.security import create_access_token, create_refresh_token

class TelegramService:
    """Сервис для работы с Telegram-интеграцией"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_auth_token(self, user_id: int) -> str:
        """
        Генерирует токен для привязки аккаунта Telegram
        
        Args:
            user_id: ID пользователя, для которого генерируется токен
            
        Returns:
            str: Сгенерированный токен
        """
        # Генерируем случайный токен
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Создаем запись в базе данных
        auth_token = TelegramAuthToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=15)  # Токен действителен 15 минут
        )
        
        self.db.add(auth_token)
        await self.db.commit()
        await self.db.refresh(auth_token)
        
        return token
    
    async def verify_auth_token(self, token: str) -> Optional[int]:
        """
        Проверяет токен аутентификации Telegram
        
        Args:
            token: Токен для проверки
            
        Returns:
            Optional[int]: ID пользователя, если токен действителен, иначе None
        """
        # Ищем токен в базе данных
        result = await self.db.execute(
            """
            SELECT user_id 
            FROM telegram_auth_tokens 
            WHERE token = :token 
              AND is_used = FALSE 
              AND expires_at > NOW()
            """,
            {"token": token}
        )
        
        token_data = result.scalar_one_or_none()
        if not token_data:
            return None
            
        # Помечаем токен как использованный
        await self.db.execute(
            """
            UPDATE telegram_auth_tokens 
            SET is_used = TRUE 
            WHERE token = :token
            """,
            {"token": token}
        )
        await self.db.commit()
        
        return token_data
    
    async def link_telegram_account(
        self, 
        user_id: int, 
        telegram_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Привязывает аккаунт Telegram к пользователю
        
        Args:
            user_id: ID пользователя
            telegram_data: Данные из Telegram WebApp
            
        Returns:
            Tuple[bool, str]: (Успех, Сообщение об ошибке или успехе)
        """
        # Проверяем, что у пользователя еще нет привязанного аккаунта
        existing_link = await self.db.execute(
            "SELECT 1 FROM telegram_users WHERE user_id = :user_id",
            {"user_id": user_id}
        )
        
        if existing_link.scalar_one_or_none():
            return False, "Telegram аккаунт уже привязан к этому пользователю"
            
        # Проверяем, не привязан ли этот аккаунт Telegram к другому пользователю
        existing_telegram = await self.db.execute(
            "SELECT 1 FROM telegram_users WHERE telegram_id = :telegram_id",
            {"telegram_id": telegram_data["id"]}
        )
        
        if existing_telegram.scalar_one_or_none():
            return False, "Этот аккаунт Telegram уже привязан к другому пользователю"
        
        # Создаем привязку
        telegram_user = TelegramUser(
            user_id=user_id,
            telegram_id=telegram_data["id"],
            username=telegram_data.get("username"),
            first_name=telegram_data.get("first_name"),
            last_name=telegram_data.get("last_name"),
            is_bot=telegram_data.get("is_bot", False)
        )
        
        self.db.add(telegram_user)
        await self.db.commit()
        
        return True, "Аккаунт Telegram успешно привязан"
    
    async def authenticate_telegram(
        self, 
        telegram_id: int
    ) -> Optional[Tuple[UserInDB, str, str]]:
        """
        Аутентифицирует пользователя по ID Telegram
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[Tuple[UserInDB, str, str]]: (Пользователь, access_token, refresh_token) или None
        """
        # Ищем пользователя по telegram_id
        result = await self.db.execute(
            """
            SELECT u.* 
            FROM users_auth u
            JOIN telegram_users tu ON u.id = tu.user_id
            WHERE tu.telegram_id = :telegram_id
            AND u.is_active = TRUE
            """,
            {"telegram_id": telegram_id}
        )
        
        user_data = result.mappings().first()
        if not user_data:
            return None
        
        # Создаем токены доступа
        access_token = create_access_token(
            data={"sub": str(user_data["id"])},
            expires_delta=timedelta(minutes=settings.auth.access_token_expire_minutes)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user_data["id"])},
            expires_delta=timedelta(days=settings.auth.refresh_token_expire_days)
        )
        
        # Обновляем время последнего входа
        await self.db.execute(
            """
            UPDATE users_auth 
            SET last_login = NOW() 
            WHERE id = :user_id
            """,
            {"user_id": user_data["id"]}
        )
        await self.db.commit()
        
        # Создаем объект пользователя
        user = UserInDB(
            id=user_data["id"],
            email=user_data["email"],
            username=user_data["username"],
            full_name=user_data["full_name"],
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            role=user_data["role"]
        )
        
        return user, access_token, refresh_token
