from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import logging
import uuid
import json

from .fault_tolerant_service import fault_tolerant_db, PlatformType
from .platform_adapters import (
    TelegramAdapter, WebsiteAdapter, MobileAppAdapter, 
    DesktopAppAdapter, APIAdapter, UniversalAdapter
)

logger = logging.getLogger(__name__)

class EnhancedUnifiedDatabaseService:
    """Улучшенный унифицированный сервис базы данных"""
    
    def __init__(self):
        self.fault_tolerant_db = fault_tolerant_db
        self.platform_adapters = {
            'telegram': TelegramAdapter,
            'website': WebsiteAdapter,
            'mobile': MobileAppAdapter,
            'desktop': DesktopAppAdapter,
            'api': APIAdapter,
            'universal': UniversalAdapter
        }
        
        # Статистика
        self.stats = {
            'total_users': 0,
            'total_orders': 0,
            'platform_breakdown': {},
            'last_updated': None
        }
        
        logger.info("✅ EnhancedUnifiedDatabaseService initialized")
    
    def init_databases(self):
        """Инициализация баз данных"""
        try:
            # Инициализация отказоустойчивой системы
            self.fault_tolerant_db.health_monitor._check_all_databases()
            logger.info("✅ Database initialization completed")
            return True
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        return self.fault_tolerant_db.get_system_status()
    
    def get_current_timestamp(self) -> str:
        """Получить текущую временную метку"""
        return datetime.utcnow().isoformat()
    
    # === TELEGRAM METHODS ===
    
    def create_telegram_user(self, telegram_id: int, user_data: Dict) -> Optional[str]:
        """Создать пользователя Telegram"""
        try:
            user_uuid = TelegramAdapter.create_user(telegram_id, user_data)
            if user_uuid:
                self.stats['total_users'] += 1
                self.stats['platform_breakdown']['telegram'] = self.stats['platform_breakdown'].get('telegram', 0) + 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return user_uuid
        except Exception as e:
            logger.error(f"Error creating Telegram user: {e}")
            return None
    
    def get_telegram_user_info(self, telegram_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе Telegram"""
        try:
            return TelegramAdapter.get_user_info(telegram_id)
        except Exception as e:
            logger.error(f"Error getting Telegram user info: {e}")
            return None
    
    def create_telegram_order(self, telegram_id: int, order_data: Dict) -> Optional[int]:
        """Создать заказ от Telegram пользователя"""
        try:
            order_id = TelegramAdapter.create_order(telegram_id, order_data)
            if order_id:
                self.stats['total_orders'] += 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return order_id
        except Exception as e:
            logger.error(f"Error creating Telegram order: {e}")
            return None
    
    def get_telegram_loyalty(self, telegram_id: int) -> Dict:
        """Получить информацию о лояльности Telegram пользователя"""
        try:
            return self.fault_tolerant_db.get_loyalty_with_fallback(telegram_id, PlatformType.TELEGRAM.value)
        except Exception as e:
            logger.error(f"Error getting Telegram loyalty: {e}")
            return {'current_points': 0, 'partner_cards': [], 'recent_history': [], 'source': 'error'}
    
    def get_telegram_orders(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получить заказы Telegram пользователя"""
        try:
            # Здесь должна быть реальная логика получения заказов
            # Для демонстрации возвращаем пустой список
            return []
        except Exception as e:
            logger.error(f"Error getting Telegram orders: {e}")
            return []
    
    # === WEBSITE METHODS ===
    
    def create_website_user(self, email: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя сайта"""
        try:
            user_uuid = WebsiteAdapter.create_user(email, user_data)
            if user_uuid:
                self.stats['total_users'] += 1
                self.stats['platform_breakdown']['website'] = self.stats['platform_breakdown'].get('website', 0) + 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return user_uuid
        except Exception as e:
            logger.error(f"Error creating website user: {e}")
            return None
    
    def get_website_user_info(self, email: str) -> Optional[Dict]:
        """Получить информацию о пользователе сайта"""
        try:
            return WebsiteAdapter.get_user_info(email)
        except Exception as e:
            logger.error(f"Error getting website user info: {e}")
            return None
    
    def update_website_profile(self, email: str, profile_data: Dict) -> bool:
        """Обновить профиль пользователя сайта"""
        try:
            return WebsiteAdapter.update_profile(email, profile_data)
        except Exception as e:
            logger.error(f"Error updating website profile: {e}")
            return False
    
    def link_telegram_to_website(self, email: str, telegram_id: int) -> bool:
        """Связать аккаунт сайта с Telegram"""
        try:
            return WebsiteAdapter.link_telegram_account(email, telegram_id)
        except Exception as e:
            logger.error(f"Error linking Telegram to website: {e}")
            return False
    
    def create_website_order(self, email: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от веб-пользователя"""
        try:
            order_id = WebsiteAdapter.create_order(email, order_data)
            if order_id:
                self.stats['total_orders'] += 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return order_id
        except Exception as e:
            logger.error(f"Error creating website order: {e}")
            return None
    
    def get_website_loyalty(self, email: str) -> Dict:
        """Получить информацию о лояльности веб-пользователя"""
        try:
            return self.fault_tolerant_db.get_loyalty_with_fallback(email, PlatformType.WEBSITE.value)
        except Exception as e:
            logger.error(f"Error getting website loyalty: {e}")
            return {'current_points': 0, 'partner_cards': [], 'recent_history': [], 'source': 'error'}
    
    # === MOBILE METHODS ===
    
    def create_mobile_user(self, device_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя мобильного приложения"""
        try:
            user_uuid = MobileAppAdapter.create_user(device_id, platform, user_data)
            if user_uuid:
                self.stats['total_users'] += 1
                platform_key = f"mobile_{platform}"
                self.stats['platform_breakdown'][platform_key] = self.stats['platform_breakdown'].get(platform_key, 0) + 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return user_uuid
        except Exception as e:
            logger.error(f"Error creating mobile user: {e}")
            return None
    
    def get_mobile_user_info(self, device_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе мобильного приложения"""
        try:
            return MobileAppAdapter.get_user_info(device_id, platform)
        except Exception as e:
            logger.error(f"Error getting mobile user info: {e}")
            return None
    
    def sync_mobile_data(self, device_id: str, platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать данные мобильного приложения"""
        try:
            return MobileAppAdapter.sync_data(device_id, platform, sync_data)
        except Exception as e:
            logger.error(f"Error syncing mobile data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def register_mobile_push_token(self, device_id: str, platform: str, push_token: str) -> bool:
        """Зарегистрировать токен для push уведомлений"""
        try:
            return MobileAppAdapter.register_push_token(device_id, platform, push_token)
        except Exception as e:
            logger.error(f"Error registering mobile push token: {e}")
            return False
    
    def link_mobile_accounts(self, device_id: str, platform: str, account_data: Dict) -> bool:
        """Связать мобильный аккаунт с другими платформами"""
        try:
            return MobileAppAdapter.link_accounts(device_id, platform, account_data)
        except Exception as e:
            logger.error(f"Error linking mobile accounts: {e}")
            return False
    
    def create_mobile_order(self, device_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от мобильного пользователя"""
        try:
            order_id = MobileAppAdapter.create_order(device_id, platform, order_data)
            if order_id:
                self.stats['total_orders'] += 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return order_id
        except Exception as e:
            logger.error(f"Error creating mobile order: {e}")
            return None
    
    # === DESKTOP METHODS ===
    
    def create_desktop_user(self, user_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя десктопного приложения"""
        try:
            user_uuid = DesktopAppAdapter.create_user(user_id, platform, user_data)
            if user_uuid:
                self.stats['total_users'] += 1
                platform_key = f"desktop_{platform}"
                self.stats['platform_breakdown'][platform_key] = self.stats['platform_breakdown'].get(platform_key, 0) + 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return user_uuid
        except Exception as e:
            logger.error(f"Error creating desktop user: {e}")
            return None
    
    def get_desktop_user_info(self, user_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе десктопного приложения"""
        try:
            return DesktopAppAdapter.get_user_info(user_id, platform)
        except Exception as e:
            logger.error(f"Error getting desktop user info: {e}")
            return None
    
    def sync_desktop_with_cloud(self, user_id: str, platform: str, cloud_data: Dict) -> Dict:
        """Синхронизировать десктопные данные с облаком"""
        try:
            return DesktopAppAdapter.sync_with_cloud(user_id, platform, cloud_data)
        except Exception as e:
            logger.error(f"Error syncing desktop with cloud: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def create_desktop_order(self, user_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от десктопного пользователя"""
        try:
            order_id = DesktopAppAdapter.create_order(user_id, platform, order_data)
            if order_id:
                self.stats['total_orders'] += 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return order_id
        except Exception as e:
            logger.error(f"Error creating desktop order: {e}")
            return None
    
    # === UNIVERSAL METHODS ===
    
    def get_user_across_platforms(self, identifiers: Dict) -> Optional[Dict]:
        """Найти пользователя по любому идентификатору"""
        try:
            return UniversalAdapter.find_user(identifiers)
        except Exception as e:
            logger.error(f"Error finding user across platforms: {e}")
            return None
    
    def create_cross_platform_order(self, user_identifiers: Dict, order_details: Dict, primary_platform: str) -> Optional[int]:
        """Создать заказ с поддержкой кросс-платформенности"""
        try:
            order_id = UniversalAdapter.create_cross_platform_order(user_identifiers, order_details, primary_platform)
            if order_id:
                self.stats['total_orders'] += 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return order_id
        except Exception as e:
            logger.error(f"Error creating cross-platform order: {e}")
            return None
    
    def get_unified_loyalty_info(self, identifiers: Dict) -> Dict:
        """Получить объединенную информацию о лояльности"""
        try:
            return UniversalAdapter.get_unified_loyalty(identifiers)
        except Exception as e:
            logger.error(f"Error getting unified loyalty info: {e}")
            return {'current_points': 0, 'partner_cards': [], 'recent_history': [], 'source': 'error'}
    
    def sync_user_across_platforms(self, primary_identifier: Union[int, str], primary_platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать пользователя между всеми связанными платформами"""
        try:
            return UniversalAdapter.sync_user_across_platforms(primary_identifier, primary_platform, sync_data)
        except Exception as e:
            logger.error(f"Error syncing user across platforms: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_platform_statistics(self) -> Dict:
        """Получить статистику по всем платформам"""
        try:
            return {
                'total_users': self.stats['total_users'],
                'total_orders': self.stats['total_orders'],
                'platform_breakdown': self.stats['platform_breakdown'],
                'last_updated': self.stats['last_updated'],
                'timestamp': self.get_current_timestamp()
            }
        except Exception as e:
            logger.error(f"Error getting platform statistics: {e}")
            return {'error': str(e)}
    
    # === ADMIN METHODS ===
    
    def get_admin_dashboard_data(self) -> Dict:
        """Получить данные для админского dashboard"""
        try:
            system_status = self.fault_tolerant_db.get_system_status()
            
            return {
                'system_status': system_status,
                'platform_stats': self.get_platform_statistics(),
                'alerts': self._generate_alerts(),
                'recommendations': self._generate_recommendations(),
                'timestamp': self.get_current_timestamp()
            }
        except Exception as e:
            logger.error(f"Error getting admin dashboard data: {e}")
            return {'error': str(e)}
    
    def force_system_sync(self) -> Dict:
        """Принудительная синхронизация системы"""
        try:
            result = self.fault_tolerant_db.force_sync_all_pending()
            logger.info(f"Force sync completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error during force sync: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def export_system_report(self) -> Dict:
        """Экспорт полного отчета о системе"""
        try:
            system_status = self.fault_tolerant_db.get_system_status()
            platform_stats = self.get_platform_statistics()
            
            return {
                'timestamp': self.get_current_timestamp(),
                'system_status': system_status,
                'platform_stats': platform_stats,
                'alerts': self._generate_alerts(),
                'recommendations': self._generate_recommendations(),
                'export_info': {
                    'exported_by': 'EnhancedUnifiedDatabaseService',
                    'version': '1.0.0',
                    'export_type': 'full_system_report'
                }
            }
        except Exception as e:
            logger.error(f"Error exporting system report: {e}")
            return {'error': str(e)}
    
    # === API METHODS ===
    
    def create_api_order(self, api_key: str, external_user_id: str, order_details: Dict) -> Optional[int]:
        """Создать заказ через партнерский API"""
        try:
            order_id = APIAdapter.create_order(api_key, external_user_id, order_details)
            if order_id:
                self.stats['total_orders'] += 1
                self.stats['platform_breakdown']['api'] = self.stats['platform_breakdown'].get('api', 0) + 1
                self.stats['last_updated'] = self.get_current_timestamp()
            return order_id
        except Exception as e:
            logger.error(f"Error creating API order: {e}")
            return None
    
    def get_api_user_info(self, api_key: str, external_user_id: str) -> Optional[Dict]:
        """Получить информацию о внешнем пользователе"""
        try:
            return APIAdapter.get_user_info(api_key, external_user_id)
        except Exception as e:
            logger.error(f"Error getting API user info: {e}")
            return None
    
    # === HELPER METHODS ===
    
    def _generate_alerts(self) -> List[Dict]:
        """Генерировать алерты для dashboard"""
        alerts = []
        
        try:
            system_status = self.fault_tolerant_db.get_system_status()
            
            # Проверяем статус баз данных
            if not system_status['health']['postgresql']['status']:
                alerts.append({
                    'level': 'critical',
                    'message': 'PostgreSQL database is offline',
                    'action': 'Check database connection and restart if necessary',
                    'platform_impact': 'All platforms affected'
                })
            
            if not system_status['health']['supabase']['status']:
                alerts.append({
                    'level': 'warning',
                    'message': 'Supabase service is unavailable',
                    'action': 'Check Supabase status and API keys',
                    'platform_impact': 'Loyalty system degraded'
                })
            
            # Проверяем размер очереди
            queue_size = system_status['queue']['total_operations']
            if queue_size > 100:
                alerts.append({
                    'level': 'warning',
                    'message': f'Operation queue is large: {queue_size} operations',
                    'action': 'Consider increasing processing capacity',
                    'platform_impact': 'Delayed operations'
                })
            
            # Проверяем uptime
            uptime = system_status['uptime']['overall']
            if uptime < 95:
                alerts.append({
                    'level': 'warning',
                    'message': f'System uptime is low: {uptime}%',
                    'action': 'Investigate stability issues',
                    'platform_impact': 'Service reliability degraded'
                })
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            alerts.append({
                'level': 'critical',
                'message': f'Error generating alerts: {e}',
                'action': 'Check system monitoring',
                'platform_impact': 'Unknown'
            })
        
        return alerts
    
    def _generate_recommendations(self) -> List[str]:
        """Генерировать рекомендации по оптимизации"""
        recommendations = []
        
        try:
            system_status = self.fault_tolerant_db.get_system_status()
            
            # Рекомендации по uptime
            pg_uptime = system_status['uptime']['postgresql']
            sb_uptime = system_status['uptime']['supabase']
            
            if pg_uptime < 95:
                recommendations.append(f"PostgreSQL uptime is {pg_uptime}%. Consider investigating stability issues.")
            
            if sb_uptime < 95:
                recommendations.append(f"Supabase uptime is {sb_uptime}%. Check service reliability.")
            
            # Рекомендации по кешу
            cache_items = system_status['cache']['total_items']
            if cache_items > 1000:
                recommendations.append(f"Cache has {cache_items} items. Consider implementing cache cleanup.")
            
            # Рекомендации по очереди
            queue_size = system_status['queue']['total_operations']
            if queue_size > 50:
                recommendations.append(f"Operation queue has {queue_size} items. Consider increasing processing capacity.")
            
            # Если рекомендаций нет, добавляем положительную
            if not recommendations:
                recommendations.append("System is performing optimally. No immediate actions required.")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to system error.")
        
        return recommendations

# Глобальные экземпляры
enhanced_unified_db = EnhancedUnifiedDatabaseService()
unified_db = enhanced_unified_db  # Алиас для обратной совместимости