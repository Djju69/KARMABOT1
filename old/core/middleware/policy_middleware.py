"""
Middleware для проверки принятия политики конфиденциальности.
Блокирует все функции бота до принятия политики пользователем.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from aiogram.fsm.context import FSMContext
import logging

from core.utils.locales_v2 import get_text

logger = logging.getLogger(__name__)

class PolicyMiddleware(BaseMiddleware):
    """
    Middleware для проверки принятия политики конфиденциальности.
    
    Блокирует все функции бота до принятия политики пользователем.
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        """Проверка принятия политики для сообщений и колбэков."""
        
        # Получаем данные события
        if event.message:
            user_id = event.message.from_user.id
            chat_id = event.message.chat.id
            message = event.message
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            chat_id = event.callback_query.message.chat.id
            message = event.callback_query.message
        else:
            return await handler(event, data)
        
        # Получаем состояние FSM
        state: FSMContext = data.get("state")
        if not state:
            return await handler(event, data)
        
        try:
            # Проверяем, принял ли пользователь политику
            user_data = await state.get_data()
            policy_accepted = user_data.get('policy_accepted', False)
            
            # Если политика не принята, блокируем все действия кроме выбора языка и принятия политики
            if not policy_accepted:
                # Разрешаем только выбор языка и принятие политики
                if event.callback_query:
                    callback_data = event.callback_query.data
                    if callback_data.startswith('lang:set:') or callback_data in ['policy:accept', 'policy:view']:
                        return await handler(event, data)
                    else:
                        # Блокируем все остальные callback'и
                        await event.callback_query.answer("❌ Сначала примите политику конфиденциальности")
                        return
                
                elif event.message:
                    # Разрешаем только команду /start
                    if event.message.text and event.message.text.startswith('/start'):
                        return await handler(event, data)
                    else:
                        # Блокируем все остальные сообщения
                        await message.answer("❌ Сначала примите политику конфиденциальности")
                        return
            
            # Если политика принята, разрешаем все действия
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Error in PolicyMiddleware: {e}", exc_info=True)
            # В случае ошибки разрешаем продолжить, чтобы не блокировать пользователя
            return await handler(event, data)
