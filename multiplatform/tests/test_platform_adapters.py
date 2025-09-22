"""
Тесты платформенных адаптеров мульти-платформенной системы
"""
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.platform_adapters import (
    TelegramAdapter,
    WebsiteAdapter,
    MobileAppAdapter,
    DesktopAppAdapter,
    APIAdapter,
    UniversalAdapter
)
from database.enhanced_unified_service import enhanced_unified_db

class TestPlatformAdapters:
    """Тесты платформенных адаптеров"""
    
    def __init__(self):
        self.test_telegram_id = 123456789
        self.test_email = "test@example.com"
        self.test_device_id = "test_device_123"
        self.test_user_id = "test_user_456"
        self.test_api_key = "pk_test_123456"
        print("🔧 Setting up platform adapter tests...")
    
    def test_telegram_adapter(self):
        """Тест Telegram адаптера"""
        # Создание пользователя
        user_uuid = TelegramAdapter.create_user(self.test_telegram_id, {
            'username': 'test_user',
            'first_name': 'Test'
        })
        assert user_uuid is not None
        print(f"✅ Telegram user created: {user_uuid}")
        
        # Получение информации о пользователе
        user_info = TelegramAdapter.get_user_info(self.test_telegram_id)
        assert user_info is not None
        assert user_info['platform'] == 'telegram'
        print("✅ Telegram user info retrieved")
        
        # Создание заказа
        order_id = TelegramAdapter.create_order(self.test_telegram_id, {
            'items': [{'name': 'Test Product', 'price': 50.0}],
            'total_amount': 50.0
        })
        assert order_id is not None
        print(f"✅ Telegram order created: {order_id}")
        
        # Получение информации о лояльности
        loyalty_info = TelegramAdapter.get_loyalty_info(self.test_telegram_id)
        assert loyalty_info is not None
        print("✅ Telegram loyalty info retrieved")
    
    def test_website_adapter(self):
        """Тест Website адаптера"""
        # Создание пользователя
        user_uuid = WebsiteAdapter.create_user(self.test_email, {
            'username': 'test_user',
            'first_name': 'Test'
        })
        assert user_uuid is not None
        print(f"✅ Website user created: {user_uuid}")
        
        # Получение информации о пользователе
        user_info = WebsiteAdapter.get_user_info(self.test_email)
        assert user_info is not None
        assert user_info['platform'] == 'website'
        print("✅ Website user info retrieved")
        
        # Создание заказа
        order_id = WebsiteAdapter.create_order(self.test_email, {
            'items': [{'name': 'Test Product', 'price': 75.0}],
            'total_amount': 75.0
        })
        assert order_id is not None
        print(f"✅ Website order created: {order_id}")
    
    def test_mobile_adapter(self):
        """Тест Mobile адаптера"""
        # Создание пользователя iOS
        user_uuid = MobileAppAdapter.create_user(self.test_device_id, 'ios', {
            'username': 'test_user',
            'first_name': 'Test'
        })
        assert user_uuid is not None
        print(f"✅ Mobile iOS user created: {user_uuid}")
        
        # Получение информации о пользователе
        user_info = MobileAppAdapter.get_user_info(self.test_device_id, 'ios')
        assert user_info is not None
        assert user_info['platform'] == 'mobile_ios'
        print("✅ Mobile user info retrieved")
        
        # Синхронизация данных
        sync_result = MobileAppAdapter.sync_data(self.test_device_id, 'ios', {
            'preferences': {'theme': 'dark'},
            'last_sync': '2025-01-01T00:00:00Z'
        })
        assert sync_result['status'] == 'success'
        print("✅ Mobile data sync successful")
    
    def test_desktop_adapter(self):
        """Тест Desktop адаптера"""
        # Создание пользователя Windows
        user_uuid = DesktopAppAdapter.create_user(self.test_user_id, 'windows', {
            'username': 'test_user',
            'first_name': 'Test'
        })
        assert user_uuid is not None
        print(f"✅ Desktop Windows user created: {user_uuid}")
        
        # Получение информации о пользователе
        user_info = DesktopAppAdapter.get_user_info(self.test_user_id, 'windows')
        assert user_info is not None
        assert user_info['platform'] == 'desktop_windows'
        print("✅ Desktop user info retrieved")
    
    def test_api_adapter(self):
        """Тест API адаптера"""
        # Создание пользователя API
        user_uuid = APIAdapter.create_user(self.test_api_key, {
            'username': 'test_user',
            'first_name': 'Test'
        })
        assert user_uuid is not None
        print(f"✅ API user created: {user_uuid}")
        
        # Получение информации о пользователе
        user_info = APIAdapter.get_user_info(self.test_api_key)
        assert user_info is not None
        assert user_info['platform'] == 'api'
        print("✅ API user info retrieved")
    
    def test_universal_adapter(self):
        """Тест Universal адаптера"""
        # Связывание аккаунтов
        success = UniversalAdapter.link_accounts(
            self.test_telegram_id, 'telegram',
            self.test_email, 'website'
        )
        assert success
        print("✅ Account linking successful")
        
        # Поиск пользователя
        user_info = UniversalAdapter.find_user(self.test_telegram_id, 'telegram')
        assert user_info is not None
        print("✅ User found across platforms")
        
        # Синхронизация кросс-платформенных данных
        sync_result = UniversalAdapter.sync_cross_platform_data(
            self.test_telegram_id, 'telegram',
            {'preferences': {'notifications': True}}
        )
        assert sync_result['status'] == 'success'
        print("✅ Cross-platform sync successful")
    
    def test_enhanced_unified_service(self):
        """Тест расширенного единого сервиса"""
        # Тест создания пользователей на всех платформах
        telegram_uuid = enhanced_unified_db.create_telegram_user(self.test_telegram_id + 1, {
            'username': 'unified_test'
        })
        assert telegram_uuid is not None
        
        website_uuid = enhanced_unified_db.create_website_user(f"unified_{self.test_email}", {
            'username': 'unified_test'
        })
        assert website_uuid is not None
        
        mobile_uuid = enhanced_unified_db.create_mobile_user(f"unified_{self.test_device_id}", 'android', {
            'username': 'unified_test'
        })
        assert mobile_uuid is not None
        
        desktop_uuid = enhanced_unified_db.create_desktop_user(f"unified_{self.test_user_id}", 'mac', {
            'username': 'unified_test'
        })
        assert desktop_uuid is not None
        
        print("✅ All platform users created via unified service")
        
        # Тест статистики платформ
        platform_stats = enhanced_unified_db.get_platform_statistics()
        assert 'total_users' in platform_stats
        assert 'platform_breakdown' in platform_stats
        print("✅ Platform statistics retrieved")
        
        # Тест админ дашборда
        dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
        assert 'system_status' in dashboard_data
        assert 'platform_stats' in dashboard_data
        print("✅ Admin dashboard data retrieved")

if __name__ == "__main__":
    test = TestPlatformAdapters()
    print("🚀 Starting platform adapter tests...\n")
    
    try:
        test.test_telegram_adapter()
        test.test_website_adapter()
        test.test_mobile_adapter()
        test.test_desktop_adapter()
        test.test_api_adapter()
        test.test_universal_adapter()
        test.test_enhanced_unified_service()
        
        print("\n🎉 All platform adapter tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
