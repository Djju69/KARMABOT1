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
        # Корректная работа с типами событий в aiogram v3
        message = None
        user_id = None

        if isinstance(event, Message):
            message = event
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            message = event.message
            user_id = event.from_user.id if event.from_user else None
        else:
            # Пропускаем события, не относящиеся к пользовательским апдейтам
            return await handler(event, data)
        
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
            ip_address=None
        )
        
        # Отправляем сообщение с просьбой пройти 2FA
        try:
            if isinstance(event, CallbackQuery):
                await event.answer("🔒 Требуется двухфакторная аутентификация", show_alert=True)
            elif message is not None:
                await message.answer("🔒 Требуется двухфакторная аутентификация. Пожалуйста, введите код из приложения аутентификатора.")
        except Exception:
            pass
        
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
        """Проверяет, является ли событие командой аутентификации."""
        try:
            if isinstance(event, Message):
                text = (event.text or '').lower()
                return any(text.startswith(f'/{cmd}') for cmd in self.allowed_commands)
            if isinstance(event, CallbackQuery):
                data = (event.data or '').lower()
                return data.startswith('auth')
        except Exception:
            return False
        return False


def setup_2fa_middleware(dp):
    """Добавляет 2FA middleware в диспетчер."""
    two_factor_middleware = TwoFactorAuthMiddleware(dp.fsm.storage)
    dp.message.middleware(two_factor_middleware)
    dp.callback_query.middleware(two_factor_middleware)
    return dp
