"""
Единый интерфейс для всех платформ мульти-платформенной системы
Обеспечивает унифицированный доступ ко всем адаптерам
"""
from typing import Dict, List, Optional, Union
from .fault_tolerant_service import fault_tolerant_db
from .platform_adapters import (
    TelegramAdapter,
    WebsiteAdapter,
    MobileAppAdapter,
    DesktopAppAdapter,
    APIAdapter,
    UniversalAdapter
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedUnifiedDatabaseService:
    """
    Расширенный единый сервис базы данных для всех платформ
    """
    
    def __init__(self):
        self.fault_tolerant_db = fault_tolerant_db
        self.adapters = {
            'telegram': TelegramAdapter,
            'website': WebsiteAdapter,
            'mobile': MobileAppAdapter,
            'desktop': DesktopAppAdapter,
            'api': APIAdapter,
            'universal': UniversalAdapter
        }
        logger.info("✅ EnhancedUnifiedDatabaseService initialized")
    
    # === TELEGRAM METHODS ===
    
    def create_telegram_user(self, telegram_id: int, user_data: Dict) -> Optional[str]:
        """Создать пользователя Telegram"""
        return self.adapters['telegram'].create_user(telegram_id, user_data)
    
    def get_telegram_user_info(self, telegram_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе Telegram"""
        return self.adapters['telegram'].get_user_info(telegram_id)
    
    def create_telegram_order(self, telegram_id: int, order_data: Dict) -> Optional[int]:
        """Создать заказ от Telegram пользователя"""
        return self.adapters['telegram'].create_order(telegram_id, order_data)
    
    def get_telegram_loyalty(self, telegram_id: int) -> Dict:
        """Получить информацию о лояльности Telegram пользователя"""
        return self.adapters['telegram'].get_loyalty_info(telegram_id)
    
    def get_telegram_orders(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получить заказы Telegram пользователя"""
        # Заглушка для тестирования
        return [
            {
                'order_id': 12345,
                'telegram_id': telegram_id,
                'amount': 100.0,
                'status': 'completed',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    
    # === WEBSITE METHODS ===
    
    def create_website_user(self, email: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя веб-сайта"""
        return self.adapters['website'].create_user(email, user_data)
    
    def get_website_user_info(self, email: str) -> Optional[Dict]:
        """Получить информацию о пользователе веб-сайта"""
        return self.adapters['website'].get_user_info(email)
    
    def create_website_order(self, email: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от веб-пользователя"""
        return self.adapters['website'].create_order(email, order_data)
    
    def get_website_loyalty(self, email: str) -> Dict:
        """Получить информацию о лояльности веб-пользователя"""
        return self.adapters['website'].get_loyalty_info(email)
    
    def update_website_profile(self, email: str, profile_data: Dict) -> bool:
        """Обновить профиль веб-пользователя"""
        try:
            # Сохранить в кэш
            cache_key = f"profile_website_{email}"
            self.fault_tolerant_db.local_cache.set(cache_key, profile_data, ttl=3600)
            return True
        except Exception as e:
            logger.error(f"Error updating website profile: {e}")
            return False
    
    def link_telegram_to_website(self, email: str, telegram_id: int) -> bool:
        """Связать аккаунт веб-сайта с Telegram"""
        return self.adapters['universal'].link_accounts(email, 'website', telegram_id, 'telegram')
    
    # === MOBILE METHODS ===
    
    def create_mobile_user(self, device_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя мобильного приложения"""
        return self.adapters['mobile'].create_user(device_id, platform, user_data)
    
    def get_mobile_user_info(self, device_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе мобильного приложения"""
        return self.adapters['mobile'].get_user_info(device_id, platform)
    
    def create_mobile_order(self, device_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от мобильного пользователя"""
        return self.adapters['mobile'].create_order(device_id, platform, order_data)
    
    def get_mobile_loyalty(self, device_id: str, platform: str) -> Dict:
        """Получить информацию о лояльности мобильного пользователя"""
        return self.adapters['mobile'].get_loyalty_info(device_id, platform)
    
    def sync_mobile_data(self, device_id: str, platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать данные мобильного приложения"""
        return self.adapters['mobile'].sync_data(device_id, platform, sync_data)
    
    def register_mobile_push_token(self, device_id: str, platform: str, push_token: str) -> bool:
        """Зарегистрировать токен для push уведомлений"""
        try:
            token_data = {
                'device_id': device_id,
                'platform': platform,
                'push_token': push_token,
                'registered_at': datetime.utcnow().isoformat()
            }
            
            cache_key = f"push_token_{platform}_{device_id}"
            self.fault_tolerant_db.local_cache.set(cache_key, token_data, ttl=86400 * 30)  # 30 дней
            return True
        except Exception as e:
            logger.error(f"Error registering push token: {e}")
            return False
    
    # === DESKTOP METHODS ===
    
    def create_desktop_user(self, user_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя десктопного приложения"""
        return self.adapters['desktop'].create_user(user_id, platform, user_data)
    
    def get_desktop_user_info(self, user_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе десктопного приложения"""
        return self.adapters['desktop'].get_user_info(user_id, platform)
    
    def create_desktop_order(self, user_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от десктопного пользователя"""
        return self.adapters['desktop'].create_order(user_id, platform, order_data)
    
    def get_desktop_loyalty(self, user_id: str, platform: str) -> Dict:
        """Получить информацию о лояльности десктопного пользователя"""
        return self.adapters['desktop'].get_loyalty_info(user_id, platform)
    
    # === API METHODS ===
    
    def create_api_user(self, api_key: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя через партнерский API"""
        return self.adapters['api'].create_user(api_key, user_data)
    
    def get_api_user_info(self, api_key: str) -> Optional[Dict]:
        """Получить информацию о пользователе API"""
        return self.adapters['api'].get_user_info(api_key)
    
    def create_api_order(self, api_key: str, order_data: Dict) -> Optional[int]:
        """Создать заказ через партнерский API"""
        return self.adapters['api'].create_order(api_key, order_data)
    
    def get_api_loyalty(self, api_key: str) -> Dict:
        """Получить информацию о лояльности API пользователя"""
        return self.adapters['api'].get_loyalty_info(api_key)
    
    # === UNIVERSAL METHODS ===
    
    def link_accounts(self, primary_identifier: Union[int, str], primary_platform: str,
                     secondary_identifier: Union[int, str], secondary_platform: str) -> bool:
        """Связать аккаунты между платформами"""
        return self.adapters['universal'].link_accounts(
            primary_identifier, primary_platform,
            secondary_identifier, secondary_platform
        )
    
    def find_user(self, identifier: Union[int, str], platform: str) -> Optional[Dict]:
        """Найти пользователя по идентификатору и платформе"""
        return self.adapters['universal'].find_user(identifier, platform)
    
    def sync_cross_platform_data(self, identifier: Union[int, str], platform: str, data: Dict) -> Dict:
        """Синхронизировать данные между платформами"""
        return self.adapters['universal'].sync_cross_platform_data(identifier, platform, data)
    
    def get_unified_loyalty(self, identifier: Union[int, str], platform: str) -> Dict:
        """Получить объединенную информацию о лояльности со всех платформ"""
        return self.adapters['universal'].get_unified_loyalty(identifier, platform)
    
    # === ADMINISTRATIVE METHODS ===
    
    def get_platform_statistics(self) -> Dict:
        """Получить статистику по платформам"""
        try:
            stats = {
                'total_users': 0,
                'total_orders': 0,
                'platform_breakdown': {
                    'telegram': {'users': 0, 'orders': 0},
                    'website': {'users': 0, 'orders': 0},
                    'mobile': {'users': 0, 'orders': 0},
                    'desktop': {'users': 0, 'orders': 0},
                    'api': {'users': 0, 'orders': 0}
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Подсчет из кэша (заглушка для тестирования)
            cache_items = len(self.fault_tolerant_db.local_cache.cache)
            stats['total_users'] = cache_items // 2  # Примерная оценка
            stats['total_orders'] = cache_items // 4  # Примерная оценка
            
            # Распределение по платформам
            for platform in stats['platform_breakdown']:
                stats['platform_breakdown'][platform]['users'] = cache_items // 10
                stats['platform_breakdown'][platform]['orders'] = cache_items // 20
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting platform statistics: {e}")
            return {
                'total_users': 0,
                'total_orders': 0,
                'platform_breakdown': {},
                'error': str(e)
            }
    
    def get_admin_dashboard_data(self) -> Dict:
        """Получить данные для админ дашборда"""
        try:
            system_status = self.fault_tolerant_db.get_system_status()
            platform_stats = self.get_platform_statistics()
            
            return {
                'system_status': system_status,
                'platform_stats': platform_stats,
                'alerts': self._get_system_alerts(),
                'recommendations': self._get_system_recommendations(),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting admin dashboard data: {e}")
            return {'error': str(e)}
    
    def export_system_data(self) -> Dict:
        """Экспортировать данные системы"""
        try:
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system_status': self.fault_tolerant_db.get_system_status(),
                'platform_stats': self.get_platform_statistics(),
                'cache_data': self.fault_tolerant_db.local_cache.cache,
                'queue_stats': self.fault_tolerant_db.operation_queue.get_queue_stats()
            }
            
        except Exception as e:
            logger.error(f"Error exporting system data: {e}")
            return {'error': str(e)}
    
    def _get_system_alerts(self) -> List[Dict]:
        """Получить системные алерты"""
        alerts = []
        
        # Проверить статус системы
        system_status = self.fault_tolerant_db.get_system_status()
        
        if not system_status['health']['overall']:
            alerts.append({
                'level': 'critical',
                'message': 'Database connectivity issues detected',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Проверить очередь операций
        queue_stats = system_status['queue']
        if queue_stats['total_operations'] > 100:
            alerts.append({
                'level': 'warning',
                'message': f'High number of pending operations: {queue_stats["total_operations"]}',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def _get_system_recommendations(self) -> List[Dict]:
        """Получить рекомендации по системе"""
        recommendations = []
        
        system_status = self.fault_tolerant_db.get_system_status()
        
        # Рекомендации по производительности
        if system_status['mode'] == 'CACHE_ONLY':
            recommendations.append({
                'type': 'performance',
                'message': 'Consider restoring database connectivity for better performance',
                'priority': 'high'
            })
        
        # Рекомендации по очереди операций
        queue_stats = system_status['queue']
        if queue_stats['total_operations'] > 50:
            recommendations.append({
                'type': 'maintenance',
                'message': 'Consider running forced sync to process pending operations',
                'priority': 'medium'
            })
        
        return recommendations
    
    def init_databases(self):
        """Инициализировать базы данных"""
        try:
            # Инициализация отказоустойчивого сервиса
            logger.info("🔧 Initializing fault-tolerant database service...")
            
            # Проверка здоровья БД
            health_status = self.fault_tolerant_db.get_system_status()
            logger.info(f"✅ Database health check: {health_status['health']['overall']}")
            
            logger.info("✅ EnhancedUnifiedDatabaseService databases initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing databases: {e}")
            raise

class UnifiedDatabaseService:
    """
    Обратно совместимый единый сервис базы данных
    """
    
    def __init__(self):
        self.enhanced_service = EnhancedUnifiedDatabaseService()
        logger.info("✅ UnifiedDatabaseService initialized (backward compatibility)")
    
    # Делегирование всех методов к enhanced_service
    def __getattr__(self, name):
        return getattr(self.enhanced_service, name)

# Глобальные экземпляры сервисов
enhanced_unified_db = EnhancedUnifiedDatabaseService()
unified_db = UnifiedDatabaseService()
