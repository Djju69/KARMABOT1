"""
Комплексное тестирование системы KARMABOT1
Проверяет все основные компоненты и интеграции
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.getcwd())

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemTester:
    """Комплексный тестер системы"""
    
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Запустить все тесты"""
        logger.info("🧪 Начинаем комплексное тестирование системы...")
        
        # Тестируем основные компоненты
        await self.test_database_connection()
        await self.test_loyalty_system()
        await self.test_analytics()
        await self.test_performance()
        await self.test_notifications()
        await self.test_webapp_integration()
        await self.test_user_management()
        await self.test_partner_system()
        await self.test_admin_functions()
        
        # Генерируем отчет
        return self.generate_report()
    
    async def test_database_connection(self):
        """Тест подключения к базе данных"""
        logger.info("🗄️ Тестируем подключение к БД...")
        
        try:
            from core.database.db_adapter import db_v2
            
            # Тест получения пользователей
            users = await db_v2.get_all_users()
            self.record_test("database_users", True, f"Найдено {len(users)} пользователей")
            
            # Тест получения категорий
            categories = await db_v2.get_categories()
            self.record_test("database_categories", True, f"Найдено {len(categories)} категорий")
            
            # Тест получения партнеров
            partners = await db_v2.get_partners_by_status('approved')
            self.record_test("database_partners", True, f"Найдено {len(partners)} партнеров")
            
        except Exception as e:
            self.record_test("database_connection", False, f"Ошибка: {e}")
    
    async def test_loyalty_system(self):
        """Тест системы лояльности"""
        logger.info("💎 Тестируем систему лояльности...")
        
        try:
            from core.services.loyalty_service import loyalty_service
            
            # Тест получения баланса баллов
            test_user_id = 123456789
            balance = await loyalty_service.get_user_points_balance(test_user_id)
            self.record_test("loyalty_balance", True, f"Баланс пользователя: {balance} баллов")
            
            # Тест истории баллов
            history = await loyalty_service.get_points_history(test_user_id, limit=5)
            self.record_test("loyalty_history", True, f"История: {len(history)} записей")
            
        except Exception as e:
            self.record_test("loyalty_system", False, f"Ошибка: {e}")
    
    async def test_analytics(self):
        """Тест аналитики"""
        logger.info("📊 Тестируем аналитику...")
        
        try:
            from core.services.analytics_service import analytics_service
            
            # Тест метрик пользователей
            user_metrics = await analytics_service.get_user_metrics()
            self.record_test("analytics_users", True, f"Пользователей: {user_metrics.total_users}")
            
            # Тест метрик партнеров
            partner_metrics = await analytics_service.get_partner_metrics()
            self.record_test("analytics_partners", True, f"Партнеров: {partner_metrics.total_partners}")
            
            # Тест метрик транзакций
            transaction_metrics = await analytics_service.get_transaction_metrics()
            self.record_test("analytics_transactions", True, f"Транзакций: {transaction_metrics.total_transactions}")
            
        except Exception as e:
            self.record_test("analytics", False, f"Ошибка: {e}")
    
    async def test_performance(self):
        """Тест производительности"""
        logger.info("🚀 Тестируем производительность...")
        
        try:
            from core.services.performance_service import performance_service
            
            # Тест инициализации
            await performance_service.initialize()
            self.record_test("performance_init", True, "Сервис производительности инициализирован")
            
            # Тест статистики
            stats = await performance_service.get_performance_stats()
            self.record_test("performance_stats", True, f"Метрик: {len(stats.get('metrics', {}))}")
            
        except Exception as e:
            self.record_test("performance", False, f"Ошибка: {e}")
    
    async def test_notifications(self):
        """Тест уведомлений"""
        logger.info("📱 Тестируем уведомления...")
        
        try:
            from core.services.notification_service import notification_service, NotificationType
            
            # Тест отправки уведомления
            success = await notification_service.send_notification(
                user_id=123456789,
                title="Тестовое уведомление",
                message="Это тестовое уведомление для проверки системы",
                notification_type=NotificationType.INFO
            )
            self.record_test("notification_send", success, "Уведомление отправлено" if success else "Ошибка отправки")
            
            # Тест получения уведомлений
            notifications = await notification_service.get_user_notifications(123456789)
            self.record_test("notification_get", True, f"Уведомлений: {len(notifications)}")
            
        except Exception as e:
            self.record_test("notifications", False, f"Ошибка: {e}")
    
    async def test_webapp_integration(self):
        """Тест интеграции WebApp"""
        logger.info("🌐 Тестируем WebApp...")
        
        try:
            from core.services.webapp_integration import WebAppIntegration
            
            webapp = WebAppIntegration()
            
            # Тест создания URL
            url = webapp.create_webapp_url(
                telegram_id=123456789,
                role="user",
                webapp_path="/user-cabinet.html"
            )
            self.record_test("webapp_url", bool(url), f"URL создан: {bool(url)}")
            
        except Exception as e:
            self.record_test("webapp", False, f"Ошибка: {e}")
    
    async def test_user_management(self):
        """Тест управления пользователями"""
        logger.info("👥 Тестируем управление пользователями...")
        
        try:
            from core.services.user_service import get_user_role
            
            # Тест получения роли
            role = await get_user_role(123456789)
            self.record_test("user_role", True, f"Роль пользователя: {role}")
            
        except Exception as e:
            self.record_test("user_management", False, f"Ошибка: {e}")
    
    async def test_partner_system(self):
        """Тест системы партнеров"""
        logger.info("🤝 Тестируем систему партнеров...")
        
        try:
            from core.database.db_adapter import db_v2
            
            # Тест получения партнеров
            partners = await db_v2.get_partners_by_status('pending')
            self.record_test("partner_system", True, f"Партнеров на модерации: {len(partners)}")
            
        except Exception as e:
            self.record_test("partner_system", False, f"Ошибка: {e}")
    
    async def test_admin_functions(self):
        """Тест админских функций"""
        logger.info("👑 Тестируем админские функции...")
        
        try:
            from core.services.tariff_service import TariffService
            
            tariff_service = TariffService()
            tariffs = await tariff_service.get_all_tariffs()
            self.record_test("admin_tariffs", True, f"Тарифов: {len(tariffs)}")
            
        except Exception as e:
            self.record_test("admin_functions", False, f"Ошибка: {e}")
    
    def record_test(self, test_name: str, success: bool, message: str):
        """Записать результат теста"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            logger.error(f"❌ {test_name}: {message}")
        
        self.results[test_name] = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерировать отчет о тестировании"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'success_rate': round(success_rate, 2)
            },
            'results': self.results,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("📋 ОТЧЕТ О ТЕСТИРОВАНИИ:")
        logger.info(f"Всего тестов: {self.total_tests}")
        logger.info(f"Пройдено: {self.passed_tests}")
        logger.info(f"Провалено: {self.failed_tests}")
        logger.info(f"Успешность: {success_rate:.1f}%")
        
        return report


async def main():
    """Главная функция тестирования"""
    tester = SystemTester()
    report = await tester.run_all_tests()
    
    # Сохраняем отчет
    import json
    with open('test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info("📄 Отчет сохранен в test_report.json")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
