#!/usr/bin/env python3
"""
Простая проверка бота без getUpdates
"""
import asyncio
from aiogram import Bot

BOT_TOKEN = "8363530491:AAEzRHLzbIyNk3ZvjMvXYnar-6Z7kG9L0k8"
TEST_USER_ID = 6391215556

async def test_bot():
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Проверяем что бот доступен
        me = await bot.get_me()
        print(f"Бот найден: @{me.username} ({me.first_name})")
        
        # Отправляем сообщение
        print("Отправляем /start...")
        await bot.send_message(TEST_USER_ID, "/start")
        print("Сообщение отправлено!")
        
        print("\nТеперь:")
        print("1. Открой Telegram")
        print("2. Найди бота @Karma25TESTBot")
        print("3. Напиши ему /start")
        print("4. Проверь что он отвечает")
        
        print("\nЕсли бот НЕ отвечает - проверь Railway:")
        print("- Зайди на railway.app")
        print("- Открой проект KARMABOT1")
        print("- Проверь логи (Logs)")
        print("- Убедись что бот запущен")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot())

