"""
Скрипт для обновления настроек приложения.
Выполняет следующие действия:
1. Заменяет старый файл настроек на новый
2. Обновляет __init__.py
3. Удаляет временные файлы
"""
import os
import shutil
import sys

def main():
    # Пути к файлам
    base_dir = os.path.dirname(os.path.abspath(__file__))
    core_dir = os.path.join(base_dir, 'core')
    
    # 1. Заменяем старый файл настроек на новый
    old_settings = os.path.join(core_dir, 'settings.py')
    new_settings = os.path.join(core_dir, 'settings_new.py')
    backup_settings = os.path.join(core_dir, 'settings.py.bak')
    
    # Создаем бэкап старого файла настроек
    if os.path.exists(old_settings):
        shutil.copy2(old_settings, backup_settings)
        print(f"Создан бэкап старого файла настроек: {backup_settings}")
    
    # Заменяем файл настроек
    if os.path.exists(new_settings):
        shutil.move(new_settings, old_settings)
        print(f"Файл настроек обновлен: {old_settings}")
    
    # 2. Обновляем __init__.py
    init_file = os.path.join(core_dir, '__init__.py')
    new_init = os.path.join(core_dir, '__init__new__.py')
    backup_init = os.path.join(core_dir, '__init__.py.bak')
    
    # Создаем бэкап старого __init__.py
    if os.path.exists(init_file) and os.path.exists(new_init):
        shutil.copy2(init_file, backup_init)
        print(f"Создан бэкап старого файла __init__.py: {backup_init}")
        
        # Заменяем __init__.py
        shutil.move(new_init, init_file)
        print(f"Файл __init__.py обновлен: {init_file}")
    
    # 3. Удаляем временные файлы
    temp_files = [
        os.path.join(core_dir, 'settings_new.py'),
        os.path.join(core_dir, '__init__new__.py')
    ]
    
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"Удален временный файл: {temp_file}")
            except Exception as e:
                print(f"Не удалось удалить временный файл {temp_file}: {e}")
    
    print("\nОбновление настроек успешно завершено!")
    print("Не забудьте обновить зависимости в requirements.txt, если это необходимо.")
    print("Рекомендуемые зависимости для работы с Telegram:")
    print("python-telegram-bot>=20.0")
    print("python-dotenv>=0.19.0")
    print("aiohttp>=3.8.0")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ошибка при обновлении настроек: {e}", file=sys.stderr)
        sys.exit(1)
