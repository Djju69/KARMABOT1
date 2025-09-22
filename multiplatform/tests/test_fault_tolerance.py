"""
Тесты отказоустойчивости мульти-платформенной системы
"""
import sys
import os
import time

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.fault_tolerant_service import fault_tolerant_db

class TestFaultTolerance:
    """Тесты отказоустойчивости"""
    
    def __init__(self):
        self.test_user_id = 999999999
        self.test_user_data = {
            'username': 'test_user',
            'first_name': 'Test User'
        }
        print("🔧 Setting up test environment...")
    
    def test_system_initialization(self):
        """Тест инициализации отказоустойчивой системы"""
        assert fault_tolerant_db is not None
        status = fault_tolerant_db.get_system_status()
        assert 'health' in status
        assert 'mode' in status
        print(f"✅ System initialized with mode: {status['mode']}")
    
    def test_health_monitoring(self):
        """Тест мониторинга здоровья БД"""
        health_status = fault_tolerant_db.health_monitor.get_health_status()
        assert 'postgresql' in health_status
        assert 'supabase' in health_status
        assert 'overall' in health_status
        print(f"✅ Health monitoring: PostgreSQL={health_status['postgresql']['status']}, Supabase={health_status['supabase']['status']}")
    
    def test_user_creation_with_fallback(self):
        """Тест создания пользователя с отказоустойчивостью"""
        success = fault_tolerant_db.create_user_with_fallback(
            self.test_user_id,
            self.test_user_data,
            'telegram'
        )
        assert success
        
        # Проверяем, что пользователь создан
        user_info = fault_tolerant_db.get_user_with_fallback(self.test_user_id, 'telegram')
        assert user_info is not None
        print(f"✅ User created with fallback: {self.test_user_id}")
    
    def test_order_creation_with_fallback(self):
        """Тест создания заказа с отказоустойчивостью"""
        # Создаем пользователя
        fault_tolerant_db.create_user_with_fallback(self.test_user_id + 1, self.test_user_data, 'telegram')
        
        order_data = {
            'items': [{'name': 'Test Product', 'price': 100.0}],
            'total_amount': 100.0,
            'currency': 'USD'
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(self.test_user_id + 1, order_data, 'telegram')
        assert order_id is not None
        print(f"✅ Order created with fallback: {order_id}")
    
    def test_loyalty_info_with_fallback(self):
        """Тест получения лояльности с отказоустойчивостью"""
        loyalty_info = fault_tolerant_db.get_loyalty_with_fallback(self.test_user_id, 'telegram')
        assert loyalty_info is not None
        assert 'current_points' in loyalty_info
        assert 'source' in loyalty_info
        print(f"✅ Loyalty info retrieved: {loyalty_info['current_points']} points")
    
    def test_operation_queue(self):
        """Тест очереди операций"""
        queue_stats = fault_tolerant_db.operation_queue.get_queue_stats()
        assert 'total_operations' in queue_stats
        print(f"✅ Operation queue: {queue_stats['total_operations']} operations")
    
    def test_local_cache(self):
        """Тест локального кэша"""
        cache = fault_tolerant_db.local_cache
        
        # Тестируем базовые операции
        cache.set("test_key", {"test": "data"}, ttl=60)
        cached_data = cache.get("test_key")
        assert cached_data is not None
        assert cached_data['test'] == "data"
        
        # Тестируем пользовательские данные
        cache.set_user_data("test_user", "telegram", {"points": 100})
        user_cache = cache.get_user_data("test_user", "telegram")
        assert user_cache is not None
        assert user_cache['points'] == 100
        
        print("✅ Local cache works")
    
    def test_system_mode_detection(self):
        """Тест определения режима работы системы"""
        status = fault_tolerant_db.get_system_status()
        mode = status['mode']
        assert mode in ['FULL_OPERATIONAL', 'MAIN_DB_ONLY', 'LOYALTY_ONLY', 'CACHE_ONLY']
        print(f"✅ System mode detected: {mode}")
    
    def test_uptime_statistics(self):
        """Тест статистики uptime"""
        uptime_stats = fault_tolerant_db.health_monitor.get_uptime_stats()
        assert 'postgresql' in uptime_stats
        assert 'supabase' in uptime_stats
        assert 'overall' in uptime_stats
        print(f"✅ Uptime stats: PostgreSQL={uptime_stats['postgresql']}%, Supabase={uptime_stats['supabase']}%")

if __name__ == "__main__":
    test = TestFaultTolerance()
    print("🚀 Starting fault tolerance tests...\n")
    
    try:
        test.test_system_initialization()
        test.test_health_monitoring()
        test.test_user_creation_with_fallback()
        test.test_order_creation_with_fallback()
        test.test_loyalty_info_with_fallback()
        test.test_operation_queue()
        test.test_local_cache()
        test.test_system_mode_detection()
        test.test_uptime_statistics()
        
        print("\n🎉 All fault tolerance tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
