"""
Модуль логирования для совместимости
"""
import logging
import sys
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Получение логгера для совместимости
    
    Args:
        name: Имя логгера (опционально)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # Если логгер еще не настроен
    if not logger.handlers:
        # Создаем обработчик для консоли
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

# Создаем глобальный логгер для совместимости
logger = get_logger(__name__)
