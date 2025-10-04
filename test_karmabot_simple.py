#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1
Тестирует бота который работает на Railway
"""

import asyncio
import logging
import json
from datetime import datetime
from aiogram import Bot

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8363530491:AAEzRHLzbIyNk3ZvjMvXYnar-6Z7kG9L0k8"
TEST_USER_ID = 6391215556

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KarmaBotTester:
    def __init__(self, token: str, user_id: int):
        self.bot = Bot(token=token)
        self.user_id = user_id
        self.test_results = []
        self.offset = 0
        
    async def log_result(self, test_name: str, status: str, details: dict = None):
        result = {
            'test': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        icons = {'PASS': '[OK]', 'FAIL': '[FAIL]', 'WARN': '[WARN]'}
        logger.info(f"{icons[status]} {test_name}: {status}")
        if details:
            for key, value in details.items():
                logger.info(f"   - {key}: {value}")
    
    async def get_updates(self, timeout=5):
        try:
            updates = await self.bot.get_updates(
                offset=self.offset,
                timeout=timeout,
                allowed_updates=["message", "callback_query"]
            )
            
            if updates:
                self.offset = updates[-1].update_id + 1
            
            return updates
        except Exception as e:
            logger.error(f"Ошибка получения обновлений: {e}")
            return []
    
    async def wait_for_response(self, wait_time=5):
        await asyncio.sleep(2)
        
        for _ in range(wait_time):
            updates = await self.get_updates()
            
            for update in updates:
                if update.message and update.message.chat.id == self.user_id:
                    if update.message.from_user.is_bot or update.message.from_user.id != self.user_id:
                        return update.message
            
            await asyncio.sleep(1)
        
        return None
    
    async def test_1_connection(self):
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 1: Проверка подключения к боту")
        logger.info("="*60)
        
        try:
            me = await self.bot.get_me()
            await self.log_result(
                "Подключение к боту",
                "PASS",
                {
                    "username": f"@{me.username}",
                    "name": me.first_name,
                    "id": me.id,
                    "is_bot": me.is_bot
                }
            )
            logger.info("[OK] Бот запущен и доступен!")
            return True
        except Exception as e:
            await self.log_result("Подключение к боту", "FAIL", {"error": str(e)})
            logger.error("[FAIL] Бот недоступен! Проверь Railway")
            return False
    
    async def test_2_start_command(self):
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 2: Команда /start")
        logger.info("="*60)
        
        try:
            await self.get_updates()
            await self.bot.send_message(self.user_id, "/start")
            logger.info("Отправлена команда /start...")
            
            msg = await self.wait_for_response(wait_time=10)
            
            if msg:
                text = msg.text or msg.caption or ""
                has_keyboard = msg.reply_markup is not None
                
                keyboard_type = "нет"
                if has_keyboard:
                    if hasattr(msg.reply_markup, 'keyboard'):
                        keyboard_type = "Reply keyboard"
                    elif hasattr(msg.reply_markup, 'inline_keyboard'):
                        keyboard_type = "Inline keyboard"
                
                await self.log_result(
                    "Команда /start",
                    "PASS",
                    {
                        "response_length": len(text),
                        "has_keyboard": has_keyboard,
                        "keyboard_type": keyboard_type,
                        "preview": text[:100] + "..." if len(text) > 100 else text
                    }
                )
                return msg
            else:
                await self.log_result(
                    "Команда /start", 
                    "FAIL", 
                    {"note": "Нет ответа от бота"}
                )
                return None
                
        except Exception as e:
            await self.log_result("Команда /start", "FAIL", {"error": str(e)})
            return None
    
    async def test_3_main_menu(self, last_message):
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 3: Проверка главного меню")
        logger.info("="*60)
        
        try:
            if not last_message or not last_message.reply_markup:
                await self.log_result("Главное меню", "FAIL", {"note": "Нет клавиатуры"})
                return []
            
            found_buttons = []
            if hasattr(last_message.reply_markup, 'keyboard'):
                for row in last_message.reply_markup.keyboard:
                    for button in row:
                        found_buttons.append(button.text)
            
            await self.log_result(
                "Главное меню",
                "PASS",
                {
                    "found_buttons": len(found_buttons),
                    "buttons": found_buttons
                }
            )
            
            return found_buttons
            
        except Exception as e:
            await self.log_result("Главное меню", "FAIL", {"error": str(e)})
            return []
    
    async def test_4_button_click(self, button_text: str):
        logger.info(f"\nТестируем кнопку: {button_text}")
        
        try:
            await self.get_updates()
            await self.bot.send_message(self.user_id, button_text)
            logger.info(f"Отправлено: {button_text}")
            
            msg = await self.wait_for_response(wait_time=10)
            
            if not msg:
                await self.log_result(f"Кнопка: {button_text}", "FAIL", {"note": "Нет ответа"})
                return None
            
            response_text = msg.text or msg.caption or "Медиа без текста"
            
            await self.log_result(
                f"Кнопка: {button_text}",
                "PASS",
                {
                    "response_preview": response_text[:80] + "..." if len(response_text) > 80 else response_text
                }
            )
            
            return True
            
        except Exception as e:
            await self.log_result(f"Кнопка: {button_text}", "FAIL", {"error": str(e)})
            return None
    
    async def run_all_tests(self):
        logger.info("\n\nТЕСТИРОВАНИЕ KARMABOT1 НА RAILWAY\n")
        
        # ТЕСТ 1: Подключение
        if not await self.test_1_connection():
            logger.error("[FAIL] Бот не отвечает! Проверь Railway")
            return
        
        await asyncio.sleep(2)
        
        logger.info("\nВАЖНО: Открой чат с ботом в Telegram!")
        logger.info("Напиши боту /start вручную ОДИН РАЗ")
        logger.info("Затем жди 5 секунд...\n")
        await asyncio.sleep(5)
        
        # ТЕСТ 2: /start
        last_msg = await self.test_2_start_command()
        
        if not last_msg:
            logger.error("[FAIL] Бот не отвечает на команды!")
            return
        
        await asyncio.sleep(2)
        
        # ТЕСТ 3: Главное меню
        menu_buttons = await self.test_3_main_menu(last_msg)
        await asyncio.sleep(2)
        
        # ТЕСТ 4: Тестируем каждую кнопку
        if menu_buttons:
            for button in menu_buttons:
                await self.test_4_button_click(button)
                await asyncio.sleep(3)
        
        # Итоги
        await self.print_summary()
        await self.save_report()
        
        await self.bot.session.close()
    
    async def print_summary(self):
        logger.info("\n\nИТОГИ ТЕСТИРОВАНИЯ\n")
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        total = len(self.test_results)
        
        logger.info(f"[OK] Успешно:       {passed}/{total}")
        logger.info(f"[WARN] Предупреждения: {warned}/{total}")
        logger.info(f"[FAIL] Провалено:     {failed}/{total}")
        logger.info(f"Процент успеха: {(passed/total*100 if total > 0 else 0):.1f}%\n")
    
    async def save_report(self):
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway',
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'results': self.test_results
        }
        
        filename = f'railway_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Отчет сохранен: {filename}")

async def main():
    print("АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1 НА RAILWAY")
    print("=" * 50)
    
    tester = KarmaBotTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_all_tests()
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("Проверь файлы:")
    print("- railway_test_report_*.json (полный отчет)")
    print("- bot_test.log (лог тестирования)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nТестирование остановлено")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

