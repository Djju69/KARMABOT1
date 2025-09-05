#!/usr/bin/env python3
"""
Тест импортов для проверки работоспособности бота
"""
import sys
import os

def test_imports():
    """Тестируем критические импорты"""
    print("🔍 Тестируем критические импорты...")
    
    try:
        # Добавляем путь к проекту
        sys.path.append(os.getcwd())
        
        # Тест 1: Конфигурация
        print("1. Тестируем конфигурацию...")
        from core.config import settings
        print("   ✅ core.config.settings - OK")
        
        # Тест 2: База данных
        print("2. Тестируем базу данных...")
        from core.database import get_db
        print("   ✅ core.database.get_db - OK")
        
        # Тест 3: Модели
        print("3. Тестируем модели...")
        from core.models.user import User
        from core.models.user_settings import UserSettings
        print("   ✅ core.models - OK")
        
        # Тест 4: Сервисы
        print("4. Тестируем сервисы...")
        from core.services.profile_service import ProfileService
        from core.services.loyalty_service import LoyaltyService
        from core.services.referral_service import ReferralService
        print("   ✅ core.services - OK")
        
        # Тест 5: Обработчики
        print("5. Тестируем обработчики...")
        from core.handlers.basic import router
        from core.handlers.callback import router as callback_router
        print("   ✅ core.handlers - OK")
        
        # Тест 6: Клавиатуры
        print("6. Тестируем клавиатуры...")
        from core.keyboards.restaurant_keyboards import select_restoran
        from core.keyboards.language_keyboard import language_keyboard
        print("   ✅ core.keyboards - OK")
        
        # Тест 7: Исключения
        print("7. Тестируем исключения...")
        from core.common.exceptions import NotFoundError, ValidationError
        print("   ✅ core.common.exceptions - OK")
        
        print("\n🎉 ВСЕ ИМПОРТЫ РАБОТАЮТ!")
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ИМПОРТА: {e}")
        print(f"❌ Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
