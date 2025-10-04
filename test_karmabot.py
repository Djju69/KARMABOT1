#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1
Тестирует бота который работает на Railway
Проверяет ВСЕ кнопки и функции через Telegram Bot API
"""

import asyncio
import logging
import json
from datetime import datetime
from aiogram import Bot

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8363530491:AAEzRHLzbIyNk3ZvjMvXYnar-6Z7kG9L0k8"  # Токен бота от @BotFather
TEST_USER_ID = 6391215556  # Твой Telegram ID (получить у @userinfobot)

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
    """Класс для тестирования KARMABOT1 на Railway"""
    
    def __init__(self, token: str, user_id: int):
        self.bot = Bot(token=token)
        self.user_id = user_id
        self.test_results = []
        self.offset = 0
        
    async def log_result(self, test_name: str, status: str, details: dict = None):
        """Логирование результата теста"""
        result = {
            'test': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        icons = {'PASS': '✅', 'FAIL': '❌', 'WARN': '⚠️'}
        logger.info(f"{icons[status]} {test_name}: {status}")
        if details:
            for key, value in details.items():
                logger.info(f"   └─ {key}: {value}")
    
    async def get_updates(self, timeout=5):
        """Получить обновления от бота"""
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
        """Ждать ответ от бота"""
        await asyncio.sleep(2)  # Небольшая задержка
        
        for _ in range(wait_time):
            updates = await self.get_updates()
            
            for update in updates:
                if update.message and update.message.chat.id == self.user_id:
                    # Это ответ ОТ бота
                    if update.message.from_user.is_bot or update.message.from_user.id != self.user_id:
                        return update.message
            
            await asyncio.sleep(1)
        
        return None
    
    async def test_1_connection(self):
        """ТЕСТ 1: Проверка подключения к боту"""
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 1: Проверка что бот работает на Railway")
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
            logger.info("✅ Бот запущен и доступен!")
            return True
        except Exception as e:
            await self.log_result("Подключение к боту", "FAIL", {"error": str(e)})
            logger.error("❌ Бот недоступен! Проверь что он запущен на Railway")
            return False
    
    async def test_2_start_command(self):
        """ТЕСТ 2: Команда /start"""
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 2: Команда /start")
        logger.info("="*60)
        
        try:
            # Очищаем старые обновления
            await self.get_updates()
            
            # Отправляем /start
            await self.bot.send_message(self.user_id, "/start")
            logger.info("📤 Отправлена команда /start...")
            
            # Ждем ответ
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
                    {"note": "Нет ответа от бота. Проверь логи Railway!"}
                )
                return None
                
        except Exception as e:
            await self.log_result("Команда /start", "FAIL", {"error": str(e)})
            return None
    
    async def test_3_main_menu(self, last_message):
        """ТЕСТ 3: Проверка кнопок главного меню"""
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 3: Проверка главного меню")
        logger.info("="*60)
        
        expected_menus = {
            'user': [
                "🗂️ Категории",
                "👥 Пригласить друзей",
                "⭐ Избранные",
                "❓ Помощь",
                "👤 Личный кабинет"
            ],
            'partner': [
                "🗂️ Категории",
                "👥 Пригласить друзей",
                "⭐ Избранные",
                "❓ Помощь",
                "👤 Личный кабинет"
            ],
            'admin': [
                "🗂️ Категории",
                "🤖 ИИ Помощник",
                "📊 Дашборд: Модерация",
                "📊 Дашборд: Уведомления",
                "👤 Админ кабинет",
                "❓ Помощь"
            ],
            'superadmin': [
                "🗂️ Категории",
                "🤖 ИИ Помощник",
                "📊 Дашборд: Модерация",
                "📊 Дашборд: Уведомления",
                "📊 Дашборд: Система",
                "🧪 Тестовые данные",
                "👑 Супер-админ кабинет",
                "❓ Помощь"
            ]
        }
        
        try:
            if not last_message or not last_message.reply_markup:
                await self.log_result("Главное меню", "FAIL", {"note": "Нет клавиатуры в ответе"})
                return []
            
            found_buttons = []
            if hasattr(last_message.reply_markup, 'keyboard'):
                for row in last_message.reply_markup.keyboard:
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
                    "found": len(found_buttons),
                    "expected": len(expected),
                    "missing": missing if missing else "нет",
                    "extra": extra if extra else "нет",
                    "all_buttons": found_buttons
                }
            )
            
            return found_buttons
            
        except Exception as e:
            await self.log_result("Главное меню", "FAIL", {"error": str(e)})
            return []
    
    async def test_4_button_click(self, button_text: str):
        """ТЕСТ 4+: Нажатие на кнопку"""
        logger.info(f"\n{'─'*60}")
        logger.info(f"Тестируем кнопку: {button_text}")
        logger.info('─'*60)
        
        try:
            # Очищаем обновления
            await self.get_updates()
            
            # Нажимаем кнопку
            await self.bot.send_message(self.user_id, button_text)
            logger.info(f"📤 Отправлено: {button_text}")
            
            # Ждем ответ
            msg = await self.wait_for_response(wait_time=10)
            
            if not msg:
                await self.log_result(f"Кнопка: {button_text}", "FAIL", {"note": "Нет ответа от бота"})
                return None
            
            response_text = msg.text or msg.caption or "Медиа без текста"
            has_inline = msg.reply_markup is not None
            
            # Собираем inline кнопки
            next_actions = []
            if has_inline and hasattr(msg.reply_markup, 'inline_keyboard'):
                for row in msg.reply_markup.inline_keyboard:
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
                    "response_preview": response_text[:80] + "..." if len(response_text) > 80 else response_text,
                    "has_inline_buttons": has_inline,
                    "next_actions_count": len(next_actions),
                    "next_actions": [a['text'] for a in next_actions]
                }
            )
            
            if next_actions:
                logger.info(f"   └─ Найдено {len(next_actions)} следующих действий")
            
            return next_actions
            
        except Exception as e:
            await self.log_result(f"Кнопка: {button_text}", "FAIL", {"error": str(e)})
            return None
    
    async def test_5_all_commands(self):
        """ТЕСТ 5: Все команды бота"""
        logger.info("\n" + "="*60)
        logger.info("ТЕСТ 5: Проверка всех команд")
        logger.info("="*60)
        
        commands = [
            "/help",
            "/moderate",
            "/mod_stats",
            "/add_card",
            "/my_cards",
            "/webapp"
        ]
        
        for cmd in commands:
            try:
                await self.get_updates()
                await self.bot.send_message(self.user_id, cmd)
                logger.info(f"📤 Отправлена команда: {cmd}")
                
                msg = await self.wait_for_response(wait_time=8)
                
                if msg:
                    await self.log_result(f"Команда: {cmd}", "PASS", {"response": "получен"})
                else:
                    await self.log_result(f"Команда: {cmd}", "WARN", {"note": "нет ответа или команда недоступна"})
                    
            except Exception as e:
                await self.log_result(f"Команда: {cmd}", "FAIL", {"error": str(e)})
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("\n\n" + "🚀"*30)
        logger.info("ТЕСТИРОВАНИЕ KARMABOT1 НА RAILWAY")
        logger.info("🚀"*30 + "\n")
        
        # ТЕСТ 1: Подключение
        if not await self.test_1_connection():
            logger.error("❌ Бот не отвечает! Проверь Railway:")
            logger.error("   1. Зайди на railway.app")
            logger.error("   2. Открой свой проект KARMABOT1")
            logger.error("   3. Проверь логи (Logs)")
            logger.error("   4. Убедись что бот запущен (Deploy)")
            return
        
        await asyncio.sleep(2)
        
        logger.info("\n⚠️  ВАЖНО: Открой чат с ботом в Telegram!")
        logger.info("   Напиши боту /start вручную ОДИН РАЗ")
        logger.info("   Затем жди 5 секунд...\n")
        await asyncio.sleep(5)
        
        # ТЕСТ 2: /start
        last_msg = await self.test_2_start_command()
        
        if not last_msg:
            logger.error("❌ Бот не отвечает на команды!")
            logger.error("   Проверь логи на Railway - возможно там ошибка")
            return
        
        await asyncio.sleep(2)
        
        # ТЕСТ 3: Главное меню
        menu_buttons = await self.test_3_main_menu(last_msg)
        await asyncio.sleep(2)
        
        # ТЕСТ 4: Тестируем каждую кнопку
        if menu_buttons:
            for button in menu_buttons:
                await self.test_4_button_click(button)
                await asyncio.sleep(3)  # Задержка между кнопками
        
        # ТЕСТ 5: Все команды
        await self.test_5_all_commands()
        
        # Итоги
        await self.print_summary()
        await self.save_report()
        
        await self.bot.session.close()
    
    async def print_summary(self):
        """Вывод итогов"""
        logger.info("\n\n" + "📊"*30)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("📊"*30 + "\n")
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        total = len(self.test_results)
        
        logger.info(f"✅ Успешно:       {passed}/{total}")
        logger.info(f"⚠️  Предупреждения: {warned}/{total}")
        logger.info(f"❌ Провалено:     {failed}/{total}")
        logger.info(f"\n📈 Процент успеха: {(passed/total*100 if total > 0 else 0):.1f}%\n")
    
    async def save_report(self):
        """Сохранение отчета"""
        report = {
            'test_date': datetime.now().isoformat(),
            'platform': 'Railway',
            'bot_token': self.bot.token[:10] + "...",
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warned': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'results': self.test_results
        }
        
        filename = f'railway_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Отчет сохранен: {filename}")

async def main():
    """Главная функция"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║    АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК KARMABOT1 НА RAILWAY      ║
    ║                                                          ║
    ║  Проверяет бота который работает в облаке Railway.app   ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    if BOT_TOKEN == "ВСТАВЬ_СЮДА_BOT_TOKEN":
        logger.error("❌ Ошибка: Не указан BOT_TOKEN!")
        logger.error("📝 Найди токен:")
        logger.error("   1. Открой @BotFather в Telegram")
        logger.error("   2. Отправь /token")
        logger.error("   3. Выбери своего бота")
        logger.error("   4. Скопируй токен и вставь в этот файл")
        return
    
    if TEST_USER_ID == 123456789:
        logger.warning("⚠️  Используется тестовый USER_ID")
        logger.warning("📝 Получи свой ID:")
        logger.warning("   1. Открой @userinfobot в Telegram")
        logger.warning("   2. Нажми /start")
        logger.warning("   3. Скопируй свой ID")
    
    tester = KarmaBotTester(BOT_TOKEN, TEST_USER_ID)
    await tester.run_all_tests()
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                  ТЕСТИРОВАНИЕ ЗАВЕРШЕНО                  ║
    ║                                                          ║
    ║  Проверь файлы:                                          ║
    ║  - railway_test_report_*.json  (полный отчет)           ║
    ║  - bot_test.log               (лог тестирования)        ║
    ╚══════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⛔ Тестирование остановлено")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

