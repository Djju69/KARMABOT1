#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА КАТАЛОГА
Проверяет состояние всех категорий и подкатегорий
"""
import os
import sys
import psycopg2

def diagnose_catalog():
    """Полная диагностика состояния каталога"""
    print("🔍 КРИТИЧЕСКАЯ ДИАГНОСТИКА КАТАЛОГА")
    print("=" * 60)
    
    try:
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url.startswith('postgresql://'):
            print("❌ DATABASE_URL не настроен для PostgreSQL")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # ДИАГНОСТИКА 1: Все категории с количеством карточек
        print("\n📊 ДИАГНОСТИКА 1: Состояние всех категорий")
        print("-" * 50)
        
        cur.execute("""
            SELECT 
                c.slug,
                c.name,
                COUNT(cards.id) as total_cards,
                COUNT(CASE WHEN cards.status = 'published' THEN 1 END) as published_cards
            FROM categories_v2 c
            LEFT JOIN cards_v2 cards ON c.id = cards.category_id
            GROUP BY c.id, c.slug, c.name
            ORDER BY published_cards DESC;
        """)
        
        categories = cur.fetchall()
        
        print(f"{'Категория':<15} {'Всего':<8} {'Опубликовано':<12} {'Статус'}")
        print("-" * 50)
        
        empty_categories = []
        working_categories = []
        
        for slug, name, total, published in categories:
            status = "✅ РАБОТАЕТ" if published > 0 else "❌ ПУСТАЯ"
            print(f"{slug:<15} {total:<8} {published:<12} {status}")
            
            if published == 0:
                empty_categories.append(slug)
            else:
                working_categories.append(slug)
        
        print(f"\n📈 ИТОГО: {len(working_categories)} работающих, {len(empty_categories)} пустых")
        
        # ДИАГНОСТИКА 2: Подкатегории
        print("\n📊 ДИАГНОСТИКА 2: Состояние подкатегорий")
        print("-" * 50)
        
        cur.execute("""
            SELECT 
                c.slug as category_slug,
                cards.sub_slug,
                COUNT(*) as cards_count
            FROM cards_v2 cards
            JOIN categories_v2 c ON cards.category_id = c.id
            WHERE cards.status = 'published'
            GROUP BY c.slug, cards.sub_slug
            ORDER BY c.slug, cards.sub_slug;
        """)
        
        subcategories = cur.fetchall()
        
        if subcategories:
            print(f"{'Категория':<15} {'Подкатегория':<15} {'Карточек'}")
            print("-" * 50)
            for cat_slug, sub_slug, count in subcategories:
                print(f"{cat_slug:<15} {sub_slug:<15} {count}")
        else:
            print("❌ НЕТ ДАННЫХ О ПОДКАТЕГОРИЯХ")
        
        # ДИАГНОСТИКА 3: Проверка партнеров
        print("\n📊 ДИАГНОСТИКА 3: Партнеры")
        print("-" * 50)
        
        cur.execute("SELECT COUNT(*) FROM partners_v2")
        partners_count = cur.fetchone()[0]
        print(f"Всего партнеров: {partners_count}")
        
        cur.execute("SELECT COUNT(*) FROM partners_v2 WHERE display_name LIKE '%Sample%'")
        sample_partners = cur.fetchone()[0]
        print(f"Тестовых партнеров: {sample_partners}")
        
        # ДИАГНОСТИКА 4: Проверка фотографий
        print("\n📊 ДИАГНОСТИКА 4: Фотографии")
        print("-" * 50)
        
        cur.execute("SELECT COUNT(*) FROM card_photos")
        photos_count = cur.fetchone()[0]
        print(f"Всего фотографий: {photos_count}")
        
        cur.execute("""
            SELECT COUNT(DISTINCT card_id) 
            FROM card_photos cp
            JOIN cards_v2 c ON cp.card_id = c.id
            WHERE c.status = 'published'
        """)
        cards_with_photos = cur.fetchone()[0]
        print(f"Карточек с фото: {cards_with_photos}")
        
        conn.close()
        
        # ВЫВОДЫ
        print("\n🎯 ВЫВОДЫ ДИАГНОСТИКИ:")
        print("=" * 60)
        
        if len(empty_categories) > 0:
            print(f"❌ ПРОБЛЕМА: {len(empty_categories)} категорий пустые:")
            for cat in empty_categories:
                print(f"   - {cat}")
            print("\n🔧 РЕШЕНИЕ: Добавить тестовые карточки во все пустые категории")
        else:
            print("✅ Все категории содержат карточки")
        
        if len(working_categories) > 0:
            print(f"✅ РАБОТАЕТ: {len(working_categories)} категорий:")
            for cat in working_categories:
                print(f"   - {cat}")
        
        return len(empty_categories) == 0
        
    except Exception as e:
        print(f"❌ ОШИБКА ДИАГНОСТИКИ: {e}")
        return False

if __name__ == "__main__":
    success = diagnose_catalog()
    if success:
        print("\n🎉 ДИАГНОСТИКА ЗАВЕРШЕНА: Каталог в порядке")
    else:
        print("\n🚨 ДИАГНОСТИКА ЗАВЕРШЕНА: Требуется исправление")
