"""
Migration 010: User features tables
- favorites: избранные заведения пользователей
- referrals: реферальная система
- karma_log: история кармы
- points_log: история баллов
- achievements: достижения пользователей
"""

import sqlite3
from pathlib import Path

def upgrade(db_path: str):
    """Add user features tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Избранные заведения
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (card_id) REFERENCES cards_v2(id),
            UNIQUE(user_id, card_id)
        )
    """)
    
    # Реферальная система
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id INTEGER NOT NULL,
            invited_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending', -- pending, completed, expired
            reward_points INTEGER DEFAULT 0,
            FOREIGN KEY (inviter_id) REFERENCES users(id),
            FOREIGN KEY (invited_id) REFERENCES users(id),
            UNIQUE(invited_id)
        )
    """)
    
    # История кармы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS karma_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            points INTEGER NOT NULL,
            action TEXT NOT NULL, -- qr_scan, referral, achievement, etc
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # История баллов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            points INTEGER NOT NULL,
            operation TEXT NOT NULL, -- earn, spend, bonus, etc
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Достижения
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_type TEXT NOT NULL, -- first_qr, foodie, traveler, etc
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            points_reward INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, achievement_type)
        )
    """)
    
    # Индексы для производительности
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorites_card_id ON favorites(card_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals(inviter_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_invited ON referrals(invited_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_karma_log_user_id ON karma_log(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_log_user_id ON points_log(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)")
    
    conn.commit()
    conn.close()
    print("✅ Migration 010: User features tables created")

def downgrade(db_path: str):
    """Remove user features tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS achievements")
    cursor.execute("DROP TABLE IF EXISTS points_log")
    cursor.execute("DROP TABLE IF EXISTS karma_log")
    cursor.execute("DROP TABLE IF EXISTS referrals")
    cursor.execute("DROP TABLE IF EXISTS favorites")
    
    conn.commit()
    conn.close()
    print("✅ Migration 010: User features tables removed")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade("karmabot.db")
    else:
        upgrade("karmabot.db")
