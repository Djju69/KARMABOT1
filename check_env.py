import os

# Проверяем переменные окружения
env_vars = {}
for key, value in os.environ.items():
    if any(x in key for x in ['BOT_', 'REDIS_', 'DATABASE_', 'ODOO_']):
        env_vars[key] = value

print("🔍 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
for key, value in env_vars.items():
    print(f"{key}={value}")

if not env_vars:
    print("❌ Переменные не найдены")