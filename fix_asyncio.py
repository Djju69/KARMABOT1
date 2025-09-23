import subprocess
import sys

def run_cmd(cmd):
    print(f"Выполняю: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Результат: {result.stdout}")
    if result.stderr:
        print(f"Ошибка: {result.stderr}")
    return result.returncode == 0

# Коммит исправлений
commands = [
    "git add core/database/postgresql_service.py",
    "git commit -m \"Исправление ошибки asyncio.run в PostgreSQL сервисе\"",
    "git push origin main"
]

for cmd in commands:
    if not run_cmd(cmd):
        print(f"ОШИБКА: {cmd}")
        sys.exit(1)

print("✅ Все исправления отправлены!")
