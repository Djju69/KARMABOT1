import subprocess
import sys

def run_cmd(cmd):
    print(f"Выполняю: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Результат: {result.stdout}")
    if result.stderr:
        print(f"Ошибка: {result.stderr}")
    return result.returncode == 0

# Коммит исправления ролей
commands = [
    "git add core/handlers/main_menu_router.py",
    "git commit -m \"Исправление определения ролей в main_menu_router - используем новую систему ролей\"",
    "git push origin main"
]

for cmd in commands:
    if not run_cmd(cmd):
        print(f"ОШИБКА: {cmd}")
        sys.exit(1)

print("✅ Исправления ролей отправлены!")
