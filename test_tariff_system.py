#!/usr/bin/env python3
"""
Скрипт проверки тарифной системы
"""
import sys
import os
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_tariff_system():
    """Тест работоспособности тарифной системы"""
    print("🔍 Проверка тарифной системы...")
    
    try:
        # Импортируем модели
        from core.models.tariff_models import Tariff, TariffType, TariffFeatures, DEFAULT_TARIFFS
        print("✅ Модели тарифов импортированы")
        
        # Проверяем предустановленные тарифы
        assert len(DEFAULT_TARIFFS) == 3
        print("✅ Предустановленные тарифы загружены")
        
        # Проверяем FREE STARTER
        free_tariff = DEFAULT_TARIFFS[TariffType.FREE_STARTER]
        assert free_tariff.price_vnd == 0
        assert free_tariff.features.max_transactions_per_month == 15
        assert free_tariff.features.commission_rate == 0.12
        print("✅ FREE STARTER тариф корректен")
        
        # Проверяем BUSINESS
        business_tariff = DEFAULT_TARIFFS[TariffType.BUSINESS]
        assert business_tariff.price_vnd == 490000
        assert business_tariff.features.max_transactions_per_month == 100
        assert business_tariff.features.commission_rate == 0.06
        print("✅ BUSINESS тариф корректен")
        
        # Проверяем ENTERPRISE
        enterprise_tariff = DEFAULT_TARIFFS[TariffType.ENTERPRISE]
        assert enterprise_tariff.price_vnd == 960000
        assert enterprise_tariff.features.max_transactions_per_month == -1
        assert enterprise_tariff.features.commission_rate == 0.04
        assert enterprise_tariff.features.api_access is True
        print("✅ ENTERPRISE тариф корректен")
        
        # Импортируем сервис
        from core.services.tariff_service import TariffService
        print("✅ Сервис тарифов импортирован")
        
        # Создаем экземпляр сервиса
        service = TariffService()
        assert service.default_tariffs is not None
        print("✅ Сервис тарифов инициализирован")
        
        # Импортируем админ-роутер
        from core.handlers.tariff_admin_router import router
        print("✅ Админ-роутер тарифов импортирован")
        
        print("\n🎉 Все компоненты тарифной системы работают корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тарифной системе: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_migration_files():
    """Тест файлов миграции"""
    print("\n🔍 Проверка файлов миграции...")
    
    try:
        # Проверяем файл миграции
        migration_file = Path("core/database/migrations/021_partner_tariff_system.py")
        if migration_file.exists():
            print("✅ Файл миграции 021 существует")
        else:
            print("❌ Файл миграции 021 не найден")
            return False
        
        # Проверяем основной файл миграций
        main_migration_file = Path("core/database/migrations.py")
        if main_migration_file.exists():
            print("✅ Основной файл миграций существует")
            
            # Проверяем что миграция добавлена
            with open(main_migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "migrate_021_partner_tariff_system" in content:
                    print("✅ Миграция 021 добавлена в основной файл")
                else:
                    print("❌ Миграция 021 не найдена в основном файле")
                    return False
        else:
            print("❌ Основной файл миграций не найден")
            return False
        
        print("✅ Все файлы миграции корректны")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки файлов миграции: {e}")
        return False

def test_integration():
    """Тест интеграции с основным приложением"""
    print("\n🔍 Проверка интеграции...")
    
    try:
        # Проверяем что роутер добавлен в main_v2.py
        main_file = Path("main_v2.py")
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "tariff_admin_router" in content:
                    print("✅ Тарифный роутер добавлен в main_v2.py")
                else:
                    print("❌ Тарифный роутер не найден в main_v2.py")
                    return False
        else:
            print("❌ Файл main_v2.py не найден")
            return False
        
        # Проверяем что кнопка добавлена в клавиатуру
        keyboard_file = Path("core/keyboards/reply_v2.py")
        if keyboard_file.exists():
            with open(keyboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Управление тарифами" in content:
                    print("✅ Кнопка управления тарифами добавлена в клавиатуру")
                else:
                    print("❌ Кнопка управления тарифами не найдена в клавиатуре")
                    return False
        else:
            print("❌ Файл клавиатуры не найден")
            return False
        
        print("✅ Интеграция корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки интеграции: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск проверки тарифной системы KARMABOT1")
    print("=" * 50)
    
    # Тест компонентов
    components_ok = await test_tariff_system()
    
    # Тест файлов миграции
    migration_ok = test_migration_files()
    
    # Тест интеграции
    integration_ok = test_integration()
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print(f"Компоненты тарифной системы: {'✅ OK' if components_ok else '❌ FAIL'}")
    print(f"Файлы миграции: {'✅ OK' if migration_ok else '❌ FAIL'}")
    print(f"Интеграция: {'✅ OK' if integration_ok else '❌ FAIL'}")
    
    if components_ok and migration_ok and integration_ok:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО!")
        print("💰 Тарифная система готова к деплою!")
        return True
    else:
        print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("🔧 Необходимо исправить ошибки перед деплоем")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
