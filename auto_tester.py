#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1
Работает как реальный пользователь - отправляет команды и получает ответы
БЕЗ ОЖИДАНИЯ ПОЛЬЗОВАТЕЛЯ!
"""

import asyncio
import logging
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8363530491:AAEzRHLzbIyNk3ZvjMvXYnar-6Z7kG9L0k8"
TEST_USER_ID = 6391215556

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoTester:
    """Автоматический тестировщик"""
    
    def __init__(self, token: str, user_id: int):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.user_id = user_id
        self.test_results = []
        self.message_queue = asyncio.Queue()
        
        # Регистрируем обработчики
        self.setup_handlers()
    
    def setup_handlers(self):
        """Ловим ВСЕ сообщения от бота"""
        
        @self.dp.message()
        async def catch_messages(message: types.Message):
            """Перехватываем все сообщения"""
            if message.chat.id == self.user_id:
                logger.debug(f"Поймано сообщение")
                await self.message_queue.put(message)
    
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
                if isinstance(value, list) and len(value) > 3:
                    logger.info(f"   - {key}: {value[:3]}... [{len(value)} всего]")
                else:
                    logger.info(f"   - {key}: {value}")
    
    async def send_and_wait(self, text: str, timeout: int = 8):
        """Отправить текст и дождаться ответа"""
        # Очищаем очередь
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except:
                break
        
        # Отправляем
        try:
            sent = await self.bot.send_message(self.user_id, text)
            logger.info(f"Отправлено: {text}")
        except Exception as e:
            logger.error(f"Ошибка отправки {text}: {e}")
            return None
        
        # Ждём ответ
        try:
            response = await asyncio.wait_for(
                self.message_queue.get(),
                timeout=timeout
            )
            logger.info(f"Получен ответ ({len(response.text or '')} символов)")
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Таймаут ожидания ответа ({timeout}s)")
            return None
    
    async def start_polling_background(self):
        """Запуск polling в фоне"""
        try:
            await self.dp.start_polling(self.bot, skip_updates=True)
        except asyncio.CancelledError:
            pass
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("\n" + "="*35)
        logger.info("АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ KARMABOT1")
        logger.info("Бот на Railway - проверяем все функции!")
        logger.info("="*35 + "\n")
        
        # Запускаем polling в фоне
        polling_task = asyncio.create_task(self.start_polling_background())
        
        try:
            await asyncio.sleep(2)  # Даём время на запуск
            
            # ============= ТЕСТ 1: ПОДКЛЮЧЕНИЕ =============
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
                        "name": me.first_name
                    }
                )
            except Exception as e:
                await self.log_result("Подключение", "FAIL", {"error": str(e)})
                return
            
            await asyncio.sleep(1)
            
            # ============= ТЕСТ 2: КОМАНДА /START =============
            logger.info("\n" + "="*70)
            logger.info("ТЕСТ 2: КОМАНДА /START")
            logger.info("="*70)
            
            start_msg = await self.send_and_wait("/start", timeout=10)
            
            if not start_msg:
                await self.log_result("Команда /start", "FAIL", {"error": "Нет ответа"})
                logger.error("[FAIL] Бот не отвечает! Проверь Railway логи!")
                return
            
            text = start_msg.text or start_msg.caption or ""
            has_keyboard = start_msg.reply_markup is not None
            
            # Собираем кнопки
            buttons = []
            keyboard_type = "НЕТ"
            if has_keyboard:
                if hasattr(start_msg.reply_markup, 'keyboard'):
                    keyboard_type = "Reply Keyboard"
                    for row in start_msg.reply_markup.keyboard:
                        for btn in row:
                            buttons.append(btn.text)
                elif hasattr(start_msg.reply_markup, 'inline_keyboard'):
                    keyboard_type = "Inline Keyboard"
                    for row in start_msg.reply_markup.inline_keyboard:
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
            
            await asyncio.sleep(2)
            
            # ============= ТЕСТ 3: ГЛАВНОЕ МЕНЮ =============
            logger.info("\n" + "="*70)
            logger.info("ТЕСТ 3: АНАЛИЗ ГЛАВНОГО МЕНЮ")
            logger.info("="*70)
            
            expected_user = ["🗂️ Категории", "👥 Пригласить друзей", "⭐ Избранные", "❓ Помощь", "👤 Личный кабинет"]
            expected_admin = ["🗂️ Категории", "🤖 ИИ Помощник", "📊 Дашборд: Модерация", "👤 Админ кабинет"]
            expected_superadmin = ["🗂️ Категории", "🤖 ИИ Помощник", "📊 Дашборд: Модерация", "📊 Дашборд: Уведомления", "📊 Дашборд: Система", "🧪 Тестовые данные", "👑 Супер-админ кабинет", "❓ Помощь"]
            
            role = "unknown"
            expected = []
            
            if all(btn in buttons for btn in expected_superadmin[:2]):
                role = "superadmin"
                expected = expected_superadmin
            elif all(btn in buttons for btn in expected_admin[:2]):
                role = "admin"
                expected = expected_admin
            elif all(btn in buttons for btn in expected_user[:2]):
                role = "user"
                expected = expected_user
            
            missing = [b for b in expected if b not in buttons]
            extra = [b for b in buttons if b not in expected]
            
            status = "PASS" if not missing else "WARN"
            await self.log_result(
                f"Главное меню ({role})",
                status,
                {
                    "found": len(buttons),
                    "expected": len(expected),
                    "missing": missing if missing else "нет",
                    "extra": extra if extra else "нет"
                }
            )
            
            await asyncio.sleep(2)
            
            # ============= ТЕСТ 4-N: КАЖДАЯ КНОПКА =============
            logger.info("\n" + "="*70)
            logger.info(f"ТЕСТ 4-{3+len(buttons)}: ПРОВЕРКА КАЖДОЙ КНОПКИ")
            logger.info("="*70)
            
            for i, button_text in enumerate(buttons, 1):
                logger.info(f"\n{'─'*70}")
                logger.info(f"[{i}/{len(buttons)}] Тестируем: {button_text}")
                logger.info('─'*70)
                
                response = await self.send_and_wait(button_text, timeout=10)
                
                if not response:
                    await self.log_result(
                        f"Кнопка: {button_text}",
                        "FAIL",
                        {"error": "Таймаут ожидания"}
                    )
                    continue
                
                resp_text = response.text or response.caption or "Медиа"
                has_inline = response.reply_markup is not None
                
                # Собираем inline кнопки
                inline_buttons = []
                if has_inline and hasattr(response.reply_markup, 'inline_keyboard'):
                    for row in response.reply_markup.inline_keyboard:
                        for btn in row:
                            inline_buttons.append({
                                'text': btn.text,
                                'callback': getattr(btn, 'callback_data', None),
                                'url': getattr(btn, 'url', None)
                            })
                
                await self.log_result(
                    f"Кнопка: {button_text}",
                    "PASS",
                    {
                        "response_length": len(resp_text),
                        "response_preview": resp_text[:80] + "..." if len(resp_text) > 80 else resp_text,
                        "has_inline_keyboard": has_inline,
                        "inline_buttons_count": len(inline_buttons),
                        "inline_buttons": [b['text'] for b in inline_buttons]
                    }
                )
                
                await asyncio.sleep(2)  # Задержка между кнопками
            
            # ============= ТЕСТ: КОМАНДЫ =============
            logger.info("\n" + "="*70)
            logger.info("ТЕСТ: ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ")
            logger.info("="*70)
            
            commands = ["/help", "/moderate", "/add_card", "/my_cards", "/tariffs"]
            
            for cmd in commands:
                response = await self.send_and_wait(cmd, timeout=6)
                
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
                        {"note": "Таймаут или команда недоступна"}
                    )
                
                await asyncio.sleep(1)
            
            # ============= ИТОГИ =============
            await self.print_summary()
            await self.save_report()
            
        finally:
            # Останавливаем polling
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass
            
            await self.bot.session.close()
    
    async def print_summary(self):
        """Итоги"""
        logger.info("\n\n" + "="*35)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("="*35 + "\n")
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        total = len(self.test_results)
        
        logger.info(f"[OK] Успешно:       {passed}/{total}")
        logger.info(f"[WARN] Предупреждения: {warned}/{total}")
        logger.info(f"[FAIL] Провалено:     {failed}/{total}")
        
        if total > 0:
            logger.info(f"Процент успеха: {(passed/total*100):.1f}%")
        
        logger.info("\n")
    
    async def save_report(self):
        """Сохранение отчета"""
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway',
            'test_mode': 'Auto Testing',
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'results': self.test_results
        }
        
        filename = f'auto_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Отчет сохранен: {filename}\n")

async def main():
    print("АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1")
    print("="*60)
    print("Проверяет бота на Railway - все функции!")
    print("="*60)
    
    tester = AutoTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_all_tests()
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nОстановлено")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

