#!/usr/bin/env python3
"""
ТЕСТИРОВЩИК KARMABOT1 через API (без getUpdates)
Проверяет бота который работает на Railway
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
            logger.error("[FAIL] Бот недоступен!")
            return False
    
    async def test_2_send_commands(self):
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 2: Отправка команд боту")
        logger.info("="*60)
        
        commands = [
            "/start",
            "/help", 
            "/menu",
            "Категории",
            "Помощь"
        ]
        
        for cmd in commands:
            try:
                await self.bot.send_message(self.user_id, cmd)
                await self.log_result(f"Отправка: {cmd}", "PASS", {"status": "отправлено"})
                logger.info(f"[OK] Отправлено: {cmd}")
                await asyncio.sleep(1)  # Задержка между командами
                
            except Exception as e:
                await self.log_result(f"Отправка: {cmd}", "FAIL", {"error": str(e)})
                logger.error(f"[FAIL] Ошибка отправки {cmd}: {e}")
    
    async def test_3_check_webhook(self):
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 3: Проверка webhook")
        logger.info("="*60)
        
        try:
            webhook_info = await self.bot.get_webhook_info()
            
            if webhook_info.url:
                await self.log_result(
                    "Webhook настроен",
                    "PASS",
                    {
                        "url": webhook_info.url,
                        "pending_updates": webhook_info.pending_update_count
                    }
                )
                logger.info(f"[OK] Webhook: {webhook_info.url}")
            else:
                await self.log_result("Webhook", "WARN", {"note": "Webhook не настроен"})
                logger.info("[WARN] Webhook не настроен")
                
        except Exception as e:
            await self.log_result("Webhook", "FAIL", {"error": str(e)})
            logger.error(f"[FAIL] Ошибка проверки webhook: {e}")
    
    async def test_4_check_commands(self):
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 4: Проверка команд бота")
        logger.info("="*60)
        
        try:
            commands = await self.bot.get_my_commands()
            
            if commands:
                cmd_list = [f"/{cmd.command} - {cmd.description}" for cmd in commands]
                await self.log_result(
                    "Команды бота",
                    "PASS",
                    {
                        "count": len(commands),
                        "commands": cmd_list
                    }
                )
                logger.info(f"[OK] Найдено {len(commands)} команд:")
                for cmd in cmd_list:
                    logger.info(f"   - {cmd}")
            else:
                await self.log_result("Команды бота", "WARN", {"note": "Команды не настроены"})
                logger.info("[WARN] Команды не настроены")
                
        except Exception as e:
            await self.log_result("Команды бота", "FAIL", {"error": str(e)})
            logger.error(f"[FAIL] Ошибка получения команд: {e}")
    
    async def run_all_tests(self):
        logger.info("\n\nТЕСТИРОВАНИЕ KARMABOT1 НА RAILWAY")
        logger.info("="*60)
        
        # ТЕСТ 1: Подключение
        if not await self.test_1_connection():
            logger.error("[FAIL] Бот недоступен! Проверь Railway")
            return
        
        await asyncio.sleep(1)
        
        # ТЕСТ 2: Отправка команд
        await self.test_2_send_commands()
        await asyncio.sleep(1)
        
        # ТЕСТ 3: Webhook
        await self.test_3_check_webhook()
        await asyncio.sleep(1)
        
        # ТЕСТ 4: Команды
        await self.test_4_check_commands()
        
        # Итоги
        await self.print_summary()
        await self.save_report()
        
        await self.bot.session.close()
    
    async def print_summary(self):
        logger.info("\n\nИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("="*60)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        total = len(self.test_results)
        
        logger.info(f"[OK] Успешно:       {passed}/{total}")
        logger.info(f"[WARN] Предупреждения: {warned}/{total}")
        logger.info(f"[FAIL] Провалено:     {failed}/{total}")
        logger.info(f"Процент успеха: {(passed/total*100 if total > 0 else 0):.1f}%")
        
        logger.info("\nЧТО ПРОВЕРИТЬ В TELEGRAM:")
        logger.info("1. Открой чат с ботом @Karma25TESTBot")
        logger.info("2. Проверь что бот отвечает на команды")
        logger.info("3. Проверь главное меню")
        logger.info("4. Проверь все кнопки")
    
    async def save_report(self):
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway',
            'bot_username': '@Karma25TESTBot',
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'results': self.test_results
        }
        
        filename = f'railway_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nОтчет сохранен: {filename}")

async def main():
    print("ТЕСТИРОВАНИЕ KARMABOT1 НА RAILWAY")
    print("="*50)
    
    tester = KarmaBotTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_all_tests()
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("Проверь файлы:")
    print("- railway_test_report_*.json (полный отчет)")
    print("- bot_test.log (лог тестирования)")
    print("\nТеперь проверь бота в Telegram!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nТестирование остановлено")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

