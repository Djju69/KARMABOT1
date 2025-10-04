#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для получения токена бота от @BotFather
"""

print("="*60)
print("ПОЛУЧЕНИЕ ТОКЕНА БОТА")
print("="*60)
print()
print("1. Открой Telegram")
print("2. Найди @BotFather")
print("3. Отправь команду /mybots")
print("4. Выбери своего бота")
print("5. Нажми 'API Token'")
print("6. Скопируй токен")
print()
print("Токен выглядит примерно так:")
print("1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890")
print()

token = input("Вставь токен бота: ").strip()

if token and ":" in token and len(token) > 20:
    print(f"\n✅ Токен получен: {token[:10]}...")
    
    # Обновляем .env файл
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем или добавляем BOT_TOKEN
        if 'BOT_TOKEN=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('BOT_TOKEN='):
                    lines[i] = f'BOT_TOKEN={token}'
                    break
            content = '\n'.join(lines)
        else:
            content += f'\nBOT_TOKEN={token}\n'
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: Токен сохранен в .env файл")
        
    except Exception as e:
        print(f"ERROR: Ошибка сохранения: {e}")
        print(f"Добавь в .env файл: BOT_TOKEN={token}")
    
    # Обновляем тестировщик
    try:
        with open('test_karmabot_full.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_СЮДА_BOT_TOKEN"', f'BOT_TOKEN = os.getenv("BOT_TOKEN") or "{token}"')
        
        with open('test_karmabot_full.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("OK: Тестировщик обновлен")
        
    except Exception as e:
        print(f"ERROR: Ошибка обновления тестировщика: {e}")
    
    print("\nГотово! Теперь можно запускать тесты:")
    print("python test_karmabot_full.py")
    
else:
    print("ERROR: Неверный формат токена!")
    print("Токен должен содержать ':' и быть длиннее 20 символов")
