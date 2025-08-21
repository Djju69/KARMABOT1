from sqlite3 import connect
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "database.db"

def connect_db():
    return connect(DB_PATH)

def get_categories(category_type: str, lang: str = "ru") -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, name_{lang} FROM categories WHERE type = ?", (category_type,))
        return cursor.fetchall()
