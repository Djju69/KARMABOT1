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
    ALLOWED_COMMANDS = ['/start']
    # Только язык и политика до принятия
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
            current_state = None
            
            if isinstance(event, Message):
                user_id = event.from_user.id
                # Разрешаем только /start до принятия политики
                if event.text and any(event.text.startswith(cmd) for cmd in self.ALLOWED_COMMANDS):
                    return await handler(event, data)
                    
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id
                # Проверяем разрешенные callback
                if event.data and any(event.data.startswith(cb) for cb in self.ALLOWED_CALLBACKS):
                    return await handler(event, data)
            
            # Полный bypass для супер-админа
            try:
                from core.settings import settings as _settings
                admin_id = getattr(_settings.bots, 'admin_id', None)
                if admin_id is not None and user_id is not None and int(user_id) == int(admin_id):
                    return await handler(event, data)
            except Exception:
                pass

            if not user_id or not state:
                return await handler(event, data)
            
            # Проверяем статус принятия политики (FSM -> DB)
            user_data = await state.get_data()
            policy_accepted = user_data.get('policy_accepted', False)
            if not policy_accepted:
                # Пытаемся проверить в БД (users.policy_accepted)
                import os
                database_url = os.getenv("DATABASE_URL", "").lower()
                try:
                    if database_url.startswith("postgres"):
                        # PostgreSQL путь (asyncpg)
                        import asyncpg
                        conn_pg = await asyncpg.connect(os.getenv("DATABASE_URL"))
                        try:
                            val = await conn_pg.fetchval(
                                "SELECT policy_accepted FROM users WHERE telegram_id = $1",
                                int(user_id),
                            )
                            policy_accepted = bool(val) if val is not None else False
                        finally:
                            await conn_pg.close()
                    else:
                        # SQLite путь
                        from core.database.db_v2 import db_v2
                        conn = db_v2.get_connection()
                        try:
                            cur = conn.execute(
                                "SELECT policy_accepted FROM users WHERE telegram_id = ?",
                                (int(user_id),),
                            )
                            row = cur.fetchone()
                            if row is not None:
                                policy_accepted = bool(row[0] if not isinstance(row, dict) else row.get('policy_accepted'))
                        finally:
                            try:
                                conn.close()
                            except Exception:
                                pass
                except Exception:
                    # В случае ошибки — оставляем предыдущее значение
                    pass
            
            if not policy_accepted:
                # Проверка не прошла
                logger.info(f"Policy check failed for user {user_id}")
                
                # Блокируем действие и показываем политику
                await self._block_action(event, user_id)
                return
            else:
                # Диагностический лог при успешной проверке
                logger.info(f"DIAGNOSTIC: Policy check passed for user {user_id} - policy_accepted=True")
            
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
