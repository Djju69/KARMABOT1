#!/usr/bin/env python3
"""
Скрипт для получения Telegram ID от @userinfobot
"""

print("""
╔═══════════════════════════════════════════════════════════╗
║              ПОЛУЧЕНИЕ TELEGRAM ID                       ║
╚═══════════════════════════════════════════════════════════╝

1. Открой Telegram
2. Найди @userinfobot
3. Отправь любое сообщение
4. Бот ответит твоим ID

ID выглядит примерно так:
123456789

""")

user_id = input("Вставь свой Telegram ID: ").strip()

if user_id.isdigit() and len(user_id) >= 8:
    print(f"\n✅ ID получен: {user_id}")
    
    # Обновляем .env файл
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем или добавляем TEST_USER_ID
        if 'TEST_USER_ID=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('TEST_USER_ID='):
                    lines[i] = f'TEST_USER_ID={user_id}'
                    break
            content = '\n'.join(lines)
        else:
            content += f'\nTEST_USER_ID={user_id}\n'
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ ID сохранен в .env файл")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        print(f"Добавь в .env файл: TEST_USER_ID={user_id}")
    
    print("\n🎉 Готово! Теперь можно запускать тесты:")
    print("python test_karmabot_full.py")
    
else:
    print("❌ Неверный формат ID!")
    print("ID должен содержать только цифры и быть длиннее 7 символов")
