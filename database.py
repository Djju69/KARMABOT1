import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT,
                name_en TEXT,
                name_ko TEXT,
                type TEXT
            )
        ''')

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT,
                name_en TEXT,
                name_ko TEXT
            )
        ''')

        conn.commit()

if __name__ == "__main__":
    init_db()
    print("База данных и таблицы успешно созданы.")
