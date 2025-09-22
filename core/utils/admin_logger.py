"""
Система логирования админских действий для аудита и безопасности
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from aiogram.types import Message, CallbackQuery

# Создать директорию для логов если не существует
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настроить специальный логгер для админских действий
admin_logger = logging.getLogger("admin_actions")
admin_logger.setLevel(logging.INFO)

# Удалить существующие обработчики чтобы избежать дублирования
for handler in admin_logger.handlers[:]:
    admin_logger.removeHandler(handler)

# Создать файловый обработчик
log_file = log_dir / "admin_actions.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Создать форматтер с подробной информацией
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# Добавить обработчик к логгеру
admin_logger.addHandler(file_handler)

# Предотвратить дублирование логов в корневой логгер
admin_logger.propagate = False


class AdminActionLogger:
    """
    Класс для логирования всех админских действий
    """
    
    def __init__(self):
        self.logger = admin_logger
    
    def _get_user_info(self, event: Union[Message, CallbackQuery]) -> Dict[str, Any]:
        """
        Извлечь информацию о пользователе из события
        
        Args:
            event: Событие Telegram (Message или CallbackQuery)
            
        Returns:
            Dict с информацией о пользователе
        """
        user = event.from_user
        
        return {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language_code': user.language_code,
            'is_premium': getattr(user, 'is_premium', False)
        }
    
    def _get_chat_info(self, event: Union[Message, CallbackQuery]) -> Dict[str, Any]:
        """
        Извлечь информацию о чате из события
        
        Args:
            event: Событие Telegram (Message или CallbackQuery)
            
        Returns:
            Dict с информацией о чате
        """
        chat = event.chat
        
        return {
            'chat_id': chat.id,
            'chat_type': chat.type,
            'chat_title': getattr(chat, 'title', None)
        }
    
    def _get_action_context(self, event: Union[Message, CallbackQuery]) -> Dict[str, Any]:
        """
        Извлечь контекст действия из события
        
        Args:
            event: Событие Telegram (Message или CallbackQuery)
            
        Returns:
            Dict с контекстом действия
        """
        context = {
            'timestamp': datetime.now().isoformat(),
            'event_type': type(event).__name__
        }
        
        if isinstance(event, Message):
            context.update({
                'message_id': event.message_id,
                'text': event.text,
                'message_type': event.content_type,
                'has_photo': bool(event.photo),
                'has_document': bool(event.document),
                'has_location': bool(event.location)
            })
        elif isinstance(event, CallbackQuery):
            context.update({
                'callback_data': event.data,
                'message_id': event.message.message_id if event.message else None,
                'inline_message_id': event.inline_message_id
            })
        
        return context
    
    async def _get_user_role(self, user_id: int) -> str:
        """
        Определить роль пользователя
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            str: Роль пользователя
        """
        try:
            # Проверить супер-админа
            from core.settings import settings
            if int(user_id) == int(settings.bots.admin_id):
                return 'super_admin'
            
            # Проверить админов
            from core.services.admins import admins_service
            if await admins_service.is_admin(user_id):
                return 'admin'
            
            # Проверить партнеров
            from core.database.db_v2 import db_v2
            partner = await db_v2.get_partner_by_telegram_id(user_id)
            if partner:
                return 'partner'
            
            return 'user'
            
        except Exception as e:
            self.logger.error(f"Ошибка определения роли пользователя {user_id}: {e}")
            return 'unknown'
    
    def log_action(self, 
                   event: Union[Message, CallbackQuery],
                   action: str,
                   target: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None,
                   result: Optional[str] = None):
        """
        Записать действие администратора в лог
        
        Args:
            event: Событие Telegram
            action: Название действия
            target: Цель действия (например, ID пользователя)
            details: Дополнительные детали
            result: Результат действия (success, error, etc.)
        """
        try:
            # Собрать всю информацию
            log_entry = {
                'action': action,
                'target': target,
                'details': details or {},
                'result': result,
                'user': self._get_user_info(event),
                'chat': self._get_chat_info(event),
                'context': self._get_action_context(event)
            }
            
            # Добавить роль пользователя (асинхронно)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Если цикл уже запущен, создать задачу
                    task = asyncio.create_task(self._get_user_role(event.from_user.id))
                    # Не ждем завершения, используем значение по умолчанию
                    log_entry['user']['role'] = 'unknown'
                else:
                    # Если цикл не запущен, выполнить синхронно
                    log_entry['user']['role'] = asyncio.run(self._get_user_role(event.from_user.id))
            except:
                log_entry['user']['role'] = 'unknown'
            
            # Записать в лог
            self.logger.info(json.dumps(log_entry, ensure_ascii=False, indent=None))
            
        except Exception as e:
            self.logger.error(f"Ошибка логирования действия: {e}")
    
    def log_security_event(self, 
                          event: Union[Message, CallbackQuery],
                          event_type: str,
                          severity: str = "medium",
                          description: str = ""):
        """
        Записать событие безопасности
        
        Args:
            event: Событие Telegram
            event_type: Тип события безопасности
            severity: Уровень серьезности (low, medium, high, critical)
            description: Описание события
        """
        try:
            security_entry = {
                'type': 'security_event',
                'event_type': event_type,
                'severity': severity,
                'description': description,
                'user': self._get_user_info(event),
                'chat': self._get_chat_info(event),
                'context': self._get_action_context(event)
            }
            
            self.logger.warning(json.dumps(security_entry, ensure_ascii=False, indent=None))
            
        except Exception as e:
            self.logger.error(f"Ошибка логирования события безопасности: {e}")


# Глобальный экземпляр логгера
admin_action_logger = AdminActionLogger()


def log_admin_action(action_name: str):
    """
    Декоратор для автоматического логирования админских действий
    
    Args:
        action_name: Название действия для логирования
        
    Returns:
        Декоратор функции
    """
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            try:
                # Определить тип события
                if hasattr(message_or_callback, 'message'):
                    event = message_or_callback  # CallbackQuery
                else:
                    event = message_or_callback   # Message
                
                # Логировать начало действия
                admin_action_logger.log_action(
                    event=event,
                    action=f"{action_name}_start",
                    details={'args': str(args), 'kwargs': str(kwargs)}
                )
                
                # Выполнить функцию
                result = await func(message_or_callback, *args, **kwargs)
                
                # Логировать успешное завершение
                admin_action_logger.log_action(
                    event=event,
                    action=f"{action_name}_success",
                    result="success"
                )
                
                return result
                
            except Exception as e:
                # Логировать ошибку
                admin_action_logger.log_action(
                    event=event,
                    action=f"{action_name}_error",
                    result="error",
                    details={'error': str(e)}
                )
                raise
        
        return wrapper
    return decorator


def log_security_event(event_type: str, severity: str = "medium"):
    """
    Декоратор для логирования событий безопасности
    
    Args:
        event_type: Тип события безопасности
        severity: Уровень серьезности
        
    Returns:
        Декоратор функции
    """
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            try:
                # Определить тип события
                if hasattr(message_or_callback, 'message'):
                    event = message_or_callback  # CallbackQuery
                else:
                    event = message_or_callback   # Message
                
                # Логировать событие безопасности
                admin_action_logger.log_security_event(
                    event=event,
                    event_type=event_type,
                    severity=severity,
                    description=f"Function {func.__name__} called"
                )
                
                return await func(message_or_callback, *args, **kwargs)
                
            except Exception as e:
                # Логировать критическую ошибку безопасности
                admin_action_logger.log_security_event(
                    event=event,
                    event_type=f"{event_type}_error",
                    severity="critical",
                    description=f"Error in {func.__name__}: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


# Функции для прямого логирования
def log_admin_action_direct(event: Union[Message, CallbackQuery],
                           action: str,
                           target: Optional[str] = None,
                           details: Optional[Dict[str, Any]] = None,
                           result: Optional[str] = None):
    """
    Прямое логирование админского действия
    
    Args:
        event: Событие Telegram
        action: Название действия
        target: Цель действия
        details: Дополнительные детали
        result: Результат действия
    """
    admin_action_logger.log_action(event, action, target, details, result)


def log_security_event_direct(event: Union[Message, CallbackQuery],
                             event_type: str,
                             severity: str = "medium",
                             description: str = ""):
    """
    Прямое логирование события безопасности
    
    Args:
        event: Событие Telegram
        event_type: Тип события безопасности
        severity: Уровень серьезности
        description: Описание события
    """
    admin_action_logger.log_security_event(event, event_type, severity, description)

