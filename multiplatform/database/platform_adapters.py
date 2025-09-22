"""
Мульти-платформенные адаптеры для всех платформ
Telegram, Website, Mobile, Desktop с единым интерфейсом
"""
from typing import Dict, List, Optional, Union
from .fault_tolerant_service import fault_tolerant_db, PlatformType
import logging
import hashlib
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramAdapter:
    """Адаптер для Telegram бота"""
    
    @staticmethod
    def create_user(telegram_id: int, user_data: Dict) -> Optional[str]:
        """Создать пользователя Telegram"""
        enhanced_data = {
            **user_data,
            'telegram_id': telegram_id,
            'platform': PlatformType.TELEGRAM.value,
            'user_type': 'telegram_user'
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            telegram_id, enhanced_data, PlatformType.TELEGRAM.value
        )
        
        if success:
            user_uuid = TelegramAdapter._generate_user_uuid(telegram_id)
            logger.info(f"✅ Telegram user created: {telegram_id}")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(telegram_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе Telegram"""
        user_info = fault_tolerant_db.get_user_with_fallback(telegram_id, PlatformType.TELEGRAM.value)
        
        if user_info:
            # Добавляем дополнительную информацию для Telegram
            user_info['platform'] = PlatformType.TELEGRAM.value
            user_info['telegram_id'] = telegram_id
            user_info['is_bot_user'] = True
        
        return user_info
    
    @staticmethod
    def create_order(telegram_id: int, order_data: Dict) -> Optional[int]:
        """Создать заказ от Telegram пользователя"""
        enhanced_order_data = {
            **order_data,
            'platform': PlatformType.TELEGRAM.value,
            'source': 'telegram_bot',
            'user_telegram_id': telegram_id
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            telegram_id, enhanced_order_data, PlatformType.TELEGRAM.value
        )
        
        if order_id:
            logger.info(f"✅ Telegram order created: {order_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(telegram_id: int) -> Dict:
        """Получить информацию о лояльности"""
        return fault_tolerant_db.get_loyalty_with_fallback(telegram_id, PlatformType.TELEGRAM.value)
    
    @staticmethod
    def _generate_user_uuid(telegram_id: int) -> str:
        """Генерировать UUID для пользователя Telegram"""
        data = f"telegram_{telegram_id}_{datetime.utcnow().isoformat()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, data))

class WebsiteAdapter:
    """Адаптер для веб-сайта"""
    
    @staticmethod
    def create_user(email: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя веб-сайта"""
        enhanced_data = {
            **user_data,
            'email': email,
            'platform': PlatformType.WEBSITE.value,
            'user_type': 'website_user'
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            email, enhanced_data, PlatformType.WEBSITE.value
        )
        
        if success:
            user_uuid = WebsiteAdapter._generate_user_uuid(email)
            logger.info(f"✅ Website user created: {email}")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(email: str) -> Optional[Dict]:
        """Получить информацию о пользователе веб-сайта"""
        user_info = fault_tolerant_db.get_user_with_fallback(email, PlatformType.WEBSITE.value)
        
        if user_info:
            user_info['platform'] = PlatformType.WEBSITE.value
            user_info['email'] = email
            user_info['is_web_user'] = True
        
        return user_info
    
    @staticmethod
    def create_order(email: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от веб-пользователя"""
        enhanced_order_data = {
            **order_data,
            'platform': PlatformType.WEBSITE.value,
            'source': 'website',
            'user_email': email
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            email, enhanced_order_data, PlatformType.WEBSITE.value
        )
        
        if order_id:
            logger.info(f"✅ Website order created: {order_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(email: str) -> Dict:
        """Получить информацию о лояльности"""
        return fault_tolerant_db.get_loyalty_with_fallback(email, PlatformType.WEBSITE.value)
    
    @staticmethod
    def _generate_user_uuid(email: str) -> str:
        """Генерировать UUID для пользователя веб-сайта"""
        data = f"website_{email}_{datetime.utcnow().isoformat()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, data))

class MobileAppAdapter:
    """Адаптер для мобильных приложений"""
    
    @staticmethod
    def create_user(device_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя мобильного приложения"""
        platform_type = PlatformType.MOBILE_IOS if platform.lower() == 'ios' else PlatformType.MOBILE_ANDROID
        
        enhanced_data = {
            **user_data,
            'device_id': device_id,
            'platform': platform_type.value,
            'user_type': 'mobile_user',
            'app_platform': platform.lower()
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            device_id, enhanced_data, platform_type.value
        )
        
        if success:
            user_uuid = MobileAppAdapter._generate_user_uuid(device_id, platform)
            logger.info(f"✅ Mobile user created: {device_id} ({platform})")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(device_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе мобильного приложения"""
        platform_type = PlatformType.MOBILE_IOS if platform.lower() == 'ios' else PlatformType.MOBILE_ANDROID
        
        user_info = fault_tolerant_db.get_user_with_fallback(device_id, platform_type.value)
        
        if user_info:
            user_info['platform'] = platform_type.value
            user_info['device_id'] = device_id
            user_info['app_platform'] = platform.lower()
            user_info['is_mobile_user'] = True
        
        return user_info
    
    @staticmethod
    def create_order(device_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от мобильного пользователя"""
        platform_type = PlatformType.MOBILE_IOS if platform.lower() == 'ios' else PlatformType.MOBILE_ANDROID
        
        enhanced_order_data = {
            **order_data,
            'platform': platform_type.value,
            'source': f'mobile_{platform.lower()}',
            'device_id': device_id
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            device_id, enhanced_order_data, platform_type.value
        )
        
        if order_id:
            logger.info(f"✅ Mobile order created: {order_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(device_id: str, platform: str) -> Dict:
        """Получить информацию о лояльности"""
        platform_type = PlatformType.MOBILE_IOS if platform.lower() == 'ios' else PlatformType.MOBILE_ANDROID
        return fault_tolerant_db.get_loyalty_with_fallback(device_id, platform_type.value)
    
    @staticmethod
    def sync_data(device_id: str, platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать данные мобильного приложения"""
        platform_type = PlatformType.MOBILE_IOS if platform.lower() == 'ios' else PlatformType.MOBILE_ANDROID
        
        # Сохранить данные синхронизации в кэш
        sync_key = f"sync_{platform_type.value}_{device_id}"
        fault_tolerant_db.local_cache.set(sync_key, sync_data, ttl=3600)  # 1 час
        
        return {
            'status': 'success',
            'synced_at': datetime.utcnow().isoformat(),
            'platform': platform_type.value,
            'device_id': device_id
        }
    
    @staticmethod
    def _generate_user_uuid(device_id: str, platform: str) -> str:
        """Генерировать UUID для пользователя мобильного приложения"""
        data = f"mobile_{platform}_{device_id}_{datetime.utcnow().isoformat()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, data))

class DesktopAppAdapter:
    """Адаптер для десктопных приложений"""
    
    @staticmethod
    def create_user(user_id: str, platform: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя десктопного приложения"""
        enhanced_data = {
            **user_data,
            'user_id': user_id,
            'platform': f'desktop_{platform.lower()}',
            'user_type': 'desktop_user',
            'desktop_platform': platform.lower()
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            user_id, enhanced_data, f'desktop_{platform.lower()}'
        )
        
        if success:
            user_uuid = DesktopAppAdapter._generate_user_uuid(user_id, platform)
            logger.info(f"✅ Desktop user created: {user_id} ({platform})")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(user_id: str, platform: str) -> Optional[Dict]:
        """Получить информацию о пользователе десктопного приложения"""
        user_info = fault_tolerant_db.get_user_with_fallback(user_id, f'desktop_{platform.lower()}')
        
        if user_info:
            user_info['platform'] = f'desktop_{platform.lower()}'
            user_info['user_id'] = user_id
            user_info['desktop_platform'] = platform.lower()
            user_info['is_desktop_user'] = True
        
        return user_info
    
    @staticmethod
    def create_order(user_id: str, platform: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от десктопного пользователя"""
        enhanced_order_data = {
            **order_data,
            'platform': f'desktop_{platform.lower()}',
            'source': f'desktop_{platform.lower()}',
            'user_id': user_id
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            user_id, enhanced_order_data, f'desktop_{platform.lower()}'
        )
        
        if order_id:
            logger.info(f"✅ Desktop order created: {order_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(user_id: str, platform: str) -> Dict:
        """Получить информацию о лояльности"""
        return fault_tolerant_db.get_loyalty_with_fallback(user_id, f'desktop_{platform.lower()}')
    
    @staticmethod
    def _generate_user_uuid(user_id: str, platform: str) -> str:
        """Генерировать UUID для пользователя десктопного приложения"""
        data = f"desktop_{platform}_{user_id}_{datetime.utcnow().isoformat()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, data))

class APIAdapter:
    """Адаптер для партнерского API"""
    
    @staticmethod
    def create_user(api_key: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя через партнерский API"""
        enhanced_data = {
            **user_data,
            'platform': 'api',
            'user_type': 'api_user',
            'api_key': api_key
        }
        
        # Используем API ключ как идентификатор
        success = fault_tolerant_db.create_user_with_fallback(
            api_key, enhanced_data, 'api'
        )
        
        if success:
            user_uuid = APIAdapter._generate_user_uuid(api_key)
            logger.info(f"✅ API user created: {api_key}")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(api_key: str) -> Optional[Dict]:
        """Получить информацию о пользователе API"""
        user_info = fault_tolerant_db.get_user_with_fallback(api_key, 'api')
        
        if user_info:
            user_info['platform'] = 'api'
            user_info['api_key'] = api_key
            user_info['is_api_user'] = True
        
        return user_info
    
    @staticmethod
    def create_order(api_key: str, order_data: Dict) -> Optional[int]:
        """Создать заказ через партнерский API"""
        enhanced_order_data = {
            **order_data,
            'platform': 'api',
            'source': 'partner_api',
            'api_key': api_key
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            api_key, enhanced_order_data, 'api'
        )
        
        if order_id:
            logger.info(f"✅ API order created: {order_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(api_key: str) -> Dict:
        """Получить информацию о лояльности"""
        return fault_tolerant_db.get_loyalty_with_fallback(api_key, 'api')
    
    @staticmethod
    def _generate_user_uuid(api_key: str) -> str:
        """Генерировать UUID для пользователя API"""
        data = f"api_{api_key}_{datetime.utcnow().isoformat()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, data))

class UniversalAdapter:
    """Универсальный адаптер для кросс-платформенной синхронизации"""
    
    @staticmethod
    def link_accounts(primary_identifier: Union[int, str], primary_platform: str, 
                     secondary_identifier: Union[int, str], secondary_platform: str) -> bool:
        """Связать аккаунты между платформами"""
        try:
            link_data = {
                'primary_identifier': primary_identifier,
                'primary_platform': primary_platform,
                'secondary_identifier': secondary_identifier,
                'secondary_platform': secondary_platform,
                'linked_at': datetime.utcnow().isoformat()
            }
            
            # Сохранить связь в кэш
            link_key = f"link_{primary_platform}_{primary_identifier}_{secondary_platform}_{secondary_identifier}"
            fault_tolerant_db.local_cache.set(link_key, link_data, ttl=86400 * 365)  # 1 год
            
            logger.info(f"✅ Accounts linked: {primary_platform}:{primary_identifier} <-> {secondary_platform}:{secondary_identifier}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error linking accounts: {e}")
            return False
    
    @staticmethod
    def find_user(identifier: Union[int, str], platform: str) -> Optional[Dict]:
        """Найти пользователя по идентификатору и платформе"""
        try:
            user_info = fault_tolerant_db.get_user_with_fallback(identifier, platform)
            if user_info:
                # Добавить информацию о связанных аккаунтах
                user_info['linked_accounts'] = UniversalAdapter._get_linked_accounts(identifier, platform)
            
            return user_info
            
        except Exception as e:
            logger.error(f"❌ Error finding user: {e}")
            return None
    
    @staticmethod
    def sync_cross_platform_data(identifier: Union[int, str], platform: str, data: Dict) -> Dict:
        """Синхронизировать данные между платформами"""
        try:
            # Получить связанные аккаунты
            linked_accounts = UniversalAdapter._get_linked_accounts(identifier, platform)
            
            sync_results = []
            
            # Синхронизировать с каждым связанным аккаунтом
            for linked_account in linked_accounts:
                linked_platform = linked_account['platform']
                linked_identifier = linked_account['identifier']
                
                # Сохранить данные синхронизации
                sync_key = f"sync_{linked_platform}_{linked_identifier}"
                fault_tolerant_db.local_cache.set(sync_key, data, ttl=3600)  # 1 час
                
                sync_results.append({
                    'platform': linked_platform,
                    'identifier': linked_identifier,
                    'synced_at': datetime.utcnow().isoformat()
                })
            
            return {
                'status': 'success',
                'synced_accounts': len(sync_results),
                'results': sync_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error syncing cross-platform data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def get_unified_loyalty(identifier: Union[int, str], platform: str) -> Dict:
        """Получить объединенную информацию о лояльности со всех платформ"""
        try:
            # Получить основную информацию о лояльности
            main_loyalty = fault_tolerant_db.get_loyalty_with_fallback(identifier, platform)
            
            # Получить связанные аккаунты
            linked_accounts = UniversalAdapter._get_linked_accounts(identifier, platform)
            
            # Объединить данные лояльности
            total_points = main_loyalty.get('current_points', 0)
            all_cards = main_loyalty.get('partner_cards', [])
            all_history = main_loyalty.get('recent_history', [])
            
            for linked_account in linked_accounts:
                linked_platform = linked_account['platform']
                linked_identifier = linked_account['identifier']
                
                linked_loyalty = fault_tolerant_db.get_loyalty_with_fallback(linked_identifier, linked_platform)
                
                total_points += linked_loyalty.get('current_points', 0)
                all_cards.extend(linked_loyalty.get('partner_cards', []))
                all_history.extend(linked_loyalty.get('recent_history', []))
            
            return {
                'total_points': total_points,
                'all_cards': all_cards,
                'all_history': all_history,
                'platforms': [platform] + [acc['platform'] for acc in linked_accounts],
                'source': 'unified'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting unified loyalty: {e}")
            return {
                'total_points': 0,
                'all_cards': [],
                'all_history': [],
                'platforms': [],
                'source': 'error'
            }
    
    @staticmethod
    def _get_linked_accounts(identifier: Union[int, str], platform: str) -> List[Dict]:
        """Получить список связанных аккаунтов"""
        try:
            # Поиск связей в кэше
            linked_accounts = []
            
            # Простой поиск по ключам кэша
            for key in fault_tolerant_db.local_cache.cache.keys():
                if key.startswith(f"link_{platform}_{identifier}_"):
                    link_data = fault_tolerant_db.local_cache.get(key)
                    if link_data:
                        linked_accounts.append({
                            'platform': link_data['secondary_platform'],
                            'identifier': link_data['secondary_identifier'],
                            'linked_at': link_data['linked_at']
                        })
            
            return linked_accounts
            
        except Exception as e:
            logger.error(f"❌ Error getting linked accounts: {e}")
            return []
