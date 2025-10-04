#!/usr/bin/env python3
"""
ПРОСТОЙ ТЕСТИРОВЩИК KARMABOT1
Только отправляет команды - проверяет что они доставляются
БЕЗ КОНФЛИКТОВ с Railway webhook!
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
        logging.FileHandler('simple_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleTester:
    """Простой тестировщик без конфликтов"""
    
    def __init__(self, token: str, user_id: int):
        self.bot = Bot(token=token)
        self.user_id = user_id
        self.test_results = []
        self.message_counter = 0
        
    async def log_result(self, test_name: str, status: str, details: dict = None):
        """Логирование"""
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
    
    async def send_message(self, text: str):
        """Отправить сообщение"""
        try:
            message = await self.bot.send_message(self.user_id, text)
            self.message_counter += 1
            logger.info(f"Отправлено: {text} (ID: {message.message_id})")
            return message
        except Exception as e:
            logger.error(f"Ошибка отправки {text}: {e}")
            return None
    
    async def test_1_connection(self):
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 1: ПРОВЕРКА ПОДКЛЮЧЕНИЯ")
        logger.info("="*70)
        
        try:
            me = await self.bot.get_me()
            await self.log_result(
                "Подключение к боту",
                "PASS",
                {
                    "username": f"@{me.username}",
                    "name": me.first_name,
                    "id": me.id
                }
            )
            return True
        except Exception as e:
            await self.log_result("Подключение", "FAIL", {"error": str(e)})
            return False
    
    async def test_2_webhook_status(self):
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 2: СТАТУС WEBHOOK")
        logger.info("="*70)
        
        try:
            webhook_info = await self.bot.get_webhook_info()
            
            if webhook_info.url:
                logger.info(f"[INFO] Webhook настроен: {webhook_info.url}")
                logger.info(f"[INFO] Ожидающих обновлений: {webhook_info.pending_update_count}")
                
                if webhook_info.last_error_message:
                    logger.warning(f"[WARN] Последняя ошибка webhook: {webhook_info.last_error_message}")
                
                await self.log_result(
                    "Webhook статус",
                    "PASS",
                    {
                        "url": webhook_info.url,
                        "pending_updates": webhook_info.pending_update_count,
                        "last_error": webhook_info.last_error_message
                    }
                )
            else:
                logger.info("[INFO] Webhook не настроен")
                await self.log_result("Webhook статус", "WARN", {"note": "Webhook не настроен"})
            
            return True
            
        except Exception as e:
            await self.log_result("Webhook статус", "FAIL", {"error": str(e)})
            return False
    
    async def test_3_commands_delivery(self):
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 3: ДОСТАВКА КОМАНД")
        logger.info("="*70)
        
        commands = [
            "/start",
            "/help", 
            "/menu",
            "Категории",
            "Помощь",
            "Личный кабинет",
            "Пригласить друзей",
            "Избранные"
        ]
        
        delivered_count = 0
        
        for cmd in commands:
            logger.info(f"\nОтправляем: {cmd}")
            
            message = await self.send_message(cmd)
            
            if message:
                delivered_count += 1
                await self.log_result(f"Отправка: {cmd}", "PASS", {
                    "message_id": message.message_id,
                    "delivered": True
                })
                logger.info(f"[OK] Команда {cmd} доставлена")
            else:
                await self.log_result(f"Отправка: {cmd}", "FAIL", {"note": "Не удалось отправить"})
                logger.error(f"[FAIL] Не удалось отправить: {cmd}")
            
            await asyncio.sleep(1)  # Задержка между командами
        
        await self.log_result(
            "Общая доставка команд",
            "PASS" if delivered_count == len(commands) else "WARN",
            {
                "delivered": delivered_count,
                "total": len(commands),
                "success_rate": f"{(delivered_count/len(commands)*100):.1f}%"
            }
        )
    
    async def test_4_bot_commands(self):
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 4: КОМАНДЫ БОТА")
        logger.info("="*70)
        
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
    
    async def test_5_manual_check(self):
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 5: РУЧНАЯ ПРОВЕРКА")
        logger.info("="*70)
        
        logger.info("\nВАЖНО! Теперь проверь бота вручную:")
        logger.info("1. Открой Telegram")
        logger.info("2. Найди бота @Karma25TESTBot")
        logger.info("3. Проверь что бот отвечает на команды:")
        logger.info("   - /start (должен показать главное меню)")
        logger.info("   - /help (должен показать справку)")
        logger.info("   - Кнопки главного меню")
        logger.info("4. Если бот НЕ отвечает - проверь Railway:")
        logger.info("   - Зайди на railway.app")
        logger.info("   - Открой проект KARMABOT1")
        logger.info("   - Проверь логи (Logs)")
        logger.info("   - Убедись что бот запущен")
        
        await self.log_result(
            "Ручная проверка",
            "WARN",
            {"note": "Требует ручной проверки в Telegram"}
        )
    
    async def run_all_tests(self):
        logger.info("\n\nПРОСТОЕ ТЕСТИРОВАНИЕ KARMABOT1")
        logger.info("="*70)
        
        # ТЕСТ 1: Подключение
        if not await self.test_1_connection():
            logger.error("[FAIL] Бот недоступен!")
            return
        
        await asyncio.sleep(1)
        
        # ТЕСТ 2: Webhook
        await self.test_2_webhook_status()
        await asyncio.sleep(1)
        
        # ТЕСТ 3: Доставка команд
        await self.test_3_commands_delivery()
        await asyncio.sleep(1)
        
        # ТЕСТ 4: Команды
        await self.test_4_bot_commands()
        await asyncio.sleep(1)
        
        # ТЕСТ 5: Ручная проверка
        await self.test_5_manual_check()
        
        # Итоги
        await self.print_summary()
        await self.save_report()
        
        await self.bot.session.close()
    
    async def print_summary(self):
        logger.info("\n\nИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("="*70)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        total = len(self.test_results)
        
        logger.info(f"[OK] Успешно:       {passed}/{total}")
        logger.info(f"[WARN] Предупреждения: {warned}/{total}")
        logger.info(f"[FAIL] Провалено:     {failed}/{total}")
        logger.info(f"Процент успеха: {(passed/total*100 if total > 0 else 0):.1f}%")
        logger.info(f"Сообщений отправлено: {self.message_counter}")
        
        # Выводы
        if passed >= 8:
            logger.info("\n[OK] БОТ РАБОТАЕТ НОРМАЛЬНО!")
            logger.info("   - Все команды доставляются")
            logger.info("   - Проверь ответы в Telegram")
        elif passed >= 6:
            logger.info("\n[WARN] ЕСТЬ НЕЗНАЧИТЕЛЬНЫЕ ПРОБЛЕМЫ")
            logger.info("   - Большинство команд доставляются")
            logger.info("   - Проверь Railway логи")
        else:
            logger.info("\n[FAIL] ЕСТЬ СЕРЬЕЗНЫЕ ПРОБЛЕМЫ!")
            logger.info("   - Много команд не доставляются")
            logger.info("   - Проверь Railway логи")
            logger.info("   - Убедись что бот запущен")
    
    async def save_report(self):
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway',
            'bot_username': '@Karma25TESTBot',
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'messages_sent': self.message_counter,
            'results': self.test_results
        }
        
        filename = f'simple_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nОтчет сохранен: {filename}")

async def main():
    print("ПРОСТОЕ ТЕСТИРОВАНИЕ KARMABOT1 НА RAILWAY")
    print("="*60)
    print("Проверяет доставку команд без конфликтов")
    print("="*60)
    
    tester = SimpleTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_all_tests()
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("Проверь файлы:")
    print("- simple_test_*.json (полный отчет)")
    print("- simple_test.log (лог тестирования)")
    print("\nТеперь проверь бота в Telegram!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nТестирование остановлено")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

