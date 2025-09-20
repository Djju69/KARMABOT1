#!/usr/bin/env python3
"""
Odoo Connector для интеграции Telegram бота с Odoo
"""

import xmlrpc.client
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class OdooConnector:
    """Класс для подключения к Odoo через XML-RPC API"""
    
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB', 'railway')
        self.username = os.getenv('ODOO_USERNAME', 'admin')
        self.password = os.getenv('ODOO_PASSWORD')
        self.uid = None
        
        # Инициализация XML-RPC клиентов
        if self.url and self.password:
            try:
                self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                logger.info(f"✅ Odoo connector initialized for {self.url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Odoo connector: {e}")
                self.common = None
                self.models = None
        else:
            logger.warning("⚠️ Odoo URL or password not set")
            self.common = None
            self.models = None
    
    def authenticate(self) -> bool:
        """Аутентификация в Odoo"""
        if not all([self.url, self.db, self.username, self.password]):
            logger.error("❌ Missing Odoo credentials")
            return False
            
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                logger.info(f"✅ Authenticated to Odoo as {self.username} (UID: {self.uid})")
                return True
            else:
                logger.error("❌ Authentication failed")
                return False
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Простой тест подключения"""
        if not self.authenticate():
            return False
            
        try:
            # Получаем список модулей karmabot
            modules = self.models.execute_kw(
                self.db, self.uid, self.password,
                'ir.module.module', 'search_read',
                [[('name', 'like', 'karmabot')]],
                {'fields': ['name', 'state']}
            )
            logger.info(f"✅ Found {len(modules)} karmabot modules")
            for mod in modules:
                logger.info(f"  - {mod['name']}: {mod['state']}")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def create_user(self, telegram_id: int, username: str, name: str) -> Optional[int]:
        """Создание пользователя в Odoo"""
        if not self.authenticate():
            return None
            
        try:
            # Создаем партнера
            partner_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'create',
                [{
                    'name': name,
                    'is_company': False,
                    'comment': f'Telegram user: @{username} (ID: {telegram_id})'
                }]
            )
            
            # Создаем пользователя системы
            user_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.users', 'create',
                [{
                    'name': name,
                    'login': f'telegram_{telegram_id}',
                    'partner_id': partner_id,
                    'groups_id': [(6, 0, [self._get_portal_group_id()])]
                }]
            )
            
            logger.info(f"✅ Created user {name} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            return None
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по Telegram ID"""
        if not self.authenticate():
            return None
            
        try:
            users = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.users', 'search_read',
                [[('login', '=', f'telegram_{telegram_id}')]],
                {'fields': ['id', 'name', 'login', 'partner_id']}
            )
            
            if users:
                return users[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get user: {e}")
            return None
    
    def _get_portal_group_id(self) -> int:
        """Получение ID группы Portal"""
        try:
            groups = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.groups', 'search',
                [[('name', '=', 'Portal')]]
            )
            return groups[0] if groups else 1
        except:
            return 1  # Fallback to admin group

# Глобальный экземпляр коннектора
odoo_connector = OdooConnector()

# Функции для использования в боте
async def test_odoo_connection() -> bool:
    """Тестирование подключения к Odoo"""
    return odoo_connector.test_connection()

async def create_telegram_user(telegram_id: int, username: str, name: str) -> Optional[int]:
    """Создание пользователя Telegram в Odoo"""
    return odoo_connector.create_user(telegram_id, username, name)

async def get_telegram_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получение пользователя Telegram из Odoo"""
    return odoo_connector.get_user_by_telegram_id(telegram_id)
