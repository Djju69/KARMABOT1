#!/usr/bin/env python3
"""
Скрипт для полного тестирования унифицированной базы данных
"""
import sys
import os
import asyncio
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_postgresql_structure():
    """ТЕСТ 1: Проверить что структура PostgreSQL соответствует ТЗ"""
    print("\n🧪 ТЕСТ 1: Проверка структуры PostgreSQL БД")
    print("-" * 50)
    
    try:
        from core.database.postgresql_service import PostgreSQLService
        
        db = PostgreSQLService()
        await db.initialize()
        
        # Проверить структуру card_photos
        query = """
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'card_photos'
            ORDER BY ordinal_position;
        """
        
        columns = await db.fetch_all(query)
        
        required_columns = {
            'position': 'integer',
            'is_main': 'boolean', 
            'photo_url': 'text',
            'photo_file_id': 'text',
            'file_id': 'text'  # добавлено для совместимости
        }
        
        print("📋 Найденные колонки в card_photos:")
        for col in columns:
            print(f"   - {col['column_name']}: {col['data_type']}")
        
        for col_name, col_type in required_columns.items():
            found = any(col['column_name'] == col_name for col in columns)
            if found:
                print(f"✅ Колонка {col_name} найдена")
            else:
                print(f"❌ Колонка {col_name} ОТСУТСТВУЕТ")
                raise AssertionError(f"Колонка {col_name} отсутствует в card_photos")
        
        print("✅ ТЕСТ 1 ПРОШЕЛ: Структура PostgreSQL корректна")
        return True
        
    except Exception as e:
        print(f"❌ ТЕСТ 1 ПРОВАЛЕН: {e}")
        return False

async def test_sample_data_insertion():
    """ТЕСТ 2: Проверить что тестовые карточки добавляются без ошибок"""
    print("\n🧪 ТЕСТ 2: Проверка добавления тестовых данных")
    print("-" * 50)
    
    try:
        from core.database.postgresql_service import PostgreSQLService
        from core.database.migrations import add_sample_cards
        
        db = PostgreSQLService()
        await db.initialize()
        
        # Подсчитать карточки ДО добавления
        cards_query = "SELECT COUNT(*) FROM cards_v2"
        cards_before = await db.fetch_one(cards_query)
        cards_before = cards_before[0] if cards_before else 0
        
        photos_query = "SELECT COUNT(*) FROM card_photos"
        photos_before = await db.fetch_one(photos_query)
        photos_before = photos_before[0] if photos_before else 0
        
        print(f"📊 ДО добавления: {cards_before} карточек, {photos_before} фото")
        
        # Попытаться добавить тестовые карточки
        try:
            add_sample_cards()
            print("✅ Функция add_sample_cards() выполнилась без ошибок")
        except Exception as e:
            print(f"❌ ОШИБКА при добавлении: {e}")
            raise
        
        # Подсчитать карточки ПОСЛЕ добавления  
        cards_after = await db.fetch_one(cards_query)
        cards_after = cards_after[0] if cards_after else 0
        
        photos_after = await db.fetch_one(photos_query)
        photos_after = photos_after[0] if photos_after else 0
        
        print(f"📊 ПОСЛЕ добавления: {cards_after} карточек, {photos_after} фото")
        
        if cards_after <= cards_before:
            raise AssertionError(f"Карточки не добавились: было {cards_before}, стало {cards_after}")
        
        if photos_after <= photos_before:
            raise AssertionError(f"Фото не добавились: было {photos_before}, стало {photos_after}")
        
        print(f"✅ ТЕСТ 2 ПРОШЕЛ: Добавлено {cards_after - cards_before} карточек, {photos_after - photos_before} фото")
        return True
        
    except Exception as e:
        print(f"❌ ТЕСТ 2 ПРОВАЛЕН: {e}")
        return False

