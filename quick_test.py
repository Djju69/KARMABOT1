#!/usr/bin/env python3
"""
Простая проверка бота
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
        
        # Ждем обновления
        print("Ждем ответ...")
        updates = await bot.get_updates(timeout=10)
        
        if updates:
            print(f"Получено {len(updates)} обновлений")
            for update in updates:
                if update.message:
                    print(f"Ответ: {update.message.text}")
        else:
            print("Нет ответа от бота!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot())

