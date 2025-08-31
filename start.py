#!/usr/bin/env python3
# Альтернативный скрипт запуска с обработкой PORT

import os
import uvicorn
from web.main import app

def main():
    # Получаем порт из переменной окружения или используем по умолчанию
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
