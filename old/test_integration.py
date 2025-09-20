#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

def test_environment():
    """Проверить переменные окружения"""
    print("🔍 Проверка переменных окружения:")
    
    required_vars = [
        'ODOO_BASE_URL', 'ODOO_DB', 'ODOO_USERNAME', 'ODOO_PASSWORD'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display_value = value if var not in ['ODOO_PASSWORD'] else '*' * 8
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: НЕ УСТАНОВЛЕН")

def test_odoo_connection():
    """Тест подключения к Odoo"""
    print("\n🔗 Тест подключения к Odoo:")
    
    try:
        from core.services.odoo_api import OdooAPI
        odoo = OdooAPI()
        
        if odoo.connect():
            print("✅ Подключение к Odoo успешно!")
            return True
        else:
            print("❌ Не удалось подключиться к Odoo")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование интеграции KARMABOT1 + Odoo\n")
    
    test_environment()
    success = test_odoo_connection()
    
    print(f"\n{'✅ ВСЕ ТЕСТЫ ПРОШЛИ' if success else '❌ ЕСТЬ ПРОБЛЕМЫ'}")
