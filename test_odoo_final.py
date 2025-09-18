#!/usr/bin/env python3
import os
import sys
import xmlrpc.client

sys.path.append('.')

def test_odoo_direct():
    """Прямой тест подключения к Odoo"""
    
    # Параметры из переменных окружения
    url = os.getenv('ODOO_BASE_URL', 'https://odoo-crm-production.up.railway.app')
    db = os.getenv('ODOO_DB', 'karmabot_odoo')  # Теперь правильное значение
    username = os.getenv('ODOO_USERNAME', 'admin')
    password = os.getenv('ODOO_PASSWORD')
    
    print(f"Тест подключения к Odoo:")
    print(f"URL: {url}")
    print(f"DB: {db}")
    print(f"Username: {username}")
    print(f"Password: {'*' * 8 if password else 'НЕ УСТАНОВЛЕН'}")
    print()
    
    try:
        # Подключение к common endpoint
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        
        # Получить версию
        version = common.version()
        print(f"✅ Odoo сервер доступен")
        print(f"Версия: {version.get('server_version', 'Unknown')}")
        
        # Аутентификация
        uid = common.authenticate(db, username, password, {})
        
        if uid:
            print(f"✅ Аутентификация успешна! UID: {uid}")
            
            # Тест запроса
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            
            # Получить информацию о пользователе
            user_info = models.execute_kw(
                db, uid, password,
                'res.users', 'read',
                [uid], {'fields': ['name', 'login', 'email']}
            )
            
            print(f"✅ Пользователь: {user_info[0].get('name')} ({user_info[0].get('login')})")
            
            # Проверить доступные модели
            model_list = models.execute_kw(
                db, uid, password,
                'ir.model', 'search_read',
                [[]],
                {'fields': ['model'], 'limit': 5}
            )
            
            print(f"✅ Доступно моделей: {len(model_list)}")
            print("Примеры моделей:", [m['model'] for m in model_list[:3]])
            
            return True
            
        else:
            print("❌ Ошибка аутентификации")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_odoo_direct()
    print(f"\n{'🎉 ПОДКЛЮЧЕНИЕ К ODOO РАБОТАЕТ!' if success else '💥 ПОДКЛЮЧЕНИЕ НЕ РАБОТАЕТ'}")
