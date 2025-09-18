import requests
import json

def check_railway_odoo():
    """Проверить доступность Odoo через Railway"""
    
    base_url = "https://odoo-crm-production.up.railway.app"
    
    endpoints_to_check = [
        "/web",
        "/web/database/selector", 
        "/web/login",
        "/web/health"
    ]
    
    print(f"Проверка доступности Odoo: {base_url}")
    print("-" * 50)
    
    for endpoint in endpoints_to_check:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=10)
            status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{endpoint:25} → {status}")
        except Exception as e:
            print(f"{endpoint:25} → ❌ ERROR: {str(e)[:50]}")
    
    print("-" * 50)
    print("Если все endpoints возвращают ошибки - проблема в Railway настройках")

if __name__ == "__main__":
    check_railway_odoo()
