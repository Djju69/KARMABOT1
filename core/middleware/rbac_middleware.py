"""
Middleware для проверки прав доступа на основе ролей.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
import logging

from core.security.roles import get_user_role, Permission
from core.database import role_repository

logger = logging.getLogger(__name__)

class RBACMiddleware(BaseMiddleware):
    """
    Middleware для проверки прав доступа на основе ролей.
    
    Проверяет, есть ли у пользователя необходимые права для выполнения действия.
    """
    
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
        
        # Получаем роль пользователя
        user_role = await get_user_role(user_id)
        
        # Сохраняем роль в data для использования в хендлерах
        data['user_role'] = user_role
        
        # Логируем попытку доступа
        logger.info(
            "User %s (role: %s) is trying to access handler: %s",
            user_id, user_role.name, handler.__name__
        )
        
        # Проверяем доступ к команде (если это команда)
        if event.message and event.message.is_command():
            command = event.message.text.split()[0].lower()
            if not await self._check_command_access(command, user_role):
                await message.answer("У вас нет прав на выполнение этой команды.")
                return
        
        # Продолжаем выполнение цепочки middleware и хендлеров
        return await handler(event, data)
    
    async def _check_command_access(self, command: str, user_role) -> bool:
        """Проверяет, есть ли у роли доступ к команде."""
        # Маппинг команд к необходимым разрешениям
        command_permissions = {
            '/admin': Permission.MANAGE_SETTINGS,
            '/moderate': Permission.MODERATE_CARDS,
            '/ban': Permission.MANAGE_PARTNERS,
            # Добавьте другие команды и необходимые права
        }
        
        required_permission = command_permissions.get(command)
        if not required_permission:
            return True  # Если команда не требует специальных прав
            
        return required_permission in user_role.value


def setup_rbac_middleware(dp):
    """Добавляет RBAC middleware в диспетчер."""
    rbac_middleware = RBACMiddleware()
    dp.message.middleware(rbac_middleware)
    dp.callback_query.middleware(rbac_middleware)
    return dp
