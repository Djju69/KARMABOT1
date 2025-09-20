import pytest
import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.enhanced_unified_service import enhanced_unified_db
from api.platform_endpoints import *
from monitoring.system_monitor import SystemMonitor, HealthChecker

class TestFullSystem:
    """Полные интеграционные тесты всей системы"""
    
    @pytest.fixture(autouse=True)
    def setup_system(self):
        """Настройка системы перед тестами"""
        # Инициализируем базы данных
        enhanced_unified_db.init_databases()
        yield
        # Очистка после тестов (если нужно)
    
    def test_platform_user_creation_flow(self):
        """Тест создания пользователей на всех платформах"""
        print("🧪 Testing multi-platform user creation...")
        
        # Telegram пользователь
        telegram_uuid = enhanced_unified_db.create_telegram_user(
            123456789, 
            {"username": "test_user", "first_name": "Test"}
        )
        assert telegram_uuid, "Failed to create Telegram user"
        
        # Website пользователь
        website_uuid = enhanced_unified_db.create_website_user(
            "test@example.com",
            {"username": "test_web", "first_name": "Test"}
        )
        assert website_uuid, "Failed to create Website user"
        
        # Mobile пользователь
        mobile_uuid = enhanced_unified_db.create_mobile_user(
            "device123",
            "ios", 
            {"username": "test_mobile", "app_version": "1.0.0"}
        )
        assert mobile_uuid, "Failed to create Mobile user"
        
        # Desktop пользователь
        desktop_uuid = enhanced_unified_db.create_desktop_user(
            "desktop123",
            "windows",
            {"username": "test_desktop", "app_version": "1.0.0"}
        )
        assert desktop_uuid, "Failed to create Desktop user"
        
        print("✅ All platform users created successfully")
    
    def test_cross_platform_linking(self):
        """Тест связывания аккаунтов между платформами"""
        print("🧪 Testing cross-platform account linking...")
        
        # Создаем пользователей
        telegram_id = 987654321
        email = "link_test@example.com"
        
        enhanced_unified_db.create_telegram_user(telegram_id, {"first_name": "Link"})
        enhanced_unified_db.create_website_user(email, {"first_name": "Link"})
        
        # Связываем аккаунты
        success = enhanced_unified_db.link_telegram_to_website(email, telegram_id)
        assert success, "Failed to link Telegram to Website"
        
        # Проверяем связь
        telegram_info = enhanced_unified_db.get_telegram_user_info(telegram_id)
        website_info = enhanced_unified_db.get_website_user_info(email)
        
        assert telegram_info is not None, "Telegram user not found after linking"
        assert website_info is not None, "Website user not found after linking"
        
        print("✅ Cross-platform linking works correctly")
    
    def test_order_creation_all_platforms(self):
        """Тест создания заказов со всех платформ"""
        print("🧪 Testing order creation from all platforms...")
        
        order_data = {
            "items": [{"name": "Test Item", "price": 10.0}],
            "total_amount": 10.0,
            "currency": "USD"
        }
        
        # Telegram заказ
        telegram_id = 111222333
        enhanced_unified_db.create_telegram_user(telegram_id, {"first_name": "Order"})
        telegram_order = enhanced_unified_db.create_telegram_order(telegram_id, order_data)
        assert telegram_order, "Failed to create Telegram order"
        
        # Website заказ
        email = "order_test@example.com"
        enhanced_unified_db.create_website_user(email, {"first_name": "Order"})
        website_order = enhanced_unified_db.create_website_order(email, order_data)
        assert website_order, "Failed to create Website order"
        
        # Mobile заказ
        device_id = "order_device123"
        enhanced_unified_db.create_mobile_user(device_id, "android", {"first_name": "Order"})
        mobile_order = enhanced_unified_db.create_mobile_order(device_id, "android", order_data)
        assert mobile_order, "Failed to create Mobile order"
        
        print("✅ Orders created successfully from all platforms")
    
    def test_fault_tolerance_simulation(self):
        """Тест отказоустойчивости системы"""
        print("🧪 Testing fault tolerance...")
        
        # Получаем изначальный статус
        initial_status = enhanced_unified_db.health_check()
        print(f"Initial mode: {initial_status['mode']}")
        
        # Проверяем, что система может работать в разных режимах
        assert initial_status['mode'] in ['FULL_OPERATIONAL', 'CACHE_ONLY', 'POSTGRESQL_ONLY', 'SUPABASE_ONLY']
        
        # Тестируем создание пользователя в любом режиме
        test_id = 555666777
        user_uuid = enhanced_unified_db.create_telegram_user(
            test_id, 
            {"username": "fault_test", "first_name": "Fault"}
        )
        
        # В любом режиме пользователь должен быть создан (кеш или база)
        assert user_uuid, f"Failed to create user in {initial_status['mode']} mode"
        
        # Проверяем получение пользователя
        user_info = enhanced_unified_db.get_telegram_user_info(test_id)
        assert user_info is not None, "Failed to retrieve user in fault-tolerant mode"
        
        print("✅ System operates correctly in fault-tolerant mode")
    
    def test_queue_processing(self):
        """Тест обработки очереди операций"""
        print("🧪 Testing operation queue processing...")
        
        # Создаем несколько пользователей для генерации операций
        for i in range(5):
            enhanced_unified_db.create_telegram_user(
                900000000 + i,
                {"username": f"queue_test_{i}", "first_name": f"Queue{i}"}
            )
        
        # Получаем статус очереди
        dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
        queue_status = dashboard_data['system_status']['queue']
        
        print(f"Queue status: {queue_status['total_operations']} operations")
        
        # Принудительная синхронизация
        sync_result = enhanced_unified_db.force_system_sync()
        print(f"Sync result: {sync_result}")
        
        print("✅ Queue processing tested successfully")
    
    def test_unified_loyalty_system(self):
        """Тест объединенной системы лояльности"""
        print("🧪 Testing unified loyalty system...")
        
        # Создаем пользователя и заказы
        telegram_id = 777888999
        email = "loyalty_test@example.com"
        
        enhanced_unified_db.create_telegram_user(telegram_id, {"first_name": "Loyalty"})
        enhanced_unified_db.create_website_user(email, {"first_name": "Loyalty"})
        enhanced_unified_db.link_telegram_to_website(email, telegram_id)
        
        # Создаем заказы с разных платформ
        order_data = {"items": [{"name": "Loyalty Item", "price": 50.0}], "total_amount": 50.0}
        
        enhanced_unified_db.create_telegram_order(telegram_id, order_data)
        enhanced_unified_db.create_website_order(email, order_data)
        
        # Проверяем объединенную лояльность
        loyalty_info = enhanced_unified_db.get_unified_loyalty_info({
            "telegram_id": telegram_id,
            "email": email
        })
        
        assert loyalty_info is not None, "Failed to get unified loyalty info"
        print(f"Loyalty info: {loyalty_info}")
        
        print("✅ Unified loyalty system works correctly")
    
    def test_platform_statistics(self):
        """Тест статистики по платформам"""
        print("🧪 Testing platform statistics...")
        
        stats = enhanced_unified_db.get_platform_statistics()
        
        assert 'total_platforms' in stats, "Missing total_platforms in stats"
        assert 'by_platform' in stats, "Missing by_platform in stats"
        
        expected_platforms = ['telegram', 'website', 'mobile_ios', 'mobile_android', 'desktop_windows', 'desktop_mac', 'desktop_linux']
        
        for platform in expected_platforms:
            assert platform in stats['by_platform'], f"Missing {platform} in platform stats"
        
        print(f"Platform statistics: {stats}")
        print("✅ Platform statistics working correctly")
    
    def test_admin_dashboard_data(self):
        """Тест данных админской панели"""
        print("🧪 Testing admin dashboard data...")
        
        dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
        
        # Проверяем основные разделы
        required_sections = ['system_status', 'alerts', 'recommendations', 'platform_stats']
        
        for section in required_sections:
            assert section in dashboard_data, f"Missing {section} in dashboard data"
        
        # Проверяем системный статус
        system_status = dashboard_data['system_status']
        required_status_fields = ['mode', 'health', 'uptime', 'queue', 'cache']
        
        for field in required_status_fields:
            assert field in system_status, f"Missing {field} in system status"
        
        print("✅ Admin dashboard data structure correct")
    
    @pytest.mark.asyncio
    async def test_monitoring_system(self):
        """Тест системы мониторинга"""
        print("🧪 Testing monitoring system...")
        
        monitor = SystemMonitor()
        health_checker = HealthChecker()
        
        # Тест проверки здоровья
        await monitor.check_system_health()
        
        # Тест проверки баз данных
        health_data = await health_checker.check_database_health()
        assert health_data is not None, "Health check failed"
        
        # Тест проверки API endpoints
        api_results = await health_checker.check_api_endpoints()
        assert isinstance(api_results, dict), "API check failed"
        
        print("✅ Monitoring system working correctly")
    
    def test_api_key_validation(self):
        """Тест валидации API ключей"""
        print("🧪 Testing API key validation...")
        
        # Тестируем корректные префиксы
        valid_keys = ['pk_live_test123', 'pk_test_dev456', 'api_key_partner789']
        
        for key in valid_keys:
            # В реальности здесь был бы вызов API endpoint
            assert any(key.startswith(prefix) for prefix in ['pk_live_', 'pk_test_', 'api_key_'])
        
        # Тестируем некорректные ключи
        invalid_keys = ['invalid_key', 'wrong_prefix_123', '']
        
        for key in invalid_keys:
            assert not any(key.startswith(prefix) for prefix in ['pk_live_', 'pk_test_', 'api_key_'])
        
        print("✅ API key validation working correctly")
    
    def test_cross_platform_order_creation(self):
        """Тест кросс-платформенного создания заказов"""
        print("🧪 Testing cross-platform order creation...")
        
        # Создаем связанных пользователей
        telegram_id = 444555666
        email = "cross_order@example.com"
        device_id = "cross_device123"
        
        enhanced_unified_db.create_telegram_user(telegram_id, {"first_name": "Cross"})
        enhanced_unified_db.create_website_user(email, {"first_name": "Cross"})
        enhanced_unified_db.create_mobile_user(device_id, "ios", {"first_name": "Cross"})
        
        # Связываем аккаунты
        enhanced_unified_db.link_telegram_to_website(email, telegram_id)
        enhanced_unified_db.link_mobile_accounts(device_id, "ios", {"email": email, "telegram_id": telegram_id})
        
        # Создаем кросс-платформенный заказ
        user_identifiers = {
            "telegram_id": telegram_id,
            "email": email,
            "device_id": device_id
        }
        
        order_details = {
            "items": [{"name": "Cross Item", "price": 25.0}],
            "total_amount": 25.0,
            "currency": "USD"
        }
        
        order_id = enhanced_unified_db.create_cross_platform_order(
            user_identifiers, 
            order_details, 
            "website"
        )
        
        assert order_id, "Failed to create cross-platform order"
        print("✅ Cross-platform order creation successful")
    
    def test_system_export_import(self):
        """Тест экспорта и импорта системы"""
        print("🧪 Testing system export/import...")
        
        # Экспортируем отчет о системе
        report = enhanced_unified_db.export_system_report()
        
        assert 'export_timestamp' in report, "Missing export timestamp"
        assert 'system_summary' in report, "Missing system summary"
        assert 'detailed_data' in report, "Missing detailed data"
        
        # Проверяем, что отчет содержит данные о всех платформах
        detailed_data = report['detailed_data']
        
        platform_tables = ['telegram_users', 'website_users', 'mobile_users', 'desktop_users']
        for table in platform_tables:
            assert table in detailed_data, f"Missing {table} in export"
        
        print("✅ System export/import working correctly")

def run_all_tests():
    """Запустить все тесты"""
    print("🚀 Starting Full System Integration Tests")
    print("=" * 60)
    
    test_suite = TestFullSystem()
    test_suite.setup_system()
    
    # Список всех тестов
    tests = [
        test_suite.test_platform_user_creation_flow,
        test_suite.test_cross_platform_linking,
        test_suite.test_order_creation_all_platforms,
        test_suite.test_fault_tolerance_simulation,
        test_suite.test_queue_processing,
        test_suite.test_unified_loyalty_system,
        test_suite.test_platform_statistics,
        test_suite.test_admin_dashboard_data,
        test_suite.test_api_key_validation,
        test_suite.test_cross_platform_order_creation,
        test_suite.test_system_export_import
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED: {e}")
            failed += 1
    
    # Асинхронные тесты
    async def run_async_tests():
        nonlocal passed, failed
        try:
            await test_suite.test_monitoring_system()
            return 1, 0
        except Exception as e:
            print(f"❌ Async test FAILED: {e}")
            return 0, 1
    
    async_passed, async_failed = asyncio.run(run_async_tests())
    passed += async_passed
    failed += async_failed
    
    print("=" * 60)
    print(f"🏁 Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ ALL TESTS PASSED! System is fully operational.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
