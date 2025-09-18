#!/usr/bin/env python3
"""
Скрипт для удаления файла etup
"""
import os
import sys

def main():
    file_path = "etup"
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"✅ Файл {file_path} успешно удален")
        except Exception as e:
            print(f"❌ Ошибка при удалении {file_path}: {e}")
    else:
        print(f"ℹ️ Файл {file_path} не найден")

if __name__ == "__main__":
    main()
