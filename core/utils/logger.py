import logging

def get_logger(name: str) -> logging.Logger:
    """Простая функция для получения логгера"""
    return logging.getLogger(name)
