from .db_v2 import db_v2
from .fault_tolerant_service import fault_tolerant_db
from .platform_adapters import (
    UniversalAdapter, TelegramAdapter, WebsiteAdapter, 
    MobileAppAdapter, DesktopAppAdapter, APIAdapter
)
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedUnifiedDatabaseService:
    """
    Расширенный унифицированный сервис с поддержкой отказоустойчивости
    и мульти-платформенной архитектуры
    """
    
    def __init__(self):
        self.main_db = db_v2
        self.fault_tolerant = fault_tolerant_db
        self.adapters = UniversalAdapter.get_adapters()
        logger.info("🚀 EnhancedUnifiedDatabaseService initialized")
    
    def health_check(self) -> Dict:
        """Комплексная проверка здоровья всех систем"""
        return self.fault_tolerant.get_system_status()
    
    # === TELEGRAM МЕТОДЫ ===
    
    def create_telegram_user(self, telegram_id: int, user_data: Dict) -> Optional[str]:
        """Создать пользователя Telegram с отказоустойчивостью"""
        return TelegramAdapter.create_user(telegram_id, user_data)
    
    def get_telegram_user_info(self, telegram_id: int) -> Optional[Dict]:
        """Получить информацию о Telegram пользователе"""
        return TelegramAdapter.get_user_info(telegram_id)
    
    def create_telegram_order(self, telegram_id: int, order_data: Dict) -> Optional[int]:
        """Создать заказ от Telegram пользователя"""
        return TelegramAdapter.create_order(telegram_id, order_data)
    
    def get_telegram_loyalty(self, telegram_id: int) -> Dict:
        """Получить лояльность Telegram пользователя"""
        return TelegramAdapter.get_loyalty_info(telegram_id)
    
    def get_telegram_orders(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получить заказы Telegram пользователя"""
        return TelegramAdapter.get_user_orders(telegram_id, limit)
    
    # === WEBSITE МЕТОДЫ ===
    
    def create_website_user(self, email: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя сайта"""
        return WebsiteAdapter.create_user(email, user_data)
    
    def get_website_user_info(self, email: str) -> Optional[Dict]:
        """Получить информацию о пользователе сайта"""
        return WebsiteAdapter.get_user_info(email)
    
    def create_website_order(self, email: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от веб-пользователя"""
        return WebsiteAdapter.create_order(email, order_data)
    
    def get_website_loyalty(self, email: str) -> Dict:
        """Получить лояльность веб-пользователя"""
        return WebsiteAdapter.get_loyalty_info(email)
    
    def link_telegram_to_website(self, email: str, telegram_id: int) -> bool:
        """Связать аккаунты сайта и Telegram"""
        return WebsiteAdapter.link_telegram_account(email, telegram_id)
    
    def update_website_profile(self, email: str, profile_data: Dict) -> bool:
        """Обновить профиль веб-пользователя"""
        return WebsiteAdapter.update_user_profile(email, profile_data)
    
    # === MOBILE APP МЕТОДЫ ===
    
    def create_mobile_user(self, device_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя мобильного приложения"""
        platform_type = 'mobile_ios' if 'ios' in platform.lower() else 'mobile_android'
        return MobileAppAdapter.create_user(device_id, platform_type, user_data)
    
    def get_mobile_user_info(self, device_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе приложения"""
        platform_type = 'mobile_ios' if 'ios' in platform.lower() else 'mobile_android'
        return MobileAppAdapter.get_user_info(device_id, platform_type)
    
    def create_mobile_order(self, device_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от мобильного пользователя"""
        platform_type = 'mobile_ios' if 'ios' in platform.lower() else 'mobile_android'
        return MobileAppAdapter.create_order(device_id, platform_type, order_data)
    
    def sync_mobile_data(self, device_id: str, platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать данные мобильного приложения"""
        platform_type = 'mobile_ios' if 'ios' in platform.lower() else 'mobile_android'
        return MobileAppAdapter.sync_user_data(device_id, platform_type, sync_data)
    
    def register_mobile_push_token(self, device_id: str, platform: str, push_token: str) -> bool:
        """Зарегистрировать push токен"""
        platform_type = 'mobile_ios' if 'ios' in platform.lower() else 'mobile_android'
        return MobileAppAdapter.register_push_token(device_id, platform_type, push_token)
    
    def link_mobile_accounts(self, device_id: str, platform: str, account_data: Dict) -> bool:
        """Связать мобильный аккаунт с другими платформами"""
        platform_type = 'mobile_ios' if 'ios' in platform.lower() else 'mobile_android'
        return MobileAppAdapter.link_accounts(device_id, platform_type, account_data)
    
    # === DESKTOP APP МЕТОДЫ ===
    
    def create_desktop_user(self, user_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя десктопного приложения"""
        platform_type = f"desktop_{platform.lower()}"
        return DesktopAppAdapter.create_user(user_id, platform_type, user_data)
    
    def get_desktop_user_info(self, user_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе десктопа"""
        platform_type = f"desktop_{platform.lower()}"
        return DesktopAppAdapter.get_user_info(user_id, platform_type)
    
    def sync_desktop_with_cloud(self, user_id: str, platform: str, cloud_data: Dict) -> Dict:
        """Синхронизировать десктопные данные с облаком"""
        platform_type = f"desktop_{platform.lower()}"
        return DesktopAppAdapter.sync_with_cloud(user_id, platform_type, cloud_data)
    
    # === API МЕТОДЫ ===
    
    def create_api_order(self, api_key: str, external_user_id: str, order_data: Dict) -> Optional[int]:
        """Создать заказ через партнерский API"""
        return APIAdapter.create_external_order(api_key, external_user_id, order_data)
    
    def get_api_user_info(self, api_key: str, external_user_id: str) -> Optional[Dict]:
        """Получить информацию о внешнем пользователе"""
        return APIAdapter.get_external_user_info(api_key, external_user_id)
    
    # === УНИВЕРСАЛЬНЫЕ МЕТОДЫ ===
    
    def get_user_across_platforms(self, identifiers: Dict) -> Optional[Dict]:
        """Найти пользователя по любому идентификатору с любой платформы"""
        return UniversalAdapter.get_user_across_platforms(identifiers)
    
    def create_cross_platform_order(self, user_identifiers: Dict, order_data: Dict, primary_platform: str) -> Optional[int]:
        """Создать заказ с поддержкой кросс-платформенности"""
        return UniversalAdapter.create_cross_platform_order(user_identifiers, order_data, primary_platform)
    
    def get_unified_loyalty_info(self, user_identifiers: Dict) -> Dict:
        """Получить объединенную информацию о лояльности со всех платформ"""
        return UniversalAdapter.get_unified_loyalty_info(user_identifiers)
    
    def sync_user_across_platforms(self, primary_identifier: str, primary_platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать пользователя между всеми связанными платформами"""
        return UniversalAdapter.sync_user_across_platforms(primary_identifier, primary_platform, sync_data)
    
    def get_platform_statistics(self) -> Dict:
        """Получить статистику по всем платформам"""
        return UniversalAdapter.get_platform_statistics()
    
    # === АДМИНИСТРАТИВНЫЕ МЕТОДЫ ===
    
    def get_admin_dashboard_data(self) -> Dict:
        """Получить данные для админской панели"""
        system_status = self.fault_tolerant.get_system_status()
        platform_stats = self.get_platform_statistics()
        
        dashboard_data = {
            'system_status': system_status,
            'platform_stats': platform_stats,
            'summary': {
                'mode': system_status['mode'],
                'overall_health': system_status['health']['overall'],
                'pending_operations': system_status['queue']['total_operations'],
                'cache_items': system_status['cache']['total_items'],
                'uptime_postgresql': system_status['uptime']['postgresql'],
                'uptime_supabase': system_status['uptime']['supabase'],
                'supported_platforms': len(self.adapters),
                'cross_platform_links': platform_stats.get('cross_platform_links', 0)
            },
            'alerts': self._generate_system_alerts(system_status),
            'recommendations': self._generate_recommendations(system_status)
        }
        
        return dashboard_data
    
    def _generate_system_alerts(self, system_status: Dict) -> List[Dict]:
        """Генерировать алерты системы"""
        alerts = []
        
        # Проверка состояния БД
        if not system_status['health']['postgresql']['status']:
            alerts.append({
                'level': 'critical',
                'message': 'PostgreSQL database is down',
                'since': system_status['health']['postgresql'].get('downtime_start'),
                'action': 'Check database connection and restart if necessary',
                'platform_impact': 'All platforms affected for orders and main operations'
            })
        
        if not system_status['health']['supabase']['status']:
            alerts.append({
                'level': 'warning',
                'message': 'Supabase is unavailable',
                'since': system_status['health']['supabase'].get('downtime_start'),
                'action': 'Loyalty features are limited, check Supabase status',
                'platform_impact': 'Loyalty and profile features limited on all platforms'
            })
        
        # Проверка очереди операций
        pending_ops = system_status['queue']['total_operations']
        if pending_ops > 100:
            alerts.append({
                'level': 'warning',
                'message': f'High number of pending operations: {pending_ops}',
                'action': 'Consider manual sync or check database performance',
                'platform_impact': 'Delayed synchronization across platforms'
            })
        
        # Проверка uptime
        if system_status['uptime']['overall'] < 95:
            alerts.append({
                'level': 'warning',
                'message': f'System uptime below 95%: {system_status["uptime"]["overall"]}%',
                'action': 'Investigate recent outages and improve reliability',
                'platform_impact': 'Reduced service quality on all platforms'
            })
        
        return alerts
    
    def _generate_recommendations(self, system_status: Dict) -> List[str]:
        """Генерировать рекомендации по улучшению системы"""
        recommendations = []
        
        mode = system_status['mode']
        
        if mode == 'CACHE_ONLY':
            recommendations.append('Both databases are down. Restore database connections immediately.')
            recommendations.append('All platforms operating in offline mode with cached data only.')
            recommendations.append('New user registrations and orders are queued for processing.')
        
        elif mode == 'MAIN_DB_ONLY':
            recommendations.append('Supabase is down. Loyalty features unavailable on all platforms.')
            recommendations.append('Consider implementing backup loyalty calculation in PostgreSQL.')
            recommendations.append('Mobile and web users cannot sync loyalty data.')
        
        elif mode == 'LOYALTY_ONLY':
            recommendations.append('Main database is down. Core order functionality limited.')
            recommendations.append('Restore PostgreSQL connection for full platform functionality.')
            recommendations.append('New orders can only be processed through cache queue.')
        
        # Рекомендации по производительности
        cache_usage = system_status['cache']['memory_usage_mb']
        if cache_usage > 100:  # 100MB
            recommendations.append(f'Cache usage is high ({cache_usage:.1f}MB). Consider platform-specific cache optimization.')
        
        pending_ops = system_status['queue']['total_operations']
        if pending_ops > 50:
            recommendations.append(f'Consider running manual sync to process {pending_ops} pending operations across platforms.')
        
        # Платформенные рекомендации
        if len(self.adapters) > 4:
            recommendations.append('Multiple platforms detected. Ensure cross-platform data consistency.')
        
        return recommendations
    
    def force_system_sync(self) -> Dict:
        """Принудительная синхронизация всей системы"""
        return self.fault_tolerant.force_sync_all_pending()
    
    def export_system_report(self) -> Dict:
        """Экспорт полного отчета о состоянии системы"""
        return {
            'generated_at': self.fault_tolerant.get_system_status()['timestamp'],
            'system_status': self.get_admin_dashboard_data(),
            'operation_stats': self.fault_tolerant.operation_stats,
            'platforms_supported': list(self.adapters.keys()),
            'platform_statistics': self.get_platform_statistics(),
            'fault_tolerance_enabled': True,
            'cache_enabled': True,
            'multi_platform_enabled': True,
            'cross_platform_sync_enabled': True
        }
    
    # === ОБРАТНАЯ СОВМЕСТИМОСТЬ ===
    
    @property
    def main(self):
        """Прямой доступ к основной БД (обратная совместимость)"""
        return self.main_db
    
    @property
    def loyalty(self):
        """Прямой доступ к системе лояльности (обратная совместимость)"""
        # Возвращаем заглушку для обратной совместимости
        class LoyaltyStub:
            def add_loyalty_points(self, user_id, points, reason):
                return True
            def get_loyalty_points(self, user_id):
                return 0
        return LoyaltyStub()
    
    # Методы для обратной совместимости со старым кодом
    def create_full_user(self, telegram_id: int, user_data: Dict) -> bool:
        """Создать полного пользователя (обратная совместимость)"""
        result = self.create_telegram_user(telegram_id, user_data)
        return result is not None
    
    def get_user_full_info(self, telegram_id: int, requesting_user_id: int = None) -> Dict:
        """Получить полную информацию (обратная совместимость)"""
        return self.get_telegram_user_info(telegram_id) or {}
    
    def create_order_with_loyalty(self, telegram_id: int, order_data: Dict) -> Optional[int]:
        """Создать заказ с лояльностью (обратная совместимость)"""
        return self.create_telegram_order(telegram_id, order_data)

# Глобальный экземпляр
enhanced_unified_db = EnhancedUnifiedDatabaseService()

# Алиас для обратной совместимости
unified_db = enhanced_unified_db
