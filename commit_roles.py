#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Command: {cmd}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

# Коммит изменений ролей
commands = [
    "git add core/security/roles.py core/settings.py",
    "git commit -m \"Исправление ролей пользователей - добавлен супер-админ и партнер\"",
    "git push origin main"
]

for cmd in commands:
    if not run_command(cmd):
        print(f"Failed: {cmd}")
        sys.exit(1)

print("✅ Все команды выполнены успешно!")
