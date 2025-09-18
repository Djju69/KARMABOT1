import sqlite3
from pathlib import Path

class Database:
    def __init__(self):
        db_path = Path(__file__).parent / "data.db"
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Чтобы можно было получать данные как словари
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                emoji TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category_id INTEGER,
                address TEXT,
                discount TEXT,
                link TEXT,
                qr_code TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        self.conn.commit()

    def add_category(self, name_with_emoji: str):
        emoji = name_with_emoji.strip().split(' ')[0]
        name = name_with_emoji.strip()[len(emoji):].strip()
        self.cursor.execute("SELECT id FROM categories WHERE name = ? AND emoji = ?", (name, emoji))
        if self.cursor.fetchone():
            return
        self.cursor.execute("INSERT INTO categories (name, emoji) VALUES (?, ?)", (name, emoji))
        self.conn.commit()

    def add_place(self, name, category, address, discount, link, qr_code):
        emoji = category.strip().split(' ')[0]
        name_cat = category.strip()[len(emoji):].strip()
        self.cursor.execute("SELECT id FROM categories WHERE name = ? AND emoji = ?", (name_cat, emoji))
        result = self.cursor.fetchone()
        if not result:
            raise ValueError(f"Category '{category}' not found in DB.")
        category_id = result[0]
        self.cursor.execute("""
            INSERT INTO places (name, category_id, address, discount, link, qr_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category_id, address, discount, link, qr_code))
        self.conn.commit()

    def get_categories(self):
        self.cursor.execute("SELECT id, name, emoji FROM categories")
        return [(row['id'], row['name'], row['emoji']) for row in self.cursor.fetchall()]

    def get_places_by_category(self, category_text):
        emoji = category_text.strip().split(' ')[0]
        name = category_text.strip()[len(emoji):].strip()
        self.cursor.execute("""
            SELECT p.name FROM places p
            JOIN categories c ON c.id = p.category_id
            WHERE c.name = ? AND c.emoji = ?
        """, (name, emoji))
        return [row['name'] for row in self.cursor.fetchall()]

    def get_places_by_category_id(self, category_id: int):
        self.cursor.execute("""
            SELECT name, address, discount, link, qr_code
            FROM places
            WHERE category_id = ?
        """, (category_id,))
        return self.cursor.fetchall()


db = Database()
