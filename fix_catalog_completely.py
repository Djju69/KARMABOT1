#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ КАТАЛОГА
Заполняет ВСЕ категории и подкатегории тестовыми данными
"""
import os
import sys
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_all_categories():
    """Заполнить ВСЕ категории тестовыми карточками"""
    print("🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ КАТАЛОГА")
    print("=" * 60)
    
    try:
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url.startswith('postgresql://'):
            print("❌ DATABASE_URL не настроен для PostgreSQL")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Сначала унифицируем структуру
        print("🔧 Унификация структуры БД...")
        try:
            cur.execute("ALTER TABLE card_photos ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0")
            cur.execute("ALTER TABLE card_photos ADD COLUMN IF NOT EXISTS file_id TEXT")
            cur.execute("ALTER TABLE cards_v2 ADD COLUMN IF NOT EXISTS sub_slug VARCHAR(50)")
            cur.execute("ALTER TABLE partners_v2 ADD COLUMN IF NOT EXISTS karma_points INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Структура унифицирована")
        except Exception as e:
            print(f"⚠️ Структура уже унифицирована: {e}")
        
        # Получить или создать тестового партнера
        print("\n👤 Создание тестового партнера...")
        cur.execute("""
            INSERT INTO partners_v2 (tg_user_id, display_name, username, status, karma_points)
            VALUES (999999999, 'Sample Partner', 'sample_partner', 'active', 1000)
            ON CONFLICT (tg_user_id) DO NOTHING
            RETURNING id
        """)
        
        partner_result = cur.fetchone()
        if partner_result:
            partner_id = partner_result[0]
            print(f"✅ Создан новый тестовый партнер ID: {partner_id}")
        else:
            cur.execute("SELECT id FROM partners_v2 WHERE tg_user_id = 999999999")
            partner_id = cur.fetchone()[0]
            print(f"✅ Используем существующего тестового партнера ID: {partner_id}")
        
        # Получить все категории
        print("\n📂 Получение всех категорий...")
        cur.execute("SELECT id, slug, name FROM categories_v2 ORDER BY priority_level DESC")
        categories = cur.fetchall()
        
        print(f"Найдено категорий: {len(categories)}")
        
        # Подкатегории для каждой категории
        subcategories_map = {
            'restaurants': ['asia', 'italian', 'fastfood', 'european', 'russian'],
            'transport': ['cars', 'bikes', 'bicycles', 'scooters', 'motorcycles'],
            'hotels': ['hotels', 'apartments', 'hostels', 'resorts'],
            'shops': ['clothing', 'electronics', 'food', 'books', 'sports'],
            'spa': ['massage', 'beauty', 'wellness', 'salon'],
            'tours': ['excursions', 'travel', 'adventure', 'cultural']
        }
        
        total_cards_added = 0
        total_photos_added = 0
        
        # Заполнить каждую категорию
        for cat_id, slug, name in categories:
            print(f"\n📁 Обработка категории: {slug} ({name})")
            
            # Получить подкатегории для этой категории
            subs = subcategories_map.get(slug, ['general'])
            
            cards_in_category = 0
            
            for sub_slug in subs:
                print(f"   📂 Подкатегория: {sub_slug}")
                
                # Добавить 3-5 карточек в каждую подкатегорию
                cards_to_add = 3
                
                for i in range(cards_to_add):
                    # Создать уникальное название
                    card_title = f"Тест {name} {sub_slug.title()} {i+1}"
                    card_description = f"Описание тестовой карточки {i+1} для {name} - {sub_slug}"
                    
                    # Добавить карточку
                    cur.execute("""
                        INSERT INTO cards_v2 (
                            partner_id, category_id, title, description, 
                            status, sub_slug
                        ) VALUES (%s, %s, %s, %s, 'published', %s)
                        RETURNING id
                    """, (partner_id, cat_id, card_title, card_description, sub_slug))
                    
                    card_result = cur.fetchone()
                    if card_result:
                        card_id = card_result[0]
                        cards_in_category += 1
                        total_cards_added += 1
                        
                        # Добавить 2 фотографии для каждой карточки
                        for photo_num in range(1, 3):
                            cur.execute("""
                                INSERT INTO card_photos (
                                    card_id, photo_url, photo_file_id, 
                                    is_main, position, file_id
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                card_id,
                                f"https://example.com/photo_{card_id}_{photo_num}.jpg",
                                f"photo_{card_id}_{photo_num}",
                                photo_num == 1,
                                photo_num,
                                f"photo_{card_id}_{photo_num}"
                            ))
                            total_photos_added += 1
                        
                        print(f"      ✅ Карточка {i+1}: {card_title}")
            
            print(f"   📊 Добавлено в {slug}: {cards_in_category} карточек")
        
        # Коммит всех изменений
        conn.commit()
        
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("=" * 60)
        print(f"📊 ИТОГО ДОБАВЛЕНО:")
        print(f"   - Карточек: {total_cards_added}")
        print(f"   - Фотографий: {total_photos_added}")
        print(f"   - Категорий обработано: {len(categories)}")
        
        # Финальная проверка
        print("\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА:")
        cur.execute("""
            SELECT 
                c.slug,
                COUNT(cards.id) as total_cards,
                COUNT(CASE WHEN cards.status = 'published' THEN 1 END) as published_cards
            FROM categories_v2 c
            LEFT JOIN cards_v2 cards ON c.id = cards.category_id
            GROUP BY c.id, c.slug
            ORDER BY published_cards DESC;
        """)
        
        final_check = cur.fetchall()
        
        print(f"{'Категория':<15} {'Всего':<8} {'Опубликовано':<12} {'Статус'}")
        print("-" * 50)
        
        all_categories_have_cards = True
        for slug, total, published in final_check:
            status = "✅ РАБОТАЕТ" if published > 0 else "❌ ПУСТАЯ"
            print(f"{slug:<15} {total:<8} {published:<12} {status}")
            
            if published == 0:
                all_categories_have_cards = False
        
        conn.close()
        
        if all_categories_have_cards:
            print("\n🎉 УСПЕХ: Все категории теперь содержат карточки!")
            return True
        else:
            print("\n❌ ОШИБКА: Некоторые категории остались пустыми")
            return False
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    success = populate_all_categories()
    if success:
        print("\n🎯 КАТАЛОГ ПОЛНОСТЬЮ ИСПРАВЛЕН!")
        print("Теперь все категории должны работать в боте")
    else:
        print("\n🚨 ИСПРАВЛЕНИЕ НЕ ЗАВЕРШЕНО!")
        sys.exit(1)
