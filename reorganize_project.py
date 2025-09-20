#!/usr/bin/env python3
"""
Скрипт для реорганизации проекта и перемещения старых файлов в папку old/
"""

import os
import shutil
import sys
from pathlib import Path

def reorganize_project():
    """Реорганизовать проект и переместить старые файлы"""
    
    # Получаем корневую директорию проекта
    project_root = Path.cwd()
    old_dir = project_root / "old"
    
    print("🔧 Реорганизация проекта...")
    print(f"Корневая директория: {project_root}")
    
    # Создаем папку old/ если её нет
    old_dir.mkdir(exist_ok=True)
    print(f"✅ Создана папка: {old_dir}")
    
    # Список файлов которые нужно сохранить (новые)
    keep_files = {
        # Новые файлы из задачи 3
        "api/platform_endpoints.py",
        "dashboard/system_dashboard.html",
        "monitoring/system_monitor.py", 
        "tests/test_full_system.py",
        "main.py",
        "requirements.txt",
        ".env.example",
        "railway.toml",
        "README.md",
        "Dockerfile",
        
        # Сохраняем основной database service из задачи 2
        "core/database/enhanced_unified_service.py",
        
        # Git и другие системные файлы
        ".git",
        ".gitignore",
        ".env",
        
        # Этот скрипт
        "reorganize_project.py"
    }
    
    # Создаем необходимые директории
    directories_to_create = [
        "api",
        "dashboard", 
        "monitoring",
        "tests",
        "core",
        "core/database"
    ]
    
    for dir_name in directories_to_create:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана директория: {dir_path}")
    
    # Функция для проверки, нужно ли сохранить файл/папку
    def should_keep(path_str):
        for keep_pattern in keep_files:
            if path_str == keep_pattern or path_str.startswith(keep_pattern + "/"):
                return True
        return False
    
    # Перемещаем старые файлы
    moved_count = 0
    
    for item in project_root.iterdir():
        if item.name == "old":
            continue
            
        relative_path = item.relative_to(project_root)
        
        if not should_keep(str(relative_path)):
            try:
                destination = old_dir / item.name
                
                if item.is_file():
                    shutil.move(str(item), str(destination))
                    print(f"📦 Перемещен файл: {item.name} -> old/")
                    moved_count += 1
                elif item.is_dir():
                    # Проверяем, есть ли в директории файлы которые нужно сохранить
                    has_keep_files = False
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = Path(root) / file
                            rel_path = file_path.relative_to(project_root)
                            if should_keep(str(rel_path)):
                                has_keep_files = True
                                break
                        if has_keep_files:
                            break
                    
                    if not has_keep_files:
                        shutil.move(str(item), str(destination))
                        print(f"📁 Перемещена папка: {item.name} -> old/")
                        moved_count += 1
                        
            except Exception as e:
                print(f"❌ Ошибка при перемещении {item.name}: {e}")
    
    print(f"\n✅ Перемещено {moved_count} старых элементов в папку old/")
    
    # Проверяем структуру проекта
    print("\n📋 Текущая структура проекта:")
    
    expected_files = [
        "main.py",
        "requirements.txt", 
        "README.md",
        "api/platform_endpoints.py",
        "dashboard/system_dashboard.html",
        "monitoring/system_monitor.py",
        "tests/test_full_system.py",
        "core/database/enhanced_unified_service.py"
    ]
    
    missing_files = []
    
    for file_path in expected_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - ОТСУТСТВУЕТ")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ Отсутствуют {len(missing_files)} файлов:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nНужно создать недостающие файлы из задачи 3.")
    else:
        print(f"\n🎉 Все файлы на месте! Проект готов к работе.")
    
    # Создаем файл .gitignore если его нет
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db

# Old files
old/
"""
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"✅ Создан .gitignore")
    
    print(f"\n🚀 Реорганизация завершена!")
    print(f"📁 Старые файлы находятся в: {old_dir}")
    print(f"🔧 Можно запускать: python main.py")

if __name__ == "__main__":
    try:
        reorganize_project()
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
