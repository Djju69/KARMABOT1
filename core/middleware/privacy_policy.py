"""
Middleware для принудительного принятия политики конфиденциальности
Блокирует все действия пользователя до принятия политики
"""
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

logger = logging.getLogger(__name__)

class PrivacyPolicyMiddleware(BaseMiddleware):
    """
    Middleware для проверки принятия политики конфиденциальности
    Блокирует все действия кроме разрешенных команд
    """
    
    # Разрешенные команды и callback_data
    ALLOWED_COMMANDS = ['/start', '/help']
    ALLOWED_CALLBACKS = ['lang:', 'policy:', 'accept_policy', 'decline_policy']
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Проверяет принятие политики перед обработкой события"""
        
        try:
            # Получаем пользователя и состояние
            user_id = None
            state = data.get('state')
            
            if isinstance(event, Message):
                user_id = event.from_user.id
                # Проверяем разрешенные команды
                if event.text and any(event.text.startswith(cmd) for cmd in self.ALLOWED_COMMANDS):
                    return await handler(event, data)
                    
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id
                # Проверяем разрешенные callback
                if event.data and any(event.data.startswith(cb) for cb in self.ALLOWED_CALLBACKS):
                    return await handler(event, data)
            
            if not user_id or not state:
                return await handler(event, data)
            
            # Проверяем статус принятия политики
            user_data = await state.get_data()
            policy_accepted = user_data.get('policy_accepted', False)
            
            if not policy_accepted:
                # Блокируем действие и показываем политику
                await self._block_action(event, user_id)
                return
            
            # Политика принята - продолжаем обработку
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Error in PrivacyPolicyMiddleware: {e}", exc_info=True)
            # В случае ошибки разрешаем продолжить
            return await handler(event, data)
    
    async def _block_action(self, event: TelegramObject, user_id: int):
        """Блокирует действие и показывает политику"""
        try:
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Для использования бота необходимо принять политику конфиденциальности.\n\nОтправьте /start для начала работы."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Сначала примите политику конфиденциальности",
                    show_alert=True
                )
                
            logger.info(f"Blocked action for user {user_id} - policy not accepted")
            
        except Exception as e:
            logger.error(f"Error blocking action for user {user_id}: {e}")
