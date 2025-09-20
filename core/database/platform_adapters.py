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
            telegram_id, 
            enhanced_data, 
            PlatformType.TELEGRAM.value
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
            telegram_id, 
            enhanced_order_data, 
            PlatformType.TELEGRAM.value
        )
        
        if order_id:
            logger.info(f"✅ Telegram order created: {order_id} for user {telegram_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(telegram_id: int) -> Dict:
        """Получить информацию о лояльности"""
        loyalty_info = fault_tolerant_db.get_loyalty_with_fallback(telegram_id, PlatformType.TELEGRAM.value)
        
        # Добавляем Telegram-специфичную информацию
        loyalty_info['platform'] = PlatformType.TELEGRAM.value
        loyalty_info['telegram_id'] = telegram_id
        loyalty_info['can_use_bot_commands'] = True
        
        return loyalty_info
    
    @staticmethod
    def get_user_orders(telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получить заказы пользователя"""
        try:
            # Пытаемся получить из кэша сначала
            cache_key = f"orders_telegram_{telegram_id}"
            cached_orders = fault_tolerant_db.local_cache.get(cache_key)
            
            if cached_orders:
                return cached_orders[:limit]
            
            # Если нет в кэше, возвращаем пустой список (можно расширить)
            return []
            
        except Exception as e:
            logger.error(f"Error getting Telegram user orders: {e}")
            return []
    
    @staticmethod
    def _generate_user_uuid(telegram_id: int) -> str:
        """Генерация UUID для Telegram пользователя"""
        combined_id = f"telegram_{telegram_id}"
        hash_object = hashlib.md5(combined_id.encode())
        return str(uuid.UUID(hash_object.hexdigest()))

class WebsiteAdapter:
    """Адаптер для веб-сайта"""
    
    @staticmethod
    def create_user(email: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя сайта"""
        enhanced_data = {
            **user_data,
            'email': email,
            'platform': PlatformType.WEBSITE.value,
            'user_type': 'website_user',
            'email_verified': user_data.get('email_verified', False)
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            email, 
            enhanced_data, 
            PlatformType.WEBSITE.value
        )
        
        if success:
            user_uuid = WebsiteAdapter._generate_user_uuid(email)
            logger.info(f"✅ Website user created: {email}")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(email: str) -> Optional[Dict]:
        """Получить информацию о пользователе сайта"""
        user_info = fault_tolerant_db.get_user_with_fallback(email, PlatformType.WEBSITE.value)
        
        if user_info:
            user_info['platform'] = PlatformType.WEBSITE.value
            user_info['email'] = email
            user_info['is_web_user'] = True
            user_info['can_receive_emails'] = True
            
        return user_info
    
    @staticmethod
    def create_order(email: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от веб-пользователя"""
        enhanced_order_data = {
            **order_data,
            'platform': PlatformType.WEBSITE.value,
            'source': 'website',
            'user_email': email,
            'payment_method': order_data.get('payment_method', 'card')
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            email, 
            enhanced_order_data, 
            PlatformType.WEBSITE.value
        )
        
        if order_id:
            logger.info(f"✅ Website order created: {order_id} for user {email}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(email: str) -> Dict:
        """Получить информацию о лояльности"""
        loyalty_info = fault_tolerant_db.get_loyalty_with_fallback(email, PlatformType.WEBSITE.value)
        
        loyalty_info['platform'] = PlatformType.WEBSITE.value
        loyalty_info['email'] = email
        loyalty_info['can_redeem_online'] = True
        
        return loyalty_info
    
    @staticmethod
    def link_telegram_account(email: str, telegram_id: int) -> bool:
        """Связать аккаунт сайта с Telegram"""
        try:
            # Получаем информацию о пользователе сайта
            website_user = WebsiteAdapter.get_user_info(email)
            telegram_user = TelegramAdapter.get_user_info(telegram_id)
            
            if not website_user:
                logger.error(f"Website user not found: {email}")
                return False
            
            # Создаем связь в кэше
            link_data = {
                'email': email,
                'telegram_id': telegram_id,
                'linked_at': datetime.utcnow().isoformat(),
                'link_type': 'email_telegram'
            }
            
            # Сохраняем связь в обе стороны
            fault_tolerant_db.local_cache.set(f"link_email_{email}", {
                'telegram_id': telegram_id,
                'linked_at': link_data['linked_at']
            }, ttl=86400)  # 24 часа
            
            fault_tolerant_db.local_cache.set(f"link_telegram_{telegram_id}", {
                'email': email,
                'linked_at': link_data['linked_at']
            }, ttl=86400)
            
            logger.info(f"✅ Accounts linked: {email} <-> {telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error linking accounts: {e}")
            return False
    
    @staticmethod
    def get_linked_telegram(email: str) -> Optional[int]:
        """Получить связанный Telegram ID"""
        try:
            link_data = fault_tolerant_db.local_cache.get(f"link_email_{email}")
            return link_data.get('telegram_id') if link_data else None
        except Exception as e:
            logger.error(f"Error getting linked Telegram: {e}")
            return None
    
    @staticmethod
    def update_user_profile(email: str, profile_data: Dict) -> bool:
        """Обновить профиль пользователя"""
        try:
            current_user = WebsiteAdapter.get_user_info(email)
            if not current_user:
                return False
            
            # Обновляем данные
            updated_data = {**current_user, **profile_data}
            updated_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Сохраняем в кэш
            fault_tolerant_db.local_cache.set_user_data(email, PlatformType.WEBSITE.value, updated_data)
            
            logger.info(f"✅ Website user profile updated: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating website user profile: {e}")
            return False
    
    @staticmethod
    def _generate_user_uuid(email: str) -> str:
        """Генерация UUID для веб-пользователя"""
        combined_id = f"website_{email}"
        hash_object = hashlib.md5(combined_id.encode())
        return str(uuid.UUID(hash_object.hexdigest()))

class MobileAppAdapter:
    """Адаптер для мобильного приложения"""
    
    @staticmethod
    def create_user(device_id: str, platform_type: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя мобильного приложения"""
        enhanced_data = {
            **user_data,
            'device_id': device_id,
            'platform': platform_type,
            'user_type': 'mobile_user',
            'device_type': 'ios' if 'ios' in platform_type.lower() else 'android',
            'app_version': user_data.get('app_version', '1.0.0'),
            'push_token': user_data.get('push_token')
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            device_id, 
            enhanced_data, 
            platform_type
        )
        
        if success:
            user_uuid = MobileAppAdapter._generate_user_uuid(device_id, platform_type)
            logger.info(f"✅ Mobile user created: {device_id} ({platform_type})")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(device_id: str, platform_type: str) -> Optional[Dict]:
        """Получить информацию о пользователе приложения"""
        user_info = fault_tolerant_db.get_user_with_fallback(device_id, platform_type)
        
        if user_info:
            user_info['platform'] = platform_type
            user_info['device_id'] = device_id
            user_info['is_mobile_user'] = True
            user_info['can_receive_push'] = bool(user_info.get('push_token'))
            user_info['device_type'] = 'ios' if 'ios' in platform_type.lower() else 'android'
            
        return user_info
    
    @staticmethod
    def create_order(device_id: str, platform_type: str, order_data: Dict) -> Optional[int]:
        """Создать заказ от мобильного пользователя"""
        enhanced_order_data = {
            **order_data,
            'platform': platform_type,
            'source': 'mobile_app',
            'device_id': device_id,
            'device_type': 'ios' if 'ios' in platform_type.lower() else 'android',
            'app_version': order_data.get('app_version', '1.0.0')
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            device_id, 
            enhanced_order_data, 
            platform_type
        )
        
        if order_id:
            logger.info(f"✅ Mobile order created: {order_id} for device {device_id}")
        
        return order_id
    
    @staticmethod
    def get_loyalty_info(device_id: str, platform_type: str) -> Dict:
        """Получить информацию о лояльности"""
        loyalty_info = fault_tolerant_db.get_loyalty_with_fallback(device_id, platform_type)
        
        loyalty_info['platform'] = platform_type
        loyalty_info['device_id'] = device_id
        loyalty_info['can_use_mobile_features'] = True
        loyalty_info['device_type'] = 'ios' if 'ios' in platform_type.lower() else 'android'
        
        return loyalty_info
    
    @staticmethod
    def sync_user_data(device_id: str, platform_type: str, sync_data: Dict) -> Dict:
        """Синхронизировать данные мобильного приложения"""
        try:
            current_user = MobileAppAdapter.get_user_info(device_id, platform_type)
            
            if not current_user:
                return {'status': 'user_not_found', 'synced': False}
            
            # Обновляем данные синхронизации
            sync_info = {
                'last_sync': datetime.utcnow().isoformat(),
                'sync_data': sync_data,
                'sync_version': sync_data.get('version', '1.0'),
                'device_info': {
                    'platform': platform_type,
                    'device_id': device_id,
                    'app_version': sync_data.get('app_version', '1.0.0')
                }
            }
            
            # Объединяем с текущими данными
            updated_user = {**current_user, **sync_info}
            
            # Сохраняем в кэш
            fault_tolerant_db.local_cache.set_user_data(device_id, platform_type, updated_user)
            
            logger.info(f"✅ Mobile data synced for device: {device_id}")
            
            return {
                'status': 'synced',
                'last_sync': sync_info['last_sync'],
                'user_info': updated_user,
                'platform': platform_type
            }
            
        except Exception as e:
            logger.error(f"Error syncing mobile data: {e}")
            return {'status': 'error', 'message': str(e), 'synced': False}
    
    @staticmethod
    def register_push_token(device_id: str, platform_type: str, push_token: str) -> bool:
        """Зарегистрировать токен для push уведомлений"""
        try:
            current_user = MobileAppAdapter.get_user_info(device_id, platform_type)
            
            if not current_user:
                return False
            
            # Обновляем push токен
            current_user['push_token'] = push_token
            current_user['push_registered_at'] = datetime.utcnow().isoformat()
            
            # Сохраняем
            fault_tolerant_db.local_cache.set_user_data(device_id, platform_type, current_user)
            
            logger.info(f"✅ Push token registered for device: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering push token: {e}")
            return False
    
    @staticmethod
    def link_accounts(device_id: str, platform_type: str, account_data: Dict) -> bool:
        """Связать мобильный аккаунт с другими платформами"""
        try:
            link_data = {
                'device_id': device_id,
                'platform': platform_type,
                'linked_accounts': account_data,
                'linked_at': datetime.utcnow().isoformat()
            }
            
            # Сохраняем связи
            for account_type, account_id in account_data.items():
                if account_type == 'telegram_id':
                    fault_tolerant_db.local_cache.set(f"link_mobile_{device_id}_telegram", {
                        'telegram_id': account_id,
                        'linked_at': link_data['linked_at']
                    }, ttl=86400)
                    
                elif account_type == 'email':
                    fault_tolerant_db.local_cache.set(f"link_mobile_{device_id}_email", {
                        'email': account_id,
                        'linked_at': link_data['linked_at']
                    }, ttl=86400)
            
            logger.info(f"✅ Mobile accounts linked for device: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error linking mobile accounts: {e}")
            return False
    
    @staticmethod
    def _generate_user_uuid(device_id: str, platform_type: str) -> str:
        """Генерация UUID для мобильного пользователя"""
        combined_id = f"mobile_{platform_type}_{device_id}"
        hash_object = hashlib.md5(combined_id.encode())
        return str(uuid.UUID(hash_object.hexdigest()))

class DesktopAppAdapter:
    """Адаптер для десктопного приложения"""
    
    @staticmethod
    def create_user(user_id: str, platform_type: str, user_data: Dict) -> Optional[str]:
        """Создать пользователя десктопного приложения"""
        enhanced_data = {
            **user_data,
            'desktop_user_id': user_id,
            'platform': platform_type,
            'user_type': 'desktop_user',
            'os_type': platform_type.replace('desktop_', ''),
            'app_version': user_data.get('app_version', '1.0.0')
        }
        
        success = fault_tolerant_db.create_user_with_fallback(
            user_id, 
            enhanced_data, 
            platform_type
        )
        
        if success:
            user_uuid = DesktopAppAdapter._generate_user_uuid(user_id, platform_type)
            logger.info(f"✅ Desktop user created: {user_id} ({platform_type})")
            return user_uuid
        
        return None
    
    @staticmethod
    def get_user_info(user_id: str, platform_type: str) -> Optional[Dict]:
        """Получить информацию о пользователе десктопа"""
        user_info = fault_tolerant_db.get_user_with_fallback(user_id, platform_type)
        
        if user_info:
            user_info['platform'] = platform_type
            user_info['desktop_user_id'] = user_id
            user_info['is_desktop_user'] = True
            user_info['os_type'] = platform_type.replace('desktop_', '')
            
        return user_info
    
    @staticmethod
    def sync_with_cloud(user_id: str, platform_type: str, cloud_data: Dict) -> Dict:
        """Синхронизировать данные с облаком"""
        try:
            current_user = DesktopAppAdapter.get_user_info(user_id, platform_type)
            
            if not current_user:
                return {'status': 'user_not_found'}
            
            # Данные синхронизации
            sync_info = {
                'last_cloud_sync': datetime.utcnow().isoformat(),
                'cloud_data': cloud_data,
                'sync_version': cloud_data.get('version', '1.0')
            }
            
            updated_user = {**current_user, **sync_info}
            fault_tolerant_db.local_cache.set_user_data(user_id, platform_type, updated_user)
            
            logger.info(f"✅ Desktop cloud sync completed for: {user_id}")
            
            return {
                'status': 'synced',
                'last_sync': sync_info['last_cloud_sync'],
                'platform': platform_type
            }
            
        except Exception as e:
            logger.error(f"Error syncing desktop data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def _generate_user_uuid(user_id: str, platform_type: str) -> str:
        """Генерация UUID для десктопного пользователя"""
        combined_id = f"desktop_{platform_type}_{user_id}"
        hash_object = hashlib.md5(combined_id.encode())
        return str(uuid.UUID(hash_object.hexdigest()))

class APIAdapter:
    """Адаптер для партнерского API"""
    
    @staticmethod
    def create_external_order(api_key: str, external_user_id: str, order_data: Dict) -> Optional[int]:
        """Создать заказ через партнерский API"""
        # Валидация API ключа
        if not APIAdapter._validate_api_key(api_key):
            logger.warning(f"Invalid API key used: {api_key[:10]}...")
            return None
        
        enhanced_data = {
            **order_data,
            'external_user_id': external_user_id,
            'api_key_hash': hashlib.sha256(api_key.encode()).hexdigest()[:16],
            'source': 'partner_api',
            'platform': 'api_partner'
        }
        
        order_id = fault_tolerant_db.create_order_with_fallback(
            external_user_id, 
            enhanced_data, 
            'api_partner'
        )
        
        if order_id:
            logger.info(f"✅ API order created: {order_id} for external user {external_user_id}")
        
        return order_id
    
    @staticmethod
    def get_external_user_info(api_key: str, external_user_id: str) -> Optional[Dict]:
        """Получить информацию о внешнем пользователе"""
        if not APIAdapter._validate_api_key(api_key):
            return None
        
        user_info = fault_tolerant_db.get_user_with_fallback(external_user_id, 'api_partner')
        
        if user_info:
            # Убираем чувствительную информацию для API
            safe_info = {
                'external_user_id': external_user_id,
                'platform': 'api_partner',
                'created_at': user_info.get('created_at'),
                'last_order_at': user_info.get('last_order_at')
            }
            return safe_info
        
        return None
    
    @staticmethod
    def _validate_api_key(api_key: str) -> bool:
        """Валидация API ключа партнера"""
        # Простая проверка для примера - в реальности должна быть база ключей
        if not api_key or len(api_key) < 32:
            return False
        
        # Здесь должна быть проверка в базе данных или кэше
        valid_prefixes = ['pk_live_', 'pk_test_', 'api_key_']
        return any(api_key.startswith(prefix) for prefix in valid_prefixes)

class UniversalAdapter:
    """Универсальный адаптер для всех платформ"""
    
    @staticmethod
    def get_adapters() -> Dict:
        """Получить все доступные адаптеры"""
        return {
            'telegram': TelegramAdapter,
            'website': WebsiteAdapter,
            'mobile_ios': MobileAppAdapter,
            'mobile_android': MobileAppAdapter,
            'desktop_windows': DesktopAppAdapter,
            'desktop_mac': DesktopAppAdapter,
            'desktop_linux': DesktopAppAdapter,
            'api_partner': APIAdapter
        }
    
    @staticmethod
    def route_request(platform: str, method: str, *args, **kwargs):
        """Маршрутизировать запрос к правильному адаптеру"""
        adapters = UniversalAdapter.get_adapters()
        
        if platform not in adapters:
            logger.error(f"Unknown platform: {platform}")
            return None
        
        adapter = adapters[platform]
        
        if not hasattr(adapter, method):
            logger.error(f"Method {method} not found in {platform} adapter")
            return None
        
        try:
            result = getattr(adapter, method)(*args, **kwargs)
            logger.info(f"✅ {platform}.{method} executed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ Error executing {method} on {platform}: {e}")
            return None
    
    @staticmethod
    def get_user_across_platforms(identifiers: Dict) -> Optional[Dict]:
        """Найти пользователя по любому идентификатору с любой платформы"""
        # Пытаемся найти по Telegram ID
        if 'telegram_id' in identifiers:
            user_info = TelegramAdapter.get_user_info(identifiers['telegram_id'])
            if user_info:
                user_info['found_via'] = 'telegram'
                return user_info
        
        # Пытаемся найти по email
        if 'email' in identifiers:
            user_info = WebsiteAdapter.get_user_info(identifiers['email'])
            if user_info:
                user_info['found_via'] = 'email'
                return user_info
        
        # Пытаемся найти по device_id
        if 'device_id' in identifiers:
            for platform in ['mobile_ios', 'mobile_android']:
                user_info = MobileAppAdapter.get_user_info(identifiers['device_id'], platform)
                if user_info:
                    user_info['found_via'] = 'device_id'
                    return user_info
        
        # Пытаемся найти по desktop_user_id
        if 'desktop_user_id' in identifiers:
            for platform in ['desktop_windows', 'desktop_mac', 'desktop_linux']:
                user_info = DesktopAppAdapter.get_user_info(identifiers['desktop_user_id'], platform)
                if user_info:
                    user_info['found_via'] = 'desktop_user_id'
                    return user_info
        
        return None
    
    @staticmethod
    def create_cross_platform_order(user_identifiers: Dict, order_data: Dict, primary_platform: str) -> Optional[int]:
        """Создать заказ с поддержкой кросс-платформенности"""
        # Определяем основной идентификатор пользователя
        if primary_platform == 'telegram' and 'telegram_id' in user_identifiers:
            return TelegramAdapter.create_order(user_identifiers['telegram_id'], order_data)
        elif primary_platform == 'website' and 'email' in user_identifiers:
            return WebsiteAdapter.create_order(user_identifiers['email'], order_data)
        elif primary_platform in ['mobile_ios', 'mobile_android'] and 'device_id' in user_identifiers:
            return MobileAppAdapter.create_order(user_identifiers['device_id'], primary_platform, order_data)
        elif primary_platform.startswith('desktop_') and 'desktop_user_id' in user_identifiers:
            return DesktopAppAdapter.create_order(user_identifiers['desktop_user_id'], primary_platform, order_data)
        
        # Если основная платформа недоступна, пытаемся через другие
        for platform, identifier_key in [
            ('telegram', 'telegram_id'),
            ('website', 'email'),
            ('mobile_ios', 'device_id'),
            ('mobile_android', 'device_id')
        ]:
            if identifier_key in user_identifiers:
                try:
                    if platform == 'telegram':
                        return TelegramAdapter.create_order(user_identifiers[identifier_key], order_data)
                    elif platform == 'website':
                        return WebsiteAdapter.create_order(user_identifiers[identifier_key], order_data)
                    elif platform in ['mobile_ios', 'mobile_android']:
                        return MobileAppAdapter.create_order(user_identifiers[identifier_key], platform, order_data)
                except Exception as e:
                    logger.error(f"Failed to create order via {platform}: {e}")
                    continue
        
        return None
    
    @staticmethod
    def get_unified_loyalty_info(user_identifiers: Dict) -> Dict:
        """Получить объединенную информацию о лояльности со всех платформ"""
        loyalty_data = {
            'total_points': 0,
            'partner_cards': [],
            'history': [],
            'platforms': [],
            'last_activity': None,
            'unified_at': datetime.utcnow().isoformat()
        }
        
        # Собираем данные с каждой платформы
        platforms_checked = []
        
        for platform, identifier_key in [
            ('telegram', 'telegram_id'),
            ('website', 'email'),
            ('mobile_ios', 'device_id'),
            ('mobile_android', 'device_id')
        ]:
            if identifier_key in user_identifiers:
                try:
                    if platform == 'telegram':
                        platform_loyalty = TelegramAdapter.get_loyalty_info(user_identifiers[identifier_key])
                    elif platform == 'website':
                        platform_loyalty = WebsiteAdapter.get_loyalty_info(user_identifiers[identifier_key])
                    elif platform in ['mobile_ios', 'mobile_android']:
                        platform_loyalty = MobileAppAdapter.get_loyalty_info(user_identifiers[identifier_key], platform)
                    else:
                        continue
                    
                    if platform_loyalty and platform_loyalty.get('current_points', 0) > 0:
                        # Берем максимальное количество баллов (они должны быть синхронизированы)
                        loyalty_data['total_points'] = max(loyalty_data['total_points'], platform_loyalty['current_points'])
                        
                        # Собираем партнерские карты
                        if platform_loyalty.get('partner_cards'):
                            loyalty_data['partner_cards'].extend(platform_loyalty['partner_cards'])
                        
                        # Собираем историю
                        if platform_loyalty.get('recent_history'):
                            loyalty_data['history'].extend(platform_loyalty['recent_history'])
                        
                        # Отмечаем платформу
                        loyalty_data['platforms'].append(platform)
                        platforms_checked.append(platform)
                        
                except Exception as e:
                    logger.error(f"Error getting loyalty from {platform}: {e}")
        
        # Убираем дубликаты партнерских карт
        unique_cards = {}
        for card in loyalty_data['partner_cards']:
            card_id = card.get('card_id') or card.get('id')
            if card_id and card_id not in unique_cards:
                unique_cards[card_id] = card
        loyalty_data['partner_cards'] = list(unique_cards.values())
        
        # Сортируем историю по дате
        loyalty_data['history'].sort(key=lambda x: x.get('created_at', ''), reverse=True)
        loyalty_data['history'] = loyalty_data['history'][:10]  # Последние 10 записей
        
        # Определяем последнюю активность
        if loyalty_data['history']:
            loyalty_data['last_activity'] = loyalty_data['history'][0].get('created_at')
        
        loyalty_data['platforms_checked'] = platforms_checked
        
        return loyalty_data
    
    @staticmethod
    def sync_user_across_platforms(primary_identifier: str, primary_platform: str, sync_data: Dict) -> Dict:
        """Синхронизировать пользователя между всеми связанными платформами"""
        try:
            sync_results = {
                'primary_platform': primary_platform,
                'primary_identifier': primary_identifier,
                'synced_platforms': [],
                'failed_platforms': [],
                'sync_timestamp': datetime.utcnow().isoformat()
            }
            
            # Получаем информацию о связанных аккаунтах
            linked_accounts = UniversalAdapter._get_linked_accounts(primary_identifier, primary_platform)
            
            # Синхронизируем с каждой связанной платформой
            for platform, identifier in linked_accounts.items():
                try:
                    if platform == 'telegram':
                        # Обновляем кэш Telegram пользователя
                        current_user = TelegramAdapter.get_user_info(identifier)
                        if current_user:
                            updated_user = {**current_user, **sync_data}
                            fault_tolerant_db.local_cache.set_user_data(identifier, platform, updated_user)
                            sync_results['synced_platforms'].append(platform)
                    
                    elif platform == 'website':
                        success = WebsiteAdapter.update_user_profile(identifier, sync_data)
                        if success:
                            sync_results['synced_platforms'].append(platform)
                        else:
                            sync_results['failed_platforms'].append(platform)
                    
                    elif platform in ['mobile_ios', 'mobile_android']:
                        result = MobileAppAdapter.sync_user_data(identifier, platform, sync_data)
                        if result.get('status') == 'synced':
                            sync_results['synced_platforms'].append(platform)
                        else:
                            sync_results['failed_platforms'].append(platform)
                    
                except Exception as e:
                    logger.error(f"Error syncing with {platform}: {e}")
                    sync_results['failed_platforms'].append(platform)
            
            logger.info(f"✅ User sync completed: {len(sync_results['synced_platforms'])} platforms synced")
            return sync_results
            
        except Exception as e:
            logger.error(f"Error in cross-platform sync: {e}")
            return {
                'error': str(e),
                'sync_timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _get_linked_accounts(identifier: str, platform: str) -> Dict:
        """Получить связанные аккаунты пользователя"""
        linked_accounts = {}
        
        try:
            if platform == 'telegram':
                # Ищем связанные email
                email_link = fault_tolerant_db.local_cache.get(f"link_telegram_{identifier}")
                if email_link and email_link.get('email'):
                    linked_accounts['website'] = email_link['email']
            
            elif platform == 'website':
                # Ищем связанный Telegram
                telegram_link = fault_tolerant_db.local_cache.get(f"link_email_{identifier}")
                if telegram_link and telegram_link.get('telegram_id'):
                    linked_accounts['telegram'] = telegram_link['telegram_id']
            
            elif platform.startswith('mobile_'):
                # Ищем связанные аккаунты для мобильного
                telegram_link = fault_tolerant_db.local_cache.get(f"link_mobile_{identifier}_telegram")
                if telegram_link and telegram_link.get('telegram_id'):
                    linked_accounts['telegram'] = telegram_link['telegram_id']
                
                email_link = fault_tolerant_db.local_cache.get(f"link_mobile_{identifier}_email")
                if email_link and email_link.get('email'):
                    linked_accounts['website'] = email_link['email']
            
        except Exception as e:
            logger.error(f"Error getting linked accounts: {e}")
        
        return linked_accounts
    
    @staticmethod
    def get_platform_statistics() -> Dict:
        """Получить статистику по всем платформам"""
        try:
            stats = {
                'total_platforms': len(UniversalAdapter.get_adapters()),
                'platform_usage': {},
                'cross_platform_links': 0,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Подсчитываем использование платформ из кэша
            cache_stats = fault_tolerant_db.local_cache.get_cache_stats()
            stats['cache_items'] = cache_stats['total_items']
            
            # Подсчитываем количество связей между платформами
            for key in fault_tolerant_db.local_cache.cache.keys():
                if key.startswith('link_'):
                    stats['cross_platform_links'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting platform statistics: {e}")
            return {'error': str(e)}
