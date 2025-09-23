import subprocess
import sys

def run_cmd(cmd):
    print(f"Выполняю: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Результат: {result.stdout}")
    if result.stderr:
        print(f"Ошибка: {result.stderr}")
    return result.returncode == 0

# Коммит исправления отображения карточек
commands = [
    "git add core/handlers/category_handlers_v2.py",
    "git commit -m \"Исправление отображения карточек - показывать по 5 карточек на страницу с индивидуальными кнопками\"",
    "git push origin main"
]

for cmd in commands:
    if not run_cmd(cmd):
        print(f"ОШИБКА: {cmd}")
        sys.exit(1)

print("✅ Исправления карточек отправлены!")
