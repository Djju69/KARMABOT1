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
from core.services.cache import cache_service
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
        """Проверка прав доступа пользователя для сообщений и колбэков.

        В aiogram v3 в middleware приходит конкретный объект события (Message, CallbackQuery и т.д.),
        поэтому нельзя обращаться к event.message. Нужно проверять тип события.
        """

        try:
            message_obj: Message | None = None
            user_id: int | None = None

            if isinstance(event, Message):
                message_obj = event
                user_id = event.from_user.id if event.from_user else None
            elif isinstance(event, CallbackQuery):
                message_obj = event.message
                user_id = event.from_user.id if event.from_user else None
            else:
                # Пропускаем события, для которых RBAC не применим
                return await handler(event, data)

            if not user_id:
                # Нет пользователя — пропускаем без проверки
                return await handler(event, data)

            # Получаем состояние пользователя (если нужно далее)
            state: FSMContext = data.get('state')  # noqa: F841 (оставлено на будущее использование)

            # Получаем роль пользователя с простым кэшированием на короткое время
            cache_key = f"rbac:role:{user_id}"
            cached = await cache_service.get(cache_key)
            if cached:
                user_role = cached
            else:
                user_role = await get_user_role(user_id)
                # Кэшируем на 60 секунд, чтобы снизить нагрузку и лог-спам
                try:
                    await cache_service.set(cache_key, user_role, ex=60)
                except Exception:
                    pass

            # Сохраняем роль в data для использования в хендлерах
            data['user_role'] = user_role

            # Логируем попытку доступа
            role_name = getattr(user_role, 'name', str(user_role))
            logger.debug(
                "[RBAC] user=%s role=%s handler=%s",
                user_id, role_name, getattr(handler, '__name__', str(handler))
            )

            # Проверяем доступ к команде (если это текстовая команда)
            if isinstance(event, Message) and hasattr(event, 'text') and event.text and event.text.startswith('/'):
                command = (event.text or '').split()[0].lower()
                if not await self._check_command_access(command, user_role):
                    if message_obj:
                        await message_obj.answer("У вас нет прав на выполнение этой команды.")
                    return

            # Продолжаем выполнение цепочки middleware и хендлеров
            return await handler(event, data)

        except Exception as e:
            logger.error(f"RBAC Middleware error: {e}", exc_info=True)
            # Не блокируем обработку при ошибке middleware
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
