import sqlite3 
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()

        # Таблица категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_en TEXT,
            name_ko TEXT,
            type TEXT
        )
        ''')

        # Таблица ресторанов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            latitude REAL,
            longitude REAL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        ''')

        # Таблица дополнительных услуг
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_en TEXT,
            name_ko TEXT
        )
        ''')

        conn.commit()

def add_category(name_ru, name_en, name_ko, type_):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO categories (name_ru, name_en, name_ko, type)
            VALUES (?, ?, ?, ?)
        ''', (name_ru, name_en, name_ko, type_))
        conn.commit()

def add_restaurant(name, description, lat, lon, category_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO restaurants (name, description, latitude, longitude, category_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, lat, lon, category_id))
        conn.commit()

def get_categories(type_, lang='ru'):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT id, name_{lang} FROM categories WHERE type=?
        ''', (type_,))
        return cursor.fetchall()

def get_restaurants_by_category(category_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, latitude, longitude
            FROM restaurants WHERE category_id=?
        ''', (category_id,))
        return cursor.fetchall()

# Запускай вручную, чтобы создать базу
if __name__ == "__main__":
    init_db()
    print("База данных и таблицы успешно созданы.")
