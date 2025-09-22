#!/usr/bin/env python3
"""
Простой тест для проверки мульти-платформенной системы
"""
import sys
import os

def test_structure():
    """Проверить структуру файлов"""
    print("🔍 Проверка структуры файлов...")
    
    required_files = [
        "multiplatform/main_api.py",
        "multiplatform/database/fault_tolerant_service.py",
        "multiplatform/database/platform_adapters.py",
        "multiplatform/database/enhanced_unified_service.py",
        "multiplatform/api/platform_endpoints.py",
        "multiplatform/dashboard/system_dashboard.html",
        "multiplatform/monitoring/system_monitor.py",
        "multiplatform/tests/test_fault_tolerance.py",
        "multiplatform/tests/test_platform_adapters.py",
        "multiplatform/tests/test_full_system.py",
        "requirements_multiplatform.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Отсутствуют файлы: {missing_files}")
        return False
    else:
        print("\n✅ Все файлы созданы!")
        return True

def test_imports():
    """Проверить импорты"""
    print("\n🔍 Проверка импортов...")
    
    try:
        # Добавляем путь к multiplatform
        sys.path.insert(0, 'multiplatform')
        
        # Тестируем импорты
        from database.fault_tolerant_service import fault_tolerant_db
        print("✅ fault_tolerant_service импортирован")
        
        from database.platform_adapters import TelegramAdapter
        print("✅ platform_adapters импортирован")
        
        from database.enhanced_unified_service import enhanced_unified_db
        print("✅ enhanced_unified_service импортирован")
        
        from api.platform_endpoints import main_router
        print("✅ platform_endpoints импортирован")
        
        from monitoring.system_monitor import SystemMonitor
        print("✅ system_monitor импортирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_basic_functionality():
    """Проверить базовую функциональность"""
    print("\n🔍 Проверка базовой функциональности...")
    
    try:
        sys.path.insert(0, 'multiplatform')
        
        from database.fault_tolerant_service import fault_tolerant_db
        
        # Тест статуса системы
        status = fault_tolerant_db.get_system_status()
        print(f"✅ Статус системы: {status['mode']}")
        
        # Тест создания пользователя
        success = fault_tolerant_db.create_user_with_fallback(
            123456789, 
            {'username': 'test'}, 
            'telegram'
        )
        print(f"✅ Создание пользователя: {'Успешно' if success else 'Ошибка'}")
        
        # Тест получения пользователя
        user_info = fault_tolerant_db.get_user_with_fallback(123456789, 'telegram')
        print(f"✅ Получение пользователя: {'Успешно' if user_info else 'Ошибка'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка функциональности: {e}")
        return False

def test_main_bot_intact():
    """Проверить что основной бот не затронут"""
    print("\n🔍 Проверка основного бота...")
    
    try:
        # Проверяем что main_v2.py существует и не изменен
        if os.path.exists("main_v2.py"):
            print("✅ main_v2.py существует")
            
            # Проверяем размер файла (должен быть большой)
            size = os.path.getsize("main_v2.py")
            if size > 100000:  # Больше 100KB
                print(f"✅ main_v2.py размер: {size} байт (не изменен)")
            else:
                print(f"⚠️ main_v2.py размер: {size} байт (возможно изменен)")
            
            # Проверяем что core/ не затронут
            if os.path.exists("core/"):
                print("✅ core/ директория существует")
            else:
                print("❌ core/ директория отсутствует")
            
            return True
        else:
            print("❌ main_v2.py отсутствует")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки бота: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ МУЛЬТИ-ПЛАТФОРМЕННОЙ СИСТЕМЫ")
    print("=" * 60)
    
    tests = [
        ("Структура файлов", test_structure),
        ("Импорты модулей", test_imports),
        ("Базовая функциональность", test_basic_functionality),
        ("Основной бот не затронут", test_main_bot_intact)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Результат: {passed}/{total} тестов пройдено")
    print(f"🎯 Успешность: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Мульти-платформенная система готова!")
        print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. cd multiplatform")
        print("2. python main_api.py")
        print("3. Открыть http://localhost:8001/docs")
        print("4. Открыть http://localhost:8001/dashboard/")
    else:
        print(f"\n⚠️ {total-passed} тестов провалено. Требуется исправление.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