async def test_catalog_functionality():
    """ТЕСТ 3: Проверить что каталог возвращает карточки"""
    print("\n🧪 ТЕСТ 3: Проверка работы каталога")
    print("-" * 50)
    
    try:
        from core.database.postgresql_service import PostgreSQLService
        
        db = PostgreSQLService()
        await db.initialize()
        
        # Получить все категории
        categories_query = "SELECT id, slug FROM categories_v2"
        categories = await db.fetch_all(categories_query)
        
        total_cards = 0
        categories_with_cards = 0
        
        for cat in categories:
            cat_id = cat['id']
            slug = cat['slug']
            
            # Проверить количество карточек в каждой категории
            cards_query = "SELECT COUNT(*) FROM cards_v2 WHERE category_id = %s AND status = 'published'"
            card_count = await db.fetch_one(cards_query, (cat_id,))
            card_count = card_count[0] if card_count else 0
            
            if card_count > 0:
                print(f"✅ Категория {slug}: {card_count} карточек")
                categories_with_cards += 1
                total_cards += card_count
                
                # Проверить что у карточек есть фотографии
                photos_query = """
                    SELECT COUNT(*) FROM card_photos cp
                    JOIN cards_v2 c ON cp.card_id = c.id  
                    WHERE c.category_id = %s
                """
                photo_count = await db.fetch_one(photos_query, (cat_id,))
                photo_count = photo_count[0] if photo_count else 0
                print(f"   📸 Фотографий: {photo_count}")
            else:
                print(f"❌ Категория {slug}: БЕЗ КАРТОЧЕК")
        
        print(f"\n📊 ИТОГО: {total_cards} карточек в {categories_with_cards} категориях")
        
        if total_cards == 0:
            raise AssertionError("В каталоге нет ни одной карточки!")
        
        print("✅ ТЕСТ 3 ЗАВЕРШЕН: Проверка каталога")
        return True
        
    except Exception as e:
        print(f"❌ ТЕСТ 3 ПРОВАЛЕН: {e}")
        return False

async def test_database_adapter():
    """ТЕСТ 4: Проверить что адаптер корректно работает с унифицированной структурой"""
    print("\n🧪 ТЕСТ 4: Проверка адаптера БД")
    print("-" * 50)
    
    try:
        from core.database.postgresql_service import PostgreSQLService
        from core.database.db_adapter import DatabaseAdapter
        
        db = PostgreSQLService()
        await db.initialize()
        
        # Создать тестовую карточку
        test_card_query = """
            INSERT INTO cards_v2 (partner_id, category_id, title, status) 
            VALUES (1, 1, 'Test Card', 'published') RETURNING id
        """
        test_card_result = await db.fetch_one(test_card_query)
        test_card_id = test_card_result[0] if test_card_result else None
        
        if not test_card_id:
            raise AssertionError("Не удалось создать тестовую карточку")
        
        print(f"📝 Создана тестовая карточка ID: {test_card_id}")
        
        # Добавить фото через унифицированную структуру
        test_photo_query = """
            INSERT INTO card_photos (card_id, photo_url, photo_file_id, position, is_main, file_id)
            VALUES (%s, 'test_url', 'test_file_id', 1, true, 'test_file_id')
        """
        await db.execute(test_photo_query, (test_card_id,))
        print("📸 Добавлено тестовое фото")
        
        # Проверить через адаптер
        adapter = DatabaseAdapter()
        photos = adapter.get_card_photos(test_card_id)
        
        if len(photos) == 0:
            raise AssertionError("Адаптер не вернул фотографии")
        
        print(f"✅ Адаптер вернул {len(photos)} фотографий")
        
        # Проверить структуру возвращаемых данных
        photo = photos[0]
        required_fields = ['card_id', 'photo_url', 'photo_file_id', 'position', 'is_main']
        
        for field in required_fields:
            if field not in photo:
                raise AssertionError(f"Поле {field} отсутствует в данных адаптера")
        
        print("✅ Структура данных адаптера корректна")
        
        # Очистить тестовые данные
        await db.execute("DELETE FROM card_photos WHERE card_id = %s", (test_card_id,))
        await db.execute("DELETE FROM cards_v2 WHERE id = %s", (test_card_id,))
        print("🧹 Тестовые данные очищены")
        
        print("✅ ТЕСТ 4 ПРОШЕЛ: Адаптер БД работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ ТЕСТ 4 ПРОВАЛЕН: {e}")
        return False

async def run_all_tests():
    """Запустить все тесты"""
    print("🧪 НАЧИНАЕМ ПОЛНОЕ ТЕСТИРОВАНИЕ УНИФИЦИРОВАННОЙ БД")
    print("=" * 60)
    
    # Сначала запустить унификацию
    print("🔧 Запуск унификации структуры...")
    try:
        from core.database.migrations import unify_database_structure
        unify_database_structure()
        print("✅ Унификация структуры завершена")
    except Exception as e:
        print(f"⚠️ Унификация уже выполнена или ошибка: {e}")
    
    # Запуск всех тестов
    tests = [
        test_postgresql_structure,
        test_sample_data_insertion, 
        test_catalog_functionality,
        test_database_adapter
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ Тест {test_func.__name__} завершился с ошибкой: {e}")
    
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ База данных унифицирована и работает корректно")
        print(f"📊 Результат: {passed_tests}/{total_tests} тестов пройдено")
        return True
    else:
        print(f"❌ ТЕСТЫ ПРОВАЛИЛИСЬ: {passed_tests}/{total_tests} пройдено")
        print("🚨 СИСТЕМА НЕ ГОТОВА К ИСПОЛЬЗОВАНИЮ")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)
