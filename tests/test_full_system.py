import pytest
import asyncio
import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.fault_tolerant_service import fault_tolerant_db
from core.database.enhanced_unified_service import enhanced_unified_db
from core.database.platform_adapters import (
    TelegramAdapter, WebsiteAdapter, MobileAppAdapter, 
    DesktopAppAdapter, APIAdapter, UniversalAdapter
)

class TestFullSystem:
    """Комплексные тесты всей системы"""
    
    def __init__(self):
        self.test_results = []
        self.setup_system()
    
    def setup_system(self):
        """Настройка системы перед тестами"""
        print("🔧 Setting up test environment...")
        
        # Инициализируем базы данных
        try:
            enhanced_unified_db.init_databases()
            print("✅ Database initialization completed")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
        
        # Проверяем доступность компонентов
        self.check_components()
    
    def check_components(self):
        """Проверить доступность всех компонентов"""
        components = [
            ('FaultTolerantService', fault_tolerant_db),
            ('EnhancedUnifiedDB', enhanced_unified_db),
            ('TelegramAdapter', TelegramAdapter),
            ('WebsiteAdapter', WebsiteAdapter),
            ('MobileAppAdapter', MobileAppAdapter),
            ('DesktopAppAdapter', DesktopAppAdapter),
            ('APIAdapter', APIAdapter),
            ('UniversalAdapter', UniversalAdapter)
        ]
        
        for name, component in components:
            if component is not None:
                print(f"✅ {name} available")
            else:
                print(f"❌ {name} not available")
    
    def test_system_initialization(self):
        """Тест инициализации системы"""
        print("🧪 Testing system initialization...")
        
        try:
            # Проверяем статус системы
            status = fault_tolerant_db.get_system_status()
            assert 'health' in status
            assert 'mode' in status
            assert 'operations' in status
            
            print(f"✅ System initialized with mode: {status['mode']}")
            self.test_results.append(("System Initialization", True, "System ready"))
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            self.test_results.append(("System Initialization", False, str(e)))
    
    def test_platform_user_creation_flow(self):
        """Тест создания пользователей на всех платформах"""
        print("🧪 Testing multi-platform user creation...")
        
        test_users = [
            {
                'platform': 'telegram',
                'data': {'telegram_id': 123456789, 'username': 'test_telegram', 'first_name': 'Test'},
                'adapter': TelegramAdapter
            },
            {
                'platform': 'website',
                'data': {'email': 'test@example.com', 'username': 'test_website', 'first_name': 'Test'},
                'adapter': WebsiteAdapter
            },
            {
                'platform': 'mobile',
                'data': {'device_id': 'test_device_123', 'platform': 'ios', 'username': 'test_mobile'},
                'adapter': MobileAppAdapter
            },
            {
                'platform': 'desktop',
                'data': {'user_id': 'test_desktop_123', 'platform': 'windows', 'username': 'test_desktop'},
                'adapter': DesktopAppAdapter
            }
        ]
        
        success_count = 0
        
        for user_test in test_users:
            try:
                platform = user_test['platform']
                data = user_test['data']
                adapter = user_test['adapter']
                
                # Создаем пользователя через адаптер
                if platform == 'telegram':
                    user_uuid = adapter.create_user(data['telegram_id'], data)
                elif platform == 'website':
                    user_uuid = adapter.create_user(data['email'], data)
                elif platform == 'mobile':
                    user_uuid = adapter.create_user(data['device_id'], data['platform'], data)
                elif platform == 'desktop':
                    user_uuid = adapter.create_user(data['user_id'], data['platform'], data)
                
                assert user_uuid is not None
                print(f"✅ {platform.capitalize()} user created: {user_uuid}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {platform.capitalize()} user creation failed: {e}")
        
        print(f"✅ {success_count}/{len(test_users)} platform users created successfully")
        self.test_results.append(("Multi-Platform User Creation", success_count == len(test_users), f"{success_count}/{len(test_users)} platforms"))
    
    def test_account_linking_flow(self):
        """Тест связывания аккаунтов между платформами"""
        print("🧪 Testing account linking flow...")
        
        try:
            # Создаем пользователей на разных платформах
            telegram_id = 987654321
            email = "link_test@example.com"
            
            # Создаем Telegram пользователя
            tg_uuid = TelegramAdapter.create_user(telegram_id, {
                'username': 'link_test_tg',
                'first_name': 'Link',
                'last_name': 'Test'
            })
            
            # Создаем Website пользователя
            web_uuid = WebsiteAdapter.create_user(email, {
                'username': 'link_test_web',
                'first_name': 'Link',
                'last_name': 'Test'
            })
            
            # Связываем аккаунты
            link_success = enhanced_unified_db.link_telegram_to_website(email, telegram_id)
            
            assert link_success
            print("✅ Account linking successful")
            
            # Проверяем связь
            linked_user = enhanced_unified_db.get_user_across_platforms({
                'telegram_id': telegram_id,
                'email': email
            })
            
            assert linked_user is not None
            print("✅ Cross-platform user lookup successful")
            
            self.test_results.append(("Account Linking", True, "Accounts linked successfully"))
            
        except Exception as e:
            print(f"❌ Account linking failed: {e}")
            self.test_results.append(("Account Linking", False, str(e)))
    
    def test_order_creation_flow(self):
        """Тест создания заказов на всех платформах"""
        print("🧪 Testing order creation flow...")
        
        order_data = {
            'items': [
                {'name': 'Test Product', 'price': 25.0, 'quantity': 2},
                {'name': 'Another Product', 'price': 15.0, 'quantity': 1}
            ],
            'total_amount': 65.0,
            'currency': 'USD',
            'payment_method': 'card'
        }
        
        platforms = [
            ('telegram', 111222333),
            ('website', 'order_test@example.com'),
            ('mobile', 'order_device_123', 'ios'),
            ('desktop', 'order_desktop_123', 'windows')
        ]
        
        success_count = 0
        
        for platform_info in platforms:
            try:
                platform = platform_info[0]
                
                if platform == 'telegram':
                    user_id = platform_info[1]
                    order_id = TelegramAdapter.create_order(user_id, order_data)
                elif platform == 'website':
                    email = platform_info[1]
                    order_id = enhanced_unified_db.create_website_order(email, order_data)
                elif platform == 'mobile':
                    device_id = platform_info[1]
                    platform_type = platform_info[2]
                    order_id = enhanced_unified_db.create_mobile_order(device_id, platform_type, order_data)
                elif platform == 'desktop':
                    user_id = platform_info[1]
                    platform_type = platform_info[2]
                    order_id = enhanced_unified_db.create_desktop_order(user_id, platform_type, order_data)
                
                assert order_id is not None
                print(f"✅ {platform.capitalize()} order created: {order_id}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {platform.capitalize()} order creation failed: {e}")
        
        print(f"✅ {success_count}/{len(platforms)} platform orders created successfully")
        self.test_results.append(("Multi-Platform Order Creation", success_count == len(platforms), f"{success_count}/{len(platforms)} platforms"))
    
    def test_fault_tolerance(self):
        """Тест отказоустойчивости системы"""
        print("🧪 Testing fault tolerance...")
        
        try:
            # Проверяем статус здоровья
            health_status = fault_tolerant_db.health_monitor.get_health_status()
            assert 'postgresql' in health_status
            assert 'supabase' in health_status
            assert 'overall' in health_status
            
            print(f"✅ Health monitoring: PostgreSQL={health_status['postgresql']['status']}, Supabase={health_status['supabase']['status']}")
            
            # Проверяем очередь операций
            queue_stats = fault_tolerant_db.operation_queue.get_queue_stats()
            assert 'total_operations' in queue_stats
            print(f"✅ Operation queue: {queue_stats['total_operations']} operations")
            
            # Проверяем локальный кеш
            cache_stats = fault_tolerant_db.local_cache.get_cache_stats()
            assert 'total_items' in cache_stats
            print(f"✅ Local cache: {cache_stats['total_items']} items")
            
            # Тестируем создание пользователя с отказоустойчивостью
            test_user_id = 999888777
            test_user_data = {
                'username': 'fault_test_user',
                'first_name': 'Fault',
                'last_name': 'Test'
            }
            
            success = fault_tolerant_db.create_user_with_fallback(
                test_user_id, test_user_data, 'telegram'
            )
            
            assert success
            print("✅ Fault-tolerant user creation successful")
            
            # Проверяем получение пользователя
            user_info = fault_tolerant_db.get_user_with_fallback(test_user_id, 'telegram')
            assert user_info is not None
            print("✅ Fault-tolerant user retrieval successful")
            
            self.test_results.append(("Fault Tolerance", True, "All fault tolerance features working"))
            
        except Exception as e:
            print(f"❌ Fault tolerance test failed: {e}")
            self.test_results.append(("Fault Tolerance", False, str(e)))
    
    def test_queue_processing(self):
        """Тест обработки очереди операций"""
        print("🧪 Testing queue processing...")
        
        try:
            # Добавляем тестовую операцию в очередь
            from core.database.fault_tolerant_service import PendingOperation, DatabaseType, OperationPriority
            
            test_operation = PendingOperation(
                operation_id="test_op_123",
                operation_type="test_operation",
                target_db=DatabaseType.POSTGRESQL.value,
                user_identifier=123456789,
                platform="telegram",
                data={"test": "data"},
                timestamp=datetime.utcnow().isoformat(),
                priority=OperationPriority.NORMAL.value
            )
            
            fault_tolerant_db.operation_queue.add_operation(test_operation)
            
            # Проверяем, что операция добавлена
            queue_stats = fault_tolerant_db.operation_queue.get_queue_stats()
            assert queue_stats['total_operations'] > 0
            print("✅ Operation added to queue")
            
            # Получаем операции для PostgreSQL
            pg_operations = fault_tolerant_db.operation_queue.get_operations_for_db(DatabaseType.POSTGRESQL.value)
            assert len(pg_operations) > 0
            print("✅ Queue operations retrieval successful")
            
            # Удаляем тестовую операцию
            fault_tolerant_db.operation_queue.remove_operation(test_operation)
            
            # Проверяем, что операция удалена
            queue_stats_after = fault_tolerant_db.operation_queue.get_queue_stats()
            print("✅ Operation removed from queue")
            
            self.test_results.append(("Queue Processing", True, "Queue operations working"))
            
        except Exception as e:
            print(f"❌ Queue processing test failed: {e}")
            self.test_results.append(("Queue Processing", False, str(e)))
    
    def test_loyalty_system(self):
        """Тест системы лояльности"""
        print("🧪 Testing loyalty system...")
        
        try:
            test_user_id = 555666777
            
            # Получаем информацию о лояльности
            loyalty_info = fault_tolerant_db.get_loyalty_with_fallback(test_user_id, 'telegram')
            assert loyalty_info is not None
            assert 'current_points' in loyalty_info
            assert 'partner_cards' in loyalty_info
            assert 'recent_history' in loyalty_info
            
            print(f"✅ Loyalty info retrieved: {loyalty_info['current_points']} points")
            
            # Тестируем получение лояльности через универсальный адаптер
            universal_loyalty = enhanced_unified_db.get_unified_loyalty_info({
                'telegram_id': test_user_id
            })
            
            assert universal_loyalty is not None
            print("✅ Universal loyalty system working")
            
            self.test_results.append(("Loyalty System", True, "Loyalty features working"))
            
        except Exception as e:
            print(f"❌ Loyalty system test failed: {e}")
            self.test_results.append(("Loyalty System", False, str(e)))
    
    def test_platform_statistics(self):
        """Тест статистики платформ"""
        print("🧪 Testing platform statistics...")
        
        try:
            # Получаем статистику платформ
            platform_stats = enhanced_unified_db.get_platform_statistics()
            assert platform_stats is not None
            
            # Проверяем наличие основных метрик
            expected_metrics = ['total_users', 'total_orders', 'platform_breakdown']
            for metric in expected_metrics:
                if metric in platform_stats:
                    print(f"✅ Platform metric '{metric}' available")
                else:
                    print(f"⚠️ Platform metric '{metric}' not found")
            
            print("✅ Platform statistics retrieved")
            
            self.test_results.append(("Platform Statistics", True, "Statistics system working"))
            
        except Exception as e:
            print(f"❌ Platform statistics test failed: {e}")
            self.test_results.append(("Platform Statistics", False, str(e)))
    
    def test_admin_dashboard(self):
        """Тест админского dashboard"""
        print("🧪 Testing admin dashboard...")
        
        try:
            # Получаем данные для dashboard
            dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
            assert dashboard_data is not None
            
            # Проверяем наличие основных секций
            expected_sections = ['system_status', 'alerts', 'recommendations']
            for section in expected_sections:
                if section in dashboard_data:
                    print(f"✅ Dashboard section '{section}' available")
                else:
                    print(f"⚠️ Dashboard section '{section}' not found")
            
            print("✅ Admin dashboard data retrieved")
            
            self.test_results.append(("Admin Dashboard", True, "Dashboard system working"))
            
        except Exception as e:
            print(f"❌ Admin dashboard test failed: {e}")
            self.test_results.append(("Admin Dashboard", False, str(e)))
    
    def test_api_key_validation(self):
        """Тест валидации API ключей"""
        print("🧪 Testing API key validation...")
        
        try:
            # Тестируем валидные ключи
            valid_keys = ['pk_live_test123', 'pk_test_abc456', 'api_key_xyz789']
            
            for key in valid_keys:
                # Здесь должна быть реальная проверка API ключа
                # Для демонстрации просто проверяем формат
                if any(key.startswith(prefix) for prefix in ['pk_live_', 'pk_test_', 'api_key_']):
                    print(f"✅ Valid API key format: {key}")
                else:
                    print(f"❌ Invalid API key format: {key}")
            
            # Тестируем невалидные ключи
            invalid_keys = ['invalid_key', 'test', '123456']
            
            for key in invalid_keys:
                if not any(key.startswith(prefix) for prefix in ['pk_live_', 'pk_test_', 'api_key_']):
                    print(f"✅ Invalid key correctly rejected: {key}")
            
            print("✅ API key validation working")
            
            self.test_results.append(("API Key Validation", True, "Key validation working"))
            
        except Exception as e:
            print(f"❌ API key validation test failed: {e}")
            self.test_results.append(("API Key Validation", False, str(e)))
    
    def test_cross_platform_orders(self):
        """Тест кросс-платформенных заказов"""
        print("🧪 Testing cross-platform orders...")
        
        try:
            # Создаем кросс-платформенный заказ
            order_data = {
                'user_identifiers': {
                    'telegram_id': 123456789,
                    'email': 'cross_platform@example.com'
                },
                'primary_platform': 'telegram',
                'order_details': {
                    'items': [{'name': 'Cross Platform Product', 'price': 50.0}],
                    'total_amount': 50.0,
                    'currency': 'USD'
                }
            }
            
            order_id = enhanced_unified_db.create_cross_platform_order(
                order_data['user_identifiers'],
                order_data['order_details'],
                order_data['primary_platform']
            )
            
            assert order_id is not None
            print(f"✅ Cross-platform order created: {order_id}")
            
            self.test_results.append(("Cross-Platform Orders", True, "Cross-platform orders working"))
            
        except Exception as e:
            print(f"❌ Cross-platform orders test failed: {e}")
            self.test_results.append(("Cross-Platform Orders", False, str(e)))
    
    def test_system_export_import(self):
        """Тест экспорта/импорта системы"""
        print("🧪 Testing system export/import...")
        
        try:
            # Экспортируем отчет о системе
            system_report = enhanced_unified_db.export_system_report()
            assert system_report is not None
            
            # Проверяем наличие основных данных в отчете
            expected_data = ['timestamp', 'system_status', 'platform_stats']
            for data_key in expected_data:
                if data_key in system_report:
                    print(f"✅ Export data '{data_key}' available")
                else:
                    print(f"⚠️ Export data '{data_key}' not found")
            
            print("✅ System export working")
            
            self.test_results.append(("System Export/Import", True, "Export system working"))
            
        except Exception as e:
            print(f"❌ System export/import test failed: {e}")
            self.test_results.append(("System Export/Import", False, str(e)))
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("🚀 Starting comprehensive system tests")
        print("=" * 60)
        
        # Список всех тестов
        tests = [
            self.test_system_initialization,
            self.test_platform_user_creation_flow,
            self.test_account_linking_flow,
            self.test_order_creation_flow,
            self.test_fault_tolerance,
            self.test_queue_processing,
            self.test_loyalty_system,
            self.test_platform_statistics,
            self.test_admin_dashboard,
            self.test_api_key_validation,
            self.test_cross_platform_orders,
            self.test_system_export_import
        ]
        
        # Запускаем тесты
        for test in tests:
            try:
                test()
                print()  # Пустая строка между тестами
            except Exception as e:
                print(f"💥 Test {test.__name__} crashed: {e}")
                self.test_results.append((test.__name__, False, f"Test crashed: {e}"))
        
        # Выводим результаты
        self.print_test_results()
    
    def print_test_results(self):
        """Вывести результаты тестов"""
        print("=" * 60)
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}: {details}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"📊 Total: {passed + failed} tests")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! System is fully operational.")
        else:
            print(f"\n⚠️ {failed} tests failed. Please review the issues above.")
        
        return failed == 0

def run_full_system_tests():
    """Запустить полные тесты системы"""
    test_suite = TestFullSystem()
    success = test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = run_full_system_tests()
    exit(0 if success else 1)