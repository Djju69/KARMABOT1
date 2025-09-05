"""
Middleware для проверки двухфакторной аутентификации.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from core.security.two_factor_auth import two_factor_auth
from core.security.roles import get_user_role, Role
from core.database import role_repository

logger = logging.getLogger(__name__)


class TwoFactorAuthMiddleware(BaseMiddleware):
	def __init__(self, storage):
		super().__init__()
		self.storage = storage
		self.allowed_commands = {'start', 'help', 'cancel', 'auth'}

	async def __call__(
		self,
		handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
		event: Update,
		data: Dict[str, Any]
	) -> Any:
		# Определяем наличие message/callback безопасно
		has_message = hasattr(event, 'message') and isinstance(event.message, Message)
		has_cbq = hasattr(event, 'callback_query') and isinstance(event.callback_query, CallbackQuery)
		if not (has_message or has_cbq):
			return await handler(event, data)

		message: Message | None = event.message if has_message else (event.callback_query.message if has_cbq else None)
		from_user = (event.message.from_user if has_message else event.callback_query.from_user)
		user_id = from_user.id if from_user else None

		state: FSMContext | None = data.get('state')

		# Разрешённые команды без 2FA
		if self._is_auth_command(event):
			return await handler(event, data)

		# 2FA требуется только для ADMIN/SA
		if user_id is None:
			return await handler(event, data)
		if not await self._is_2fa_required(user_id):
			return await handler(event, data)

		# Проверка пройдена ли 2FA в FSM
		if state is not None:
			state_data = await state.get_data()
			if state_data.get('2fa_verified', False):
				return await handler(event, data)

		logger.warning("2FA required for user %s", str(user_id))
		try:
			await role_repository.log_audit_event(
				user_id=user_id,
				action="2FA_REQUIRED",
				entity_type="user",
				entity_id=user_id,
				ip_address=None,
			)
		except Exception:
			pass

		# Сообщение пользователю
		text = "🔒 Требуется двухфакторная аутентификация. Введите код из приложения."
		try:
			if has_message and message is not None:
				await message.answer(text)
			elif has_cbq and event.callback_query is not None:
				await event.callback_query.message.answer(text)
		except Exception:
			pass
		return False

	async def _is_2fa_required(self, user_id: int) -> bool:
		user_role = await get_user_role(user_id)
		return user_role in [Role.ADMIN, Role.SUPER_ADMIN] and await two_factor_auth.is_2fa_enabled(user_id)

	def _is_auth_command(self, event) -> bool:
		if hasattr(event, 'message') and isinstance(event.message, Message) and event.message.text:
			text = (event.message.text or '').lower()
			return any(text.startswith(f'/{cmd}') for cmd in self.allowed_commands)
		return False


def setup_2fa_middleware(dp):
	two_factor_middleware = TwoFactorAuthMiddleware(dp.fsm.storage)
	dp.message.middleware(two_factor_middleware)
	dp.callback_query.middleware(two_factor_middleware)
	return dp
