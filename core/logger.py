"""
Адаптер для логгера - перенаправляет к существующим настройкам.
Совместим с импортами вида `from core.logger import get_logger`.
"""
from typing import Optional
import logging


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Получить настроенный логгер."""
    if name is None:
        name = __name__

    logger = logging.getLogger(name)

    if not logger.handlers:
        # Базовая настройка если нет обработчиков
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    return logger


# Для совместимости
main_logger = get_logger('bot')


