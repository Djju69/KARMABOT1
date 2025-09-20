import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.enhanced_unified_service import enhanced_unified_db
from core.database.platform_adapters import TelegramAdapter, WebsiteAdapter, MobileAppAdapter, UniversalAdapter

class TestPlatformAdapters:
    def __init__(self):
        self.test_telegram_id = 888888888
        self.test_email = "test@platform.com"
        self.test_device_id = "device_12345"
        self.test_user_data = {
            'username': 'platform_test',
            'first_name': 'Platform',
            'last_name': 'Tester'
        }
    
    def test_telegram_adapter(self):
        """Тест Telegram адаптера"""
        # Создание пользователя
        user_uuid = TelegramAdapter.create_user(self.test_telegram_id, self.test_user_data)
        assert user_uuid is not None
        
        # Получение информации
        user_info = TelegramAdapter.get_user_info(self.test_telegram_id)
        assert user_info is not None
        assert user_info['platform'] == 'telegram'
        assert user_info['is_bot_user'] == True
        
        # Создание заказа
        order_data = {'items': [{'name': 'Test', 'price': 100}], 'total_amount': 100}
        order_id = TelegramAdapter.create_order(self.test_telegram_id, order_data)
        assert order_id is not None
        
        # Получение лояльности
        loyalty = TelegramAdapter.get_loyalty_info(self.test_telegram_id)
        assert loyalty is not None
        assert 'current_points' in loyalty
        
        print("✅ Telegram adapter works")
    
    def test_website_adapter(self):
        """Тест Website адаптера"""
        # Создание пользователя
        user_uuid = WebsiteAdapter.create_user(self.test_email, self.test_user_data)
        assert user_uuid is not None
        
        # Получение информации
        user_info = WebsiteAdapter.get_user_info(self.test_email)
        assert user_info is not None
        assert user_info['platform'] == 'website'
        assert user_info['is_web_user'] == True
        
        # Создание заказа
        order_data = {'items': [{'name': 'Web Test', 'price': 200}], 'total_amount': 200}
        order_id = WebsiteAdapter.create_order(self.test_email, order_data)
        assert order_id is not None
        
        # Обновление профиля
        profile_update = {'last_name': 'Updated'}
        success = WebsiteAdapter.update_user_profile(self.test_email, profile_update)
        assert success
        
        print("✅ Website adapter works")
    
    def test_mobile_adapter(self):
        """Тест Mobile адаптера"""
        platform = 'mobile_ios'
        
        # Создание пользователя
        user_uuid = MobileAppAdapter.create_user(self.test_device_id, platform, self.test_user_data)
        assert user_uuid is not None
        
        # Получение информации
        user_info = MobileAppAdapter.get_user_info(self.test_device_id, platform)
        assert user_info is not None
        assert user_info['platform'] == platform
        assert user_info['is_mobile_user'] == True
        assert user_info['device_type'] == 'ios'
        
        # Синхронизация данных
        sync_data = {'app_version': '2.0.0', 'settings': {'notifications': True}}
        sync_result = MobileAppAdapter.sync_user_data(self.test_device_id, platform, sync_data)
        assert sync_result['status'] == 'synced'
        
        # Регистрация push токена
        push_success = MobileAppAdapter.register_push_token(self.test_device_id, platform, 'push_token_123')
        assert push_success
        
        print("✅ Mobile adapter works")
    
    def test_account_linking(self):
        """Тест связывания аккаунтов"""
        # Создаем пользователей на разных платформах
        TelegramAdapter.create_user(self.test_telegram_id + 10, self.test_user_data)
        WebsiteAdapter.create_user("link@test.com", self.test_user_data)
        
        # Связываем аккаунты
        link_success = WebsiteAdapter.link_telegram_account("link@test.com", self.test_telegram_id + 10)
        assert link_success
        
        # Проверяем связь
        linked_telegram = WebsiteAdapter.get_linked_telegram("link@test.com")
        assert linked_telegram == self.test_telegram_id + 10
        
        print("✅ Account linking works")
    
    def test_cross_platform_user_search(self):
        """Тест кросс-платформенного поиска"""
        # Создаем пользователей
        TelegramAdapter.create_user(self.test_telegram_id + 20, self.test_user_data)
        WebsiteAdapter.create_user("search@test.com", self.test_user_data)
        
        # Ищем по Telegram ID
        user_info = UniversalAdapter.get_user_across_platforms({'telegram_id': self.test_telegram_id + 20})
        assert user_info is not None
        assert user_info['found_via'] == 'telegram'
        
        # Ищем по email
        user_info = UniversalAdapter.get_user_across_platforms({'email': "search@test.com"})
        assert user_info is not None
        assert user_info['found_via'] == 'email'
        
        print("✅ Cross-platform user search works")
    
    def test_unified_loyalty_info(self):
        """Тест объединенной информации о лояльности"""
        # Создаем пользователей на разных платформах
        TelegramAdapter.create_user(self.test_telegram_id + 30, self.test_user_data)
        WebsiteAdapter.create_user("loyalty@test.com", self.test_user_data)
        
        # Получаем объединенную информацию о лояльности
        identifiers = {
            'telegram_id': self.test_telegram_id + 30,
            'email': "loyalty@test.com"
        }
        
        loyalty_info = UniversalAdapter.get_unified_loyalty_info(identifiers)
        assert loyalty_info is not None
        assert 'total_points' in loyalty_info
        assert 'platforms' in loyalty_info
        assert 'unified_at' in loyalty_info
        
        print("✅ Unified loyalty info works")
    
    def test_cross_platform_order(self):
        """Тест кросс-платформенного заказа"""
        # Создаем пользователя
        TelegramAdapter.create_user(self.test_telegram_id + 40, self.test_user_data)
        
        # Создаем заказ через универсальный адаптер
        user_identifiers = {'telegram_id': self.test_telegram_id + 40}
        order_data = {'items': [{'name': 'Cross Platform', 'price': 300}], 'total_amount': 300}
        
        order_id = UniversalAdapter.create_cross_platform_order(
            user_identifiers, 
            order_data, 
            'telegram'
        )
        
        assert order_id is not None
        print("✅ Cross-platform order works")
    
    def test_enhanced_unified_service(self):
        """Тест расширенного унифицированного сервиса"""
        # Проверка health check
        health = enhanced_unified_db.health_check()
        assert health is not None
        assert 'mode' in health
        
        # Создание пользователей через unified service
        telegram_uuid = enhanced_unified_db.create_telegram_user(self.test_telegram_id + 50, self.test_user_data)
        assert telegram_uuid is not None
        
        website_uuid = enhanced_unified_db.create_website_user("unified@test.com", self.test_user_data)
        assert website_uuid is not None
        
        mobile_uuid = enhanced_unified_db.create_mobile_user("device_unified", "ios", self.test_user_data)
        assert mobile_uuid is not None
        
        # Получение статистики платформ
        platform_stats = enhanced_unified_db.get_platform_statistics()
        assert platform_stats is not None
        assert 'total_platforms' in platform_stats
        
        print("✅ Enhanced unified service works")
    
    def test_platform_statistics(self):
        """Тест статистики платформ"""
        stats = UniversalAdapter.get_platform_statistics()
        
        assert stats is not None
        assert 'total_platforms' in stats
        assert 'generated_at' in stats
        assert stats['total_platforms'] > 0
        
        print(f"✅ Platform statistics: {stats['total_platforms']} platforms supported")
    
    def test_admin_dashboard_data(self):
        """Тест данных админской панели"""
        dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
        
        assert dashboard_data is not None
        assert 'system_status' in dashboard_data
        assert 'platform_stats' in dashboard_data
        assert 'summary' in dashboard_data
        assert 'alerts' in dashboard_data
        assert 'recommendations' in dashboard_data
        
        # Проверяем сводку
        summary = dashboard_data['summary']
        assert 'mode' in summary
        assert 'supported_platforms' in summary
        assert 'cross_platform_links' in summary
        
        print("✅ Admin dashboard data works")
    
    def test_sync_across_platforms(self):
        """Тест синхронизации между платформами"""
        # Создаем пользователя и связываем аккаунты
        TelegramAdapter.create_user(self.test_telegram_id + 60, self.test_user_data)
        WebsiteAdapter.create_user("sync@test.com", self.test_user_data)
        WebsiteAdapter.link_telegram_account("sync@test.com", self.test_telegram_id + 60)
        
        # Синхронизируем данные
        sync_data = {
            'preferences': {'language': 'ru', 'notifications': True},
            'updated_profile': {'last_name': 'Synchronized'}
        }
        
        sync_result = enhanced_unified_db.sync_user_across_platforms(
            "sync@test.com", 
            'website', 
            sync_data
        )
        
        assert sync_result is not None
        assert 'synced_platforms' in sync_result
        assert 'sync_timestamp' in sync_result
        
        print("✅ Cross-platform sync works")
    
    def test_mobile_push_notifications(self):
        """Тест push уведомлений для мобильных"""
        # Создаем мобильного пользователя
        MobileAppAdapter.create_user("push_device", "mobile_android", self.test_user_data)
        
        # Регистрируем push токен
        push_success = enhanced_unified_db.register_mobile_push_token(
            "push_device", 
            "android", 
            "fcm_token_android_123"
        )
        
        assert push_success
        
        # Проверяем что токен сохранился
        user_info = enhanced_unified_db.get_mobile_user_info("push_device", "android")
        assert user_info is not None
        assert user_info.get('can_receive_push') == True
        
        print("✅ Mobile push notifications work")
    
    def test_route_request_universal_adapter(self):
        """Тест универсальной маршрутизации запросов"""
        # Создаем пользователя
        TelegramAdapter.create_user(self.test_telegram_id + 70, self.test_user_data)
        
        # Тестируем маршрутизацию
        result = UniversalAdapter.route_request(
            'telegram', 
            'get_user_info', 
            self.test_telegram_id + 70
        )
        
        assert result is not None
        assert result['platform'] == 'telegram'
        
        # Тестируем неправильную платформу
        result = UniversalAdapter.route_request(
            'unknown_platform', 
            'get_user_info', 
            self.test_telegram_id + 70
        )
        
        assert result is None
        
        print("✅ Universal request routing works")

if __name__ == "__main__":
    test = TestPlatformAdapters()
    
    print("🚀 Starting platform adapters tests...\n")
    
    try:
        test.test_telegram_adapter()
        test.test_website_adapter()
        test.test_mobile_adapter()
        test.test_account_linking()
        test.test_cross_platform_user_search()
        test.test_unified_loyalty_info()
        test.test_cross_platform_order()
        test.test_enhanced_unified_service()
        test.test_platform_statistics()
        test.test_admin_dashboard_data()
        test.test_sync_across_platforms()
        test.test_mobile_push_notifications()
        test.test_route_request_universal_adapter()
        
        print("\n🎉 All platform adapter tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
