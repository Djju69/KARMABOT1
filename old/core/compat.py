"""
Compatibility layer for aiogram v3
"""
from typing import Any, Callable, Coroutine, TypeVar, Union, Optional
from functools import wraps

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

T = TypeVar('T')

# Типы, которые могут быть переданы в хэндлер
HandlerArg = Union[Message, CallbackQuery]

# Тип асинхронной функции
AsyncFunc = Callable[..., Coroutine[Any, Any, T]]

def compat_handler(handler: AsyncFunc[T]) -> AsyncFunc[T]:
    """
    Декоратор для совместимости старых хэндлеров с aiogram v3
    
    Позволяет использовать старые хэндлеры с сигнатурой (message: Message) -> Any
    в новом коде, где ожидается (message: Message, bot: Bot, state: FSMContext) -> Any
    """
    @wraps(handler)
    async def wrapper(
        message: HandlerArg, 
        *args: Any, 
        **kwargs: Any
    ) -> T:
        # Пробуем вызвать хэндлер с переданными аргументами
        try:
            return await handler(message, *args, **kwargs)
        except TypeError as e:
            # Если возникла ошибка из-за несоответствия аргументов,
            # пробуем вызвать с минимальным набором аргументов
            if 'positional argument' in str(e):
                return await handler(message)
            raise
    
    return wrapper

async def call_compat(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Вызывает функцию с совместимостью по аргументам
    
    Использование:
        await call_compat(old_handler, message, bot, state)
    """
    try:
        return await func(*args, **kwargs)
    except TypeError as e:
        if 'positional argument' in str(e):
            # Оставляем только первый аргумент (обычно message или callback_query)
            if args:
                return await func(args[0])
            return await func()
        raise

# Алиасы для обратной совместимости
def add_compat_aliases():
    """Добавляет алиасы для обратной совместимости"""
    try:
        from .handlers import basic
        if not hasattr(basic, 'show_nearest_v2') and hasattr(basic, 'show_nearest'):
            basic.show_nearest_v2 = basic.show_nearest
            
        if not hasattr(basic, 'show_categories_v2') and hasattr(basic, 'show_categories'):
            basic.show_categories_v2 = basic.show_categories
    except ImportError as e:
        import logging
        logging.getLogger(__name__).debug("Could not set up compatibility aliases: %s", e)
