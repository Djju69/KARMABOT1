import logging
import sys
import io
from typing import Optional

# Fix for Windows console encoding
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, 'utf-8', errors='replace')

def setup_logging(level: int = logging.INFO) -> None:
    """Настройка базового логирования"""
    # Create a handler that encodes output as UTF-8
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True
    )

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Создает и возвращает логгер с указанным именем
    
    Args:
        name: Имя логгера (обычно __name__)
        level: Уровень логирования (optional)
    
    Returns:
        Объект логгера
    """
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    
    return logger

# Автоматическая настройка при импорте
setup_logging()
