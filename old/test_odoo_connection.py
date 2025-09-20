import sys
sys.path.append('.')

from core.services.odoo_api import OdooAPI

def test_odoo():
    print("Тестирование подключения к Odoo...")
    
    odoo = OdooAPI()
    result = odoo.test_connection()
    
    print("\nРезультат теста:")
    if result['success']:
        print("✅ Подключение к Odoo успешно!")
        print(f"UID: {result['uid']}")
        print(f"Установленные модули: {result['installed_modules']}")
    else:
        print("❌ Ошибка подключения к Odoo:")
        print(f"Ошибка: {result['error']}")
    
    return result['success']

if __name__ == "__main__":
    test_odoo()
