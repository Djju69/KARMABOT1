"""
Middleware для проверки прав доступа на основе ролей.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from core.security.roles import get_user_role, Permission

logger = logging.getLogger(__name__)


class RBACMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
		event: Update,
		data: Dict[str, Any]
	) -> Any:
		# Определяем тип апдейта безопасно для aiogram v3
		has_message = hasattr(event, 'message') and isinstance(event.message, Message)
		has_cbq = hasattr(event, 'callback_query') and isinstance(event.callback_query, CallbackQuery)

		if not (has_message or has_cbq):
			return await handler(event, data)

		message: Message | None = event.message if has_message else (event.callback_query.message if has_cbq else None)
		from_user = (event.message.from_user if has_message else event.callback_query.from_user)
		user_id = from_user.id if from_user else None

		# Получаем состояние пользователя (если нужно далее)
		state: FSMContext | None = data.get('state')

		# Роль пользователя
		user_role = await get_user_role(user_id) if user_id is not None else None
		data['user_role'] = user_role

		try:
			logger.info("RBAC: user=%s role=%s handler=%s", str(user_id), getattr(user_role, 'name', None), getattr(handler, '__name__', str(handler)))
		except Exception:
			pass

		# Проверка доступа для команд (только для Message)
		if has_message and isinstance(message, Message) and message.text:
			text = message.text.strip()
			is_command = text.startswith('/')
			if is_command and user_role is not None:
				command = text.split()[0].lower()
				if not await self._check_command_access(command, user_role):
					try:
						await message.answer("У вас нет прав на выполнение этой команды.")
					except Exception:
						pass
					return

		return await handler(event, data)

	async def _check_command_access(self, command: str, user_role) -> bool:
		command_permissions = {
			'/admin': Permission.MANAGE_SETTINGS,
			'/moderate': Permission.MODERATE_CARDS,
			'/ban': Permission.MANAGE_PARTNERS,
		}
		required_permission = command_permissions.get(command)
		if not required_permission:
			return True
		return required_permission in getattr(user_role, 'value', set())


def setup_rbac_middleware(dp):
	"""Подключение middleware в диспетчер aiogram v3."""
	rbac = RBACMiddleware()
	dp.message.middleware(rbac)
	dp.callback_query.middleware(rbac)
	return dp
