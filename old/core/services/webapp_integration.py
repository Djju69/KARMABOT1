"""
Простая интеграция с Odoo WebApp без API модуля
Использует параметры URL с подписью для безопасности
"""
import time
import hashlib
import hmac
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class WebAppIntegration:
    """Простая интеграция с Odoo WebApp"""
    
    def __init__(self):
        self.secret = self._get_secret()
        self.ttl = 600  # 10 минут
    
    def _get_secret(self) -> str:
        """Получить секретный ключ"""
        secret = os.getenv('SECRET_KEY')
        if not secret:
            raise ValueError("SECRET_KEY environment variable is required!")
        return secret
    
    def create_webapp_url(self, 
                         telegram_id: int, 
                         role: str, 
                         webapp_path: str,
                         additional_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Создать URL для WebApp с параметрами
        
        Args:
            telegram_id: ID пользователя Telegram
            role: Роль пользователя
            webapp_path: Путь в WebApp
            additional_params: Дополнительные параметры
            
        Returns:
            str: URL для WebApp
        """
        try:
            # Базовые параметры
            current_time = int(time.time())
            params = {
                'tg_user_id': telegram_id,
                'tg_role': role,
                'tg_timestamp': current_time,
                'tg_expires': current_time + self.ttl
            }
            
            # Добавить дополнительные параметры
            if additional_params:
                params.update(additional_params)
            
            # Создать подпись
            signature = self._create_signature(params)
            params['tg_signature'] = signature
            
            # Создать URL
            odoo_base_url = os.getenv('ODOO_BASE_URL', 'https://odoo-crm-production.up.railway.app')
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            
            webapp_url = f"{odoo_base_url}{webapp_path}?{param_string}"
            
            logger.info(f"WebApp URL created for user {telegram_id}: {webapp_path}")
            return webapp_url
            
        except Exception as e:
            logger.error(f"Error creating WebApp URL: {e}")
            return "#"
    
    def _create_signature(self, params: Dict[str, Any]) -> str:
        """Создать подпись для параметров"""
        # Создать строку для подписи
        signature_data = f"{params['tg_user_id']}:{params['tg_role']}:{params['tg_timestamp']}"
        
        # Создать HMAC подпись
        signature = hmac.new(
            self.secret.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()[:16]  # Первые 16 символов
        
        return signature
    
    def validate_webapp_params(self, params: Dict[str, Any]) -> bool:
        """Валидировать параметры WebApp"""
        try:
            # Проверить обязательные параметры
            required_params = ['tg_user_id', 'tg_role', 'tg_timestamp', 'tg_signature']
            for param in required_params:
                if param not in params:
                    return False
            
            # Проверить время истечения
            current_time = int(time.time())
            if params.get('tg_expires', 0) < current_time:
                return False
            
            # Проверить подпись
            expected_signature = self._create_signature(params)
            if params['tg_signature'] != expected_signature:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating WebApp params: {e}")
            return False
    
    def create_partner_webapp_url(self, telegram_id: int, partner_id: Optional[int] = None) -> str:
        """Создать URL для партнерского WebApp"""
        additional_params = {}
        if partner_id:
            additional_params['partner_id'] = partner_id
        
        return self.create_webapp_url(
            telegram_id=telegram_id,
            role='partner',
            webapp_path='/my/partner',
            additional_params=additional_params
        )
    
    def create_admin_webapp_url(self, telegram_id: int, admin_level: str = 'admin') -> str:
        """Создать URL для админского WebApp"""
        if admin_level == 'super_admin':
            webapp_path = '/super-admin'
        else:
            webapp_path = '/admin'
        
        return self.create_webapp_url(
            telegram_id=telegram_id,
            role=admin_level,
            webapp_path=webapp_path,
            additional_params={'admin_level': admin_level}
        )
    
    def create_user_webapp_url(self, telegram_id: int) -> str:
        """Создать URL для пользовательского WebApp"""
        return self.create_webapp_url(
            telegram_id=telegram_id,
            role='user',
            webapp_path='/my/profile',
            additional_params={}
        )


# Глобальный экземпляр
webapp_integration = WebAppIntegration()


# Утилитарные функции
def create_partner_webapp_button(telegram_id: int, partner_id: Optional[int] = None) -> str:
    """Создать URL для партнерской кнопки WebApp"""
    return webapp_integration.create_partner_webapp_url(telegram_id, partner_id)

def create_admin_webapp_button(telegram_id: int, admin_level: str = 'admin') -> str:
    """Создать URL для админской кнопки WebApp"""
    return webapp_integration.create_admin_webapp_url(telegram_id, admin_level)

def create_user_webapp_button(telegram_id: int) -> str:
    """Создать URL для пользовательской кнопки WebApp"""
    return webapp_integration.create_user_webapp_url(telegram_id)


def create_odoo_cabinet_url(telegram_id: int, role: str, cabinet_type: str = 'main') -> str:
    """Создать URL для Odoo кабинета"""
    if role == 'user':
        return webapp_integration.create_user_webapp_url(telegram_id)
    elif role == 'partner':
        return webapp_integration.create_partner_webapp_url(telegram_id)
    elif role in ['admin', 'super_admin']:
        return webapp_integration.create_admin_webapp_url(telegram_id, role)
    else:
        logger.warning(f"Unknown role for cabinet URL: {role}")
        return "#"


def create_odoo_menu_url(telegram_id: int, role: str, menu_id: str) -> str:
    """Создать URL для конкретного меню Odoo"""
    base_url = os.getenv('ODOO_BASE_URL', 'https://odoo-crm-production.up.railway.app')
    sso_token = webapp_integration._create_signature({
        'tg_user_id': telegram_id,
        'tg_role': role,
        'tg_timestamp': int(time.time())
    })
    
    return f"{base_url}/web#menu_id={menu_id}&sso={sso_token}"


def create_odoo_record_url(telegram_id: int, role: str, model: str, record_id: int, view_type: str = 'form') -> str:
    """Создать URL для конкретной записи Odoo"""
    base_url = os.getenv('ODOO_BASE_URL', 'https://odoo-crm-production.up.railway.app')
    sso_token = webapp_integration._create_signature({
        'tg_user_id': telegram_id,
        'tg_role': role,
        'tg_timestamp': int(time.time())
    })
    
    return f"{base_url}/web#id={record_id}&model={model}&view_type={view_type}&sso={sso_token}"
