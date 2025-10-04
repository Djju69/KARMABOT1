#!/usr/bin/env python3
"""
ПОЛНЫЙ ТЕСТИРОВЩИК KARMABOT1 
Использует метод long polling для получения РЕАЛЬНЫХ ответов
"""

import asyncio
import logging
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from collections import defaultdict

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8363530491:AAEzRHLzbIyNk3ZvjMvXYnar-6Z7kG9L0k8"
TEST_USER_ID = 6391215556  # Твой Telegram ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_bot_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FullBotTester:
    """Полноценный тестировщик с получением реальных ответов"""
    
    def __init__(self, token: str, user_id: int):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.user_id = user_id
        self.test_results = []
        self.received_messages = []
        self.waiting_for_response = False
        self.current_test = None
        
        # Регистрируем обработчики
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков для получения ответов"""
        
        @self.dp.message()
        async def catch_all_messages(message: types.Message):
            """Ловим ВСЕ сообщения от бота"""
            if message.chat.id == self.user_id:
                logger.info(f"Получено сообщение от бота")
                self.received_messages.append(message)
    
    async def log_result(self, test_name: str, status: str, details: dict = None):
        """Логирование результата"""
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
                if isinstance(value, list) and len(value) > 5:
                    logger.info(f"   - {key}: [{len(value)} элементов]")
                else:
                    logger.info(f"   - {key}: {value}")
    
    async def send_and_wait(self, text: str, wait_time: int = 5):
        """Отправить сообщение и дождаться ответа"""
        # Очищаем буфер
        self.received_messages.clear()
        
        # Отправляем сообщение
        await self.bot.send_message(self.user_id, text)
        logger.info(f"Отправлено: {text}")
        
        # Ждем ответ
        for i in range(wait_time * 2):  # Проверяем каждые 0.5 сек
            await asyncio.sleep(0.5)
            if self.received_messages:
                return self.received_messages[-1]  # Возвращаем последнее сообщение
        
        return None
    
    async def test_1_connection(self):
        """ТЕСТ 1: Подключение"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 1: ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БОТУ")
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
            await self.log_result("Подключение к боту", "FAIL", {"error": str(e)})
            return False
    
    async def test_2_webhook_status(self):
        """ТЕСТ 2: Проверка webhook"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 2: ОТКЛЮЧЕНИЕ WEBHOOK ДЛЯ ТЕСТИРОВАНИЯ")
        logger.info("="*70)
        
        try:
            # Удаляем webhook чтобы использовать long polling
            await self.bot.delete_webhook(drop_pending_updates=True)
            logger.info("[OK] Webhook отключен - используем long polling")
            await self.log_result("Отключение webhook", "PASS", {})
            return True
        except Exception as e:
            await self.log_result("Отключение webhook", "WARN", {"error": str(e)})
            return True  # Продолжаем даже если ошибка
    
    async def test_3_start_command(self):
        """ТЕСТ 3: Команда /start"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 3: КОМАНДА /START")
        logger.info("="*70)
        
        try:
            response = await self.send_and_wait("/start", wait_time=8)
            
            if not response:
                await self.log_result(
                    "Команда /start",
                    "FAIL",
                    {"error": "Нет ответа от бота. Возможно бот не запущен на Railway"}
                )
                return None
            
            text = response.text or response.caption or ""
            has_keyboard = response.reply_markup is not None
            
            keyboard_info = "НЕТ"
            buttons_count = 0
            buttons_list = []
            
            if has_keyboard:
                if hasattr(response.reply_markup, 'keyboard'):
                    keyboard_info = "Reply Keyboard"
                    for row in response.reply_markup.keyboard:
                        for btn in row:
                            buttons_list.append(btn.text)
                            buttons_count += 1
                elif hasattr(response.reply_markup, 'inline_keyboard'):
                    keyboard_info = "Inline Keyboard"
                    for row in response.reply_markup.inline_keyboard:
                        for btn in row:
                            buttons_list.append(btn.text)
                            buttons_count += 1
            
            await self.log_result(
                "Команда /start",
                "PASS",
                {
                    "response_length": len(text),
                    "has_keyboard": has_keyboard,
                    "keyboard_type": keyboard_info,
                    "buttons_count": buttons_count,
                    "buttons": buttons_list,
                    "text_preview": text[:150] + "..." if len(text) > 150 else text
                }
            )
            
            return response
            
        except Exception as e:
            await self.log_result("Команда /start", "FAIL", {"error": str(e)})
            return None
    
    async def test_4_main_menu(self, start_response):
        """ТЕСТ 4: Главное меню"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 4: ПРОВЕРКА ГЛАВНОГО МЕНЮ")
        logger.info("="*70)
        
        expected_menus = {
            'user': ["🗂️ Категории", "👥 Пригласить друзей", "⭐ Избранные", "❓ Помощь", "👤 Личный кабинет"],
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
        
        # Определяем роль
        role = "unknown"
        expected = []
        for role_name, buttons in expected_menus.items():
            if all(btn in found_buttons for btn in buttons[:2]):
                role = role_name
                expected = buttons
                break
        
        missing = [btn for btn in expected if btn not in found_buttons]
        extra = [btn for btn in found_buttons if btn not in expected]
        
        status = "PASS" if not missing else "WARN"
        await self.log_result(
            f"Главное меню ({role})",
            status,
            {
                "found_count": len(found_buttons),
                "expected_count": len(expected),
                "missing": missing if missing else "нет",
                "extra": extra if extra else "нет",
                "all_buttons": found_buttons
            }
        )
        
        return found_buttons
    
    async def test_5_each_button(self, buttons: list):
        """ТЕСТ 5: Каждая кнопка отдельно"""
        logger.info("\n" + "="*70)
        logger.info(f"ТЕСТ 5: ПРОВЕРКА КАЖДОЙ КНОПКИ ({len(buttons)} кнопок)")
        logger.info("="*70)
        
        for i, button_text in enumerate(buttons, 1):
            logger.info(f"\n{'─'*70}")
            logger.info(f"[{i}/{len(buttons)}] Тестируем: {button_text}")
            logger.info('─'*70)
            
            try:
                response = await self.send_and_wait(button_text, wait_time=8)
                
                if not response:
                    await self.log_result(
                        f"Кнопка: {button_text}",
                        "FAIL",
                        {"error": "Нет ответа"}
                    )
                    continue
                
                text = response.text or response.caption or "Медиа"
                has_inline = response.reply_markup is not None
                
                next_actions = []
                if has_inline and hasattr(response.reply_markup, 'inline_keyboard'):
                    for row in response.reply_markup.inline_keyboard:
                        for btn in row:
                            next_actions.append({
                                'text': btn.text,
                                'callback': getattr(btn, 'callback_data', None),
                                'url': getattr(btn, 'url', None),
                                'webapp': getattr(btn, 'web_app', None) is not None
                            })
                
                await self.log_result(
                    f"Кнопка: {button_text}",
                    "PASS",
                    {
                        "response_preview": text[:100] + "..." if len(text) > 100 else text,
                        "response_length": len(text),
                        "has_inline_keyboard": has_inline,
                        "next_actions_count": len(next_actions),
                        "next_actions": [a['text'] for a in next_actions]
                    }
                )
                
                # Задержка между кнопками
                await asyncio.sleep(2)
                
            except Exception as e:
                await self.log_result(f"Кнопка: {button_text}", "FAIL", {"error": str(e)})
    
    async def test_6_commands(self):
        """ТЕСТ 6: Все команды"""
        logger.info("\n" + "="*70)
        logger.info("ТЕСТ 6: ПРОВЕРКА ВСЕХ КОМАНД")
        logger.info("="*70)
        
        commands = ["/help", "/moderate", "/mod_stats", "/add_card", "/my_cards", "/webapp"]
        
        for cmd in commands:
            try:
                response = await self.send_and_wait(cmd, wait_time=6)
                
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
                        {"note": "Нет ответа или команда недоступна для вашей роли"}
                    )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                await self.log_result(f"Команда: {cmd}", "FAIL", {"error": str(e)})
    
    async def run_tests(self):
        """Запуск всех тестов с polling"""
        logger.info("\n\n" + "="*35)
        logger.info("ПОЛНОЕ ТЕСТИРОВАНИЕ KARMABOT1 НА RAILWAY")
        logger.info("="*35 + "\n")
        
        # Запускаем polling в фоне
        polling_task = asyncio.create_task(self.dp.start_polling(self.bot))
        
        try:
            # Даем время на запуск polling
            await asyncio.sleep(2)
            
            # ТЕСТ 1
            if not await self.test_1_connection():
                return
            
            # ТЕСТ 2
            await self.test_2_webhook_status()
            await asyncio.sleep(2)
            
            # ТЕСТ 3
            start_msg = await self.test_3_start_command()
            if not start_msg:
                logger.error("[FAIL] Бот не отвечает! Проверь Railway логи")
                return
            
            await asyncio.sleep(2)
            
            # ТЕСТ 4
            buttons = await self.test_4_main_menu(start_msg)
            await asyncio.sleep(2)
            
            # ТЕСТ 5
            if buttons:
                await self.test_5_each_button(buttons)
            
            # ТЕСТ 6
            await self.test_6_commands()
            
            # Итоги
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
        logger.info(f"Процент успеха: {(passed/total*100 if total > 0 else 0):.1f}%\n")
    
    async def save_report(self):
        """Сохранение отчета"""
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway',
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'results': self.test_results
        }
        
        filename = f'full_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Полный отчет: {filename}")

async def main():
    print("ПОЛНЫЙ ТЕСТИРОВЩИК KARMABOT1 С РЕАЛЬНЫМИ ОТВЕТАМИ")
    print("="*60)
    print("Использует long polling для получения всех ответов бота")
    print("="*60)
    
    if BOT_TOKEN == "ВСТАВЬ_СЮДА_BOT_TOKEN":
        logger.error("[FAIL] Укажи BOT_TOKEN в файле!")
        return
    
    tester = FullBotTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_tests()
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nОстановлено")