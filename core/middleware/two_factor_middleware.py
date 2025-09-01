"""
Middleware для проверки двухфакторной аутентификации.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
import logging

from core.security.two_factor_auth import two_factor_auth
from core.security.roles import get_user_role, Role
from core.database import role_repository

logger = logging.getLogger(__name__)

class TwoFactorAuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки двухфакторной аутентификации.
    
    Проверяет, прошёл ли пользователь 2FA, если это требуется для его роли.
    """
    
    def __init__(self, storage: BaseStorage):
        super().__init__()
        self.storage = storage
        # Команды, которые разрешены без 2FA
        self.allowed_commands = {'start', 'help', 'cancel', 'auth'}
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Пропускаем служебные обновления
        if not (event.message or event.callback_query):
            return await handler(event, data)
            
        # Получаем объект сообщения или callback
        message = event.message or event.callback_query.message
        user_id = event.from_user.id
        
        # Получаем состояние пользователя
        state: FSMContext = data.get('state')
        
        # Проверяем, является ли это командой аутентификации
        if self._is_auth_command(event):
            return await handler(event, data)
        
        # Проверяем, требуется ли 2FA для пользователя
        if not await self._is_2fa_required(user_id):
            return await handler(event, data)
            
        # Проверяем, прошел ли пользователь 2FA
        state_data = await state.get_data()
        if state_data.get('2fa_verified', False):
            return await handler(event, data)
            
        # Если 2FA не пройдена, перенаправляем на аутентификацию
        logger.warning(f"User {user_id} tried to access protected resource without 2FA")
        
        # Логируем попытку доступа без 2FA
        await role_repository.log_audit_event(
            user_id=user_id,
            action="2FA_REQUIRED",
            entity_type="user",
            entity_id=user_id,
            ip_address=event.event.from_user.id if hasattr(event, 'event') else None
        )
        
        # Отправляем сообщение с просьбой пройти 2FA
        if hasattr(event, 'answer'):
            await event.answer("🔒 Требуется двухфакторная аутентификация. Пожалуйста, введите код из приложения аутентификатора.")
        elif hasattr(message, 'answer'):
            await message.answer("🔒 Требуется двухфакторная аутентификация. Пожалуйста, введите код из приложения аутентификатора.")
        
        return False
    
    async def verify_2fa_code(self, user_id: int, code: str) -> bool:
        """
        Проверяет код 2FA.
        
        Args:
            user_id: ID пользователя
            code: Код подтверждения
            
        Returns:
            bool: True если код верный, иначе False
        """
        try:
            # Проверяем код с помощью TwoFactorAuth
            return await two_factor_auth.verify_code(user_id, code)
        except Exception as e:
            logger.error(f"Error verifying 2FA code: {e}")
            return False
    
    async def _is_2fa_required(self, user_id: int) -> bool:
        """Проверяет, требуется ли для пользователя 2FA."""
        # Получаем роль пользователя
        user_role = await get_user_role(user_id)
        
        # 2FA требуется только для админов и суперадминов
        if user_role not in [Role.ADMIN, Role.SUPER_ADMIN]:
            return False
            
        # Проверяем, включена ли 2FA для пользователя
        return await two_factor_auth.is_2fa_enabled(user_id)
    
    def _is_auth_command(self, event) -> bool:
        """Проверяет, является ли сообщение командой аутентификации."""
        if hasattr(event, 'message') and event.message and event.message.text:
            text = event.message.text.lower()
            return any(text.startswith(f'/{cmd}') for cmd in self.allowed_commands)
        return False


def setup_2fa_middleware(dp):
    """Добавляет 2FA middleware в диспетчер."""
    two_factor_middleware = TwoFactorAuthMiddleware(dp.fsm.storage)
    dp.message.middleware(two_factor_middleware)
    dp.callback_query.middleware(two_factor_middleware)
    return dp
