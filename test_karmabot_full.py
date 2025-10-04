#!/usr/bin/env python3
"""
ПОЛНЫЙ АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1
Работает когда webhook отключен (DISABLE_WEBHOOK=true)
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types

# Load .env file
try:
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    pass

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TEST_USER_ID = int(os.getenv("TEST_USER_ID", "0"))

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KarmaBotTester:
    """Полный тестировщик бота"""
    
    def __init__(self, token: str, user_id: int):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.user_id = user_id
        self.test_results = []
        self.message_queue = asyncio.Queue()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Перехват всех сообщений от бота"""
        @self.dp.message()
        async def catch_all(message: types.Message):
            if message.chat.id == self.user_id:
                await self.message_queue.put(message)
    
    async def log_result(self, name: str, status: str, details: dict = None):
        """Логирование результата теста"""
        result = {
            'test': name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        icons = {'PASS': '✅', 'FAIL': '❌', 'WARN': '⚠️'}
        logger.info(f"{icons[status]} {name}: {status}")
        if details:
            for key, value in details.items():
                if isinstance(value, list) and len(value) > 5:
                    logger.info(f"   └─ {key}: [{len(value)} элементов]")
                else:
                    logger.info(f"   └─ {key}: {value}")
    
    async def send_and_wait(self, text: str, timeout: int = 10):
        """Отправить команду и дождаться ответа"""
        # Очистка очереди
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except:
                break
        
        # Отправка
        await self.bot.send_message(self.user_id, text)
        logger.info(f"📤 Отправлено: {text}")
        
        # Ожидание ответа
        try:
            response = await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
            logger.info(f"📨 Получен ответ")
            return response
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Таймаут ({timeout}s)")
            return None
    
    async def test_1_connection(self):
        """ТЕСТ 1: Подключение к боту"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 1: ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БОТУ")
        logger.info("="*70)
        
        try:
            me = await self.bot.get_me()
            await self.log_result(
                "Подключение к боту",
                "PASS",
                {"username": f"@{me.username}", "name": me.first_name}
            )
            return True
        except Exception as e:
            await self.log_result("Подключение", "FAIL", {"error": str(e)})
            return False
    
    async def test_2_start_command(self):
        """ТЕСТ 2: Команда /start"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 2: КОМАНДА /START")
        logger.info("="*70)
        
        response = await self.send_and_wait("/start", timeout=10)
        
        if not response:
            await self.log_result("Команда /start", "FAIL", {"error": "Нет ответа от бота"})
            return None
        
        text = response.text or response.caption or ""
        has_keyboard = response.reply_markup is not None
        
        buttons = []
        keyboard_type = "НЕТ"
        
        if has_keyboard:
            if hasattr(response.reply_markup, 'keyboard'):
                keyboard_type = "Reply Keyboard"
                for row in response.reply_markup.keyboard:
                    for btn in row:
                        buttons.append(btn.text)
            elif hasattr(response.reply_markup, 'inline_keyboard'):
                keyboard_type = "Inline Keyboard"
                for row in response.reply_markup.inline_keyboard:
                    for btn in row:
                        buttons.append(btn.text)
        
        await self.log_result(
            "Команда /start",
            "PASS",
            {
                "text_length": len(text),
                "keyboard_type": keyboard_type,
                "buttons_count": len(buttons),
                "buttons": buttons,
                "text_preview": text[:100] + "..." if len(text) > 100 else text
            }
        )
        
        return response
    
    async def test_3_main_menu(self, start_response):
        """ТЕСТ 3: Проверка главного меню"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 3: АНАЛИЗ ГЛАВНОГО МЕНЮ")
        logger.info("="*70)
        
        expected_menus = {
            'user': ["🗂️ Категории", "👥 Пригласить друзей", "⭐ Избранные", "❓ Помощь", "👤 Личный кабинет"],
            'partner': ["🗂️ Категории", "👥 Пригласить друзей", "⭐ Избранные", "❓ Помощь", "👤 Личный кабинет"],
            'admin': ["🗂️ Категории", "🤖 ИИ Помощник", "📊 Дашборд: Модерация", "📊 Дашборд: Уведомления", "👤 Админ кабинет", "❓ Помощь"],
            'superadmin': ["🗂️ Категории", "🤖 ИИ Помощник", "📊 Дашборд: Модерация", "📊 Дашборд: Уведомления", "📊 Дашборд: Система", "🧪 Тестовые данные", "👑 Супер-админ кабинет", "❓ Помощь"]
        }
        
        if not start_response or not start_response.reply_markup:
            await self.log_result("Главное меню", "FAIL", {"error": "Нет клавиатуры"})
            return []
        
        found_buttons = []
        if hasattr(start_response.reply_markup, 'keyboard'):
            for row in start_response.reply_markup.keyboard:
                for button in row:
                    found_buttons.append(button.text)
        
        # Определение роли
        role = "unknown"
        expected = []
        for role_name, buttons in expected_menus.items():
            if all(btn in found_buttons for btn in buttons[:2]):
                role = role_name
                expected = buttons
                break
        
        missing = [b for b in expected if b not in found_buttons]
        extra = [b for b in found_buttons if b not in expected]
        
        status = "PASS" if not missing else "WARN"
        await self.log_result(
            f"Главное меню ({role})",
            status,
            {
                "found": len(found_buttons),
                "expected": len(expected),
                "missing": missing if missing else "нет",
                "extra": extra if extra else "нет",
                "all_buttons": found_buttons
            }
        )
        
        return found_buttons
    
    async def test_4_each_button(self, buttons: list):
        """ТЕСТ 4-N: Проверка каждой кнопки"""
        logger.info("\n" + "="*70)
        logger.info(f"ТЕСТЫ 4-{3+len(buttons)}: ПРОВЕРКА КАЖДОЙ КНОПКИ")
        logger.info("="*70)
        
        for i, button_text in enumerate(buttons, 1):
            logger.info(f"\n{'─'*70}")
            logger.info(f"[{i}/{len(buttons)}] Тестируем кнопку: {button_text}")
            logger.info('─'*70)
            
            response = await self.send_and_wait(button_text, timeout=12)
            
            if not response:
                await self.log_result(
                    f"Кнопка: {button_text}",
                    "FAIL",
                    {"error": "Нет ответа"}
                )
                continue
            
            text = response.text or response.caption or "Медиа"
            has_inline = response.reply_markup is not None
            
            # Собираем inline кнопки
            inline_buttons = []
            if has_inline and hasattr(response.reply_markup, 'inline_keyboard'):
                for row in response.reply_markup.inline_keyboard:
                    for btn in row:
                        inline_buttons.append({
                            'text': btn.text,
                            'callback': getattr(btn, 'callback_data', None),
                            'url': getattr(btn, 'url', None),
                            'webapp': getattr(btn, 'web_app', None) is not None
                        })
            
            await self.log_result(
                f"Кнопка: {button_text}",
                "PASS",
                {
                    "response_length": len(text),
                    "response_preview": text[:80] + "..." if len(text) > 80 else text,
                    "has_inline_keyboard": has_inline,
                    "inline_buttons_count": len(inline_buttons),
                    "inline_buttons": [b['text'] for b in inline_buttons]
                }
            )
            
            await asyncio.sleep(2)
    
    async def test_5_commands(self):
        """ТЕСТ: Дополнительные команды"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ: ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ")
        logger.info("="*70)
        
        commands = ["/help", "/moderate", "/mod_stats", "/add_card", "/my_cards", "/webapp"]
        
        for cmd in commands:
            response = await self.send_and_wait(cmd, timeout=8)
            
            if response:
                text = response.text or response.caption or ""
                await self.log_result(
                    f"Команда: {cmd}",
                    "PASS",
                    {"response_length": len(text)}
                )
            else:
                await self.log_result(
                    f"Команда: {cmd}",
                    "WARN",
                    {"note": "Нет ответа (возможно недоступна для роли)"}
                )
            
            await asyncio.sleep(1.5)
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("\n\n" + "🚀"*35)
        logger.info("ПОЛНОЕ АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ KARMABOT1")
        logger.info("🚀"*35 + "\n")
        
        # Запуск polling в фоне
        polling_task = asyncio.create_task(self.dp.start_polling(self.bot))
        
        try:
            await asyncio.sleep(2)
            
            # ТЕСТ 1
            if not await self.test_1_connection():
                logger.error("❌ Бот недоступен!")
                return
            
            await asyncio.sleep(2)
            
            # ТЕСТ 2
            start_msg = await self.test_2_start_command()
            if not start_msg:
                logger.error("❌ Бот не отвечает! Проверь что DISABLE_WEBHOOK=true на Railway")
                return
            
            await asyncio.sleep(2)
            
            # ТЕСТ 3
            buttons = await self.test_3_main_menu(start_msg)
            await asyncio.sleep(2)
            
            # ТЕСТ 4-N
            if buttons:
                await self.test_4_each_button(buttons)
            
            # ТЕСТ: Команды
            await self.test_5_commands()
            
            # Итоги
            await self.print_summary()
            await self.save_report()
            
        finally:
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass
            
            await self.bot.session.close()
    
    async def print_summary(self):
        """Вывод итогов"""
        logger.info("\n\n" + "📊"*35)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("📊"*35 + "\n")
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        total = len(self.test_results)
        
        logger.info(f"✅ Успешно:       {passed}/{total}")
        logger.info(f"⚠️  Предупреждения: {warned}/{total}")
        logger.info(f"❌ Провалено:     {failed}/{total}")
        
        if total > 0:
            success_rate = (passed / total * 100)
            logger.info(f"\n📈 Процент успеха: {success_rate:.1f}%")
            
            if success_rate >= 80:
                logger.info("🎉 БОТ РАБОТАЕТ ОТЛИЧНО!")
            elif success_rate >= 60:
                logger.info("⚠️  Бот работает, но есть проблемы")
            else:
                logger.info("❌ Много ошибок, требуется исправление")
        
        logger.info("\n")
    
    async def save_report(self):
        """Сохранение отчета"""
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway (webhook disabled)',
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'results': self.test_results
        }
        
        filename = f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Отчет сохранен: {filename}\n")

async def main():
    print("="*60)
    print("AUTOMATIC KARMABOT1 TESTER")
    print("="*60)
    print()
    
    if BOT_TOKEN == "":
        logger.error("ERROR: Set BOT_TOKEN in .env file!")
        logger.error("   Get it from @BotFather")
        return
    
    if TEST_USER_ID == 0:
        logger.warning("WARNING: Set TEST_USER_ID in .env file")
        logger.warning("   Get it from @userinfobot")
    
    logger.info("\nIMPORTANT: Before starting check:")
    logger.info("   1. Railway has DISABLE_WEBHOOK=true")
    logger.info("   2. Bot restarted (wait 1 minute)")
    logger.info("   3. Railway logs show 'TESTING MODE'\n")
    
    # Auto start after 3 seconds
    import time
    logger.info("Starting tests in 3 seconds...")
    time.sleep(3)
    
    tester = KarmaBotTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_all_tests()
    
    print("="*60)
    print("TESTING COMPLETED!")
    print("="*60)
    print()
    print("Check files:")
    print("- test_report_*.json  (full report)")
    print("- test_results.log    (detailed log)")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⛔ Тестирование остановлено")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
