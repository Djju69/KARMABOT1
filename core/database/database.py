import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()

        # Таблица категорий (районы, кухни и т.п.)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_en TEXT,
            name_ko TEXT,
            type TEXT  -- 'district', 'kitchen', etc.
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

        # Таблица пользователей (для хранения языка)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'ru'
        )
        ''')

        conn.commit()

# ---------- ДОБАВЛЕНИЕ ДАННЫХ ----------

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

# ---------- ПОЛУЧЕНИЕ ДАННЫХ ----------

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

# ---------- РАБОТА С ЯЗЫКОМ ПОЛЬЗОВАТЕЛЯ ----------

def set_user_language(user_id, language):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, language) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language=excluded.language
        ''', (user_id, language))
        conn.commit()

def get_user_language(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT language FROM users WHERE user_id=?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'ru'

# ---------- Запуск при первом вызове ----------

if __name__ == "__main__":
    init_db()
    print("База данных и таблицы успешно созданы.")
