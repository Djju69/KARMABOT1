import logging
import sys

# Fix for Windows console encoding
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, 'utf-8', errors='replace')

def get_logger(name: str) -> logging.Logger:
    """Простая функция для получения логгера"""
    logger = logging.getLogger(name)
    
    # Ensure we have at least one handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
