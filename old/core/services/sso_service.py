"""
SSO (Single Sign-On) сервис для безопасных переходов в Odoo WebApp
Создает JWT токены с TTL для аутентификации пользователей в веб-интерфейсе
"""
import jwt
import time
import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SSOService:
    """
    Сервис для создания и валидации SSO токенов
    """
    
    def __init__(self):
        self.secret = self._get_jwt_secret()
        self.ttl = 600  # 10 минут TTL по умолчанию
        self.algorithm = 'HS256'
    
    def _get_jwt_secret(self) -> str:
        """
        Получить секретный ключ для JWT из переменных окружения
        
        Returns:
            str: Секретный ключ для подписи JWT
        """
        import os
        secret = os.getenv('JWT_SECRET')
        if not secret:
            # Fallback к SECRET_KEY если JWT_SECRET не установлен
            secret = os.getenv('SECRET_KEY')
            if not secret:
                raise ValueError("JWT_SECRET or SECRET_KEY environment variable is required!")
        return secret
    
    def _device_fingerprint(self, telegram_id: int) -> str:
        """
        Генерация отпечатка устройства для дополнительной безопасности
        
        Args:
            telegram_id: ID пользователя Telegram
            
        Returns:
            str: Хэш отпечатка устройства
        """
        import os
        # Используем комбинацию данных для уникального отпечатка
        data = f"{telegram_id}_{os.getenv('BOT_TOKEN', '')[:10]}_{int(time.time()//3600)}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    async def create_sso_token(self, 
                              telegram_id: int, 
                              role: str,
                              permissions: Optional[list] = None,
                              custom_ttl: Optional[int] = None) -> str:
        """
        Создать безопасный SSO токен для перехода в Odoo WebApp
        
        Args:
            telegram_id: ID пользователя Telegram
            role: Роль пользователя (user, partner, admin, super_admin)
            permissions: Список разрешений (опционально)
            custom_ttl: Кастомный TTL в секундах (опционально)
            
        Returns:
            str: JWT токен для SSO
        """
        try:
            current_time = int(time.time())
            ttl = custom_ttl or self.ttl
            
            # Базовый payload
            payload = {
                'telegram_id': str(telegram_id),
                'role': role,
                'iat': current_time,  # issued at
                'exp': current_time + ttl,  # expires at
                'session_id': f"tg_{telegram_id}_{current_time}",
                'device_fingerprint': self._device_fingerprint(telegram_id),
                'iss': 'karmabot',  # issuer
                'aud': 'odoo_webapp'  # audience
            }
            
            # Добавить разрешения если указаны
            if permissions:
                payload['permissions'] = permissions
            
            # Добавить роль-специфичные данные
            payload.update(self._get_role_specific_data(telegram_id, role))
            
            # Создать токен
            token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
            
            # Логировать создание токена
            logger.info(f"SSO token created for user {telegram_id} (role: {role}, TTL: {ttl}s)")
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating SSO token for user {telegram_id}: {e}")
            raise
    
    def _get_role_specific_data(self, telegram_id: int, role: str) -> Dict[str, Any]:
        """
        Получить данные специфичные для роли
        
        Args:
            telegram_id: ID пользователя Telegram
            role: Роль пользователя
            
        Returns:
            Dict с дополнительными данными
        """
        data = {}
        
        if role in ['partner', 'admin', 'super_admin']:
            # Для партнеров и админов добавить информацию о партнерстве
            try:
                from core.database.db_v2 import db_v2
                partner = db_v2.get_partner_by_telegram_id(telegram_id)
                if partner:
                    data['partner_id'] = partner.get('id')
                    data['partner_name'] = partner.get('display_name')
            except Exception as e:
                logger.warning(f"Could not get partner data for {telegram_id}: {e}")
        
        if role in ['admin', 'super_admin']:
            # Для админов добавить уровень доступа
            data['admin_level'] = 'super' if role == 'super_admin' else 'admin'
            data['admin_permissions'] = self._get_admin_permissions(role)
        
        return data
    
    def _get_admin_permissions(self, role: str) -> list:
        """
        Получить список разрешений для админа
        
        Args:
            role: Роль админа
            
        Returns:
            list: Список разрешений
        """
        base_permissions = [
            'view_users',
            'view_partners', 
            'view_cards',
            'moderate_cards',
            'view_statistics'
        ]
        
        if role == 'super_admin':
            base_permissions.extend([
                'manage_admins',
                'system_settings',
                'delete_users',
                'delete_partners',
                'manage_loyalty',
                'view_logs'
            ])
        
        return base_permissions
    
    def validate_sso_token(self, token: str) -> Dict[str, Any]:
        """
        Валидировать SSO токен
        
        Args:
            token: JWT токен для валидации
            
        Returns:
            Dict с данными токена если валиден
            
        Raises:
            jwt.ExpiredSignatureError: Токен истек
            jwt.InvalidTokenError: Токен невалиден
        """
        try:
            # Декодировать токен
            payload = jwt.decode(
                token, 
                self.secret, 
                algorithms=[self.algorithm],
                audience='odoo_webapp',
                issuer='karmabot'
            )
            
            # Проверить отпечаток устройства
            telegram_id = int(payload['telegram_id'])
            expected_fingerprint = self._device_fingerprint(telegram_id)
            if payload.get('device_fingerprint') != expected_fingerprint:
                raise jwt.InvalidTokenError("Invalid device fingerprint")
            
            logger.info(f"SSO token validated for user {telegram_id}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"SSO token expired: {token[:20]}...")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid SSO token: {e}")
            raise
    
    async def refresh_sso_token(self, token: str, new_ttl: Optional[int] = None) -> str:
        """
        Обновить SSO токен (создать новый с теми же данными)
        
        Args:
            token: Старый токен
            new_ttl: Новый TTL (опционально)
            
        Returns:
            str: Новый токен
        """
        try:
            # Валидировать старый токен
            payload = self.validate_sso_token(token)
            
            # Создать новый токен с теми же данными
            telegram_id = int(payload['telegram_id'])
            role = payload['role']
            permissions = payload.get('permissions')
            
            # Создать новый токен с новым временем
            return await self.create_sso_token(telegram_id, role, permissions, new_ttl)
            
        except Exception as e:
            logger.error(f"Error refreshing SSO token: {e}")
            raise
    
    async def create_webapp_url(self, 
                         telegram_id: int, 
                         role: str, 
                         webapp_path: str,
                         permissions: Optional[list] = None) -> str:
        """
        Создать полный URL для WebApp с SSO токеном
        
        Args:
            telegram_id: ID пользователя Telegram
            role: Роль пользователя
            webapp_path: Путь в WebApp (например, '/partner/cards')
            permissions: Список разрешений (опционально)
            
        Returns:
            str: Полный URL с SSO токеном
        """
        try:
            # Создать токен
            token = await self.create_sso_token(telegram_id, role, permissions)
            
            # Получить базовый URL Odoo
            import os
            odoo_base_url = os.getenv('ODOO_BASE_URL', 'https://odoo.example.com')
            
            # Создать URL
            webapp_url = f"{odoo_base_url}{webapp_path}?sso={token}"
            
            logger.info(f"WebApp URL created for user {telegram_id}: {webapp_path}")
            return webapp_url
            
        except Exception as e:
            logger.error(f"Error creating WebApp URL for user {telegram_id}: {e}")
            raise
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Получить информацию о токене без валидации (для отладки)
        
        Args:
            token: JWT токен
            
        Returns:
            Dict с информацией о токене
        """
        try:
            # Декодировать без проверки подписи
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Вычислить оставшееся время
            current_time = int(time.time())
            expires_at = payload.get('exp', 0)
            remaining_time = max(0, expires_at - current_time)
            
            return {
                'telegram_id': payload.get('telegram_id'),
                'role': payload.get('role'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                'expires_at': datetime.fromtimestamp(expires_at),
                'remaining_seconds': remaining_time,
                'is_expired': remaining_time == 0,
                'permissions': payload.get('permissions', []),
                'session_id': payload.get('session_id')
            }
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return {'error': str(e)}


# Глобальный экземпляр сервиса
sso_service = SSOService()


# Утилитарные функции для удобства использования
async def create_partner_sso_token(telegram_id: int) -> str:
    """Создать SSO токен для партнера"""
    return await sso_service.create_sso_token(telegram_id, 'partner')


async def create_admin_sso_token(telegram_id: int, admin_level: str = 'admin') -> str:
    """Создать SSO токен для админа"""
    return await sso_service.create_sso_token(telegram_id, admin_level)


async def create_user_sso_token(telegram_id: int) -> str:
    """Создать SSO токен для обычного пользователя"""
    return await sso_service.create_sso_token(telegram_id, 'user')


async def create_webapp_button(url_path: str, title: str, user_data: dict) -> str:
    """
    Создать URL для WebApp кнопки
    
    Args:
        url_path: Путь в WebApp
        title: Название кнопки (для логирования)
        user_data: Данные пользователя {'id': int, 'role': str}
        
    Returns:
        str: URL для WebApp кнопки
    """
    try:
        telegram_id = user_data['id']
        role = user_data['role']
        
        return await sso_service.create_webapp_url(telegram_id, role, url_path)
        
    except Exception as e:
        logger.error(f"Error creating WebApp button URL: {e}")
        return "#"
