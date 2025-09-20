from sqlite3 import connect
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "database.db"

def connect_db():
    return connect(DB_PATH)

def get_categories(category_type: str, lang: str = "ru") -> list:
    with connect_db() as conn:
        cursor = conn.cursor()
        # Безопасный параметризованный запрос с валидацией языка
        valid_langs = ['ru', 'en', 'ko', 'vi']
        safe_lang = lang if lang in valid_langs else 'ru'
        # Полностью безопасный запрос без f-строк
        if safe_lang == 'ru':
            cursor.execute("SELECT id, name_ru FROM categories WHERE type = ?", (category_type,))
        elif safe_lang == 'en':
            cursor.execute("SELECT id, name_en FROM categories WHERE type = ?", (category_type,))
        elif safe_lang == 'ko':
            cursor.execute("SELECT id, name_ko FROM categories WHERE type = ?", (category_type,))
        elif safe_lang == 'vi':
            cursor.execute("SELECT id, name_vi FROM categories WHERE type = ?", (category_type,))
        else:
            cursor.execute("SELECT id, name_ru FROM categories WHERE type = ?", (category_type,))
        return cursor.fetchall()
