-- Миграция для многоуровневой реферальной системы
-- Дата: 2025-12-19
-- Описание: Создание таблиц для 3-уровневой реферальной системы

-- Создание таблицы дерева рефералов
CREATE TABLE IF NOT EXISTS referral_tree (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    referrer_id BIGINT NULL,
    level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_earnings DECIMAL(10, 2) DEFAULT 0,
    total_referrals INTEGER DEFAULT 0,
    active_referrals INTEGER DEFAULT 0,
    
    FOREIGN KEY (referrer_id) REFERENCES referral_tree(id) ON DELETE SET NULL
);

-- Создание таблицы бонусов рефералов
CREATE TABLE IF NOT EXISTS referral_bonuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    level INTEGER NOT NULL,
    bonus_amount DECIMAL(10, 2) NOT NULL,
    source_transaction_id INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_transaction_id) REFERENCES loyalty_transactions(id) ON DELETE SET NULL
);

-- Создание таблицы статистики рефералов
CREATE TABLE IF NOT EXISTS referral_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    
    -- Статистика по уровням
    level_1_count INTEGER DEFAULT 0,
    level_2_count INTEGER DEFAULT 0,
    level_3_count INTEGER DEFAULT 0,
    
    -- Доходы по уровням
    level_1_earnings DECIMAL(10, 2) DEFAULT 0,
    level_2_earnings DECIMAL(10, 2) DEFAULT 0,
    level_3_earnings DECIMAL(10, 2) DEFAULT 0,
    
    -- Общая статистика
    total_referrals INTEGER DEFAULT 0,
    total_earnings DECIMAL(10, 2) DEFAULT 0,
    
    -- Временные метки
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_referral_tree_user_id ON referral_tree(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_tree_referrer_id ON referral_tree(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_tree_user_referrer ON referral_tree(user_id, referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_tree_referrer_level ON referral_tree(referrer_id, level);
CREATE INDEX IF NOT EXISTS idx_referral_tree_created_at ON referral_tree(created_at);

CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer_id ON referral_bonuses(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referred_id ON referral_bonuses(referred_id);
CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer_level ON referral_bonuses(referrer_id, level);
CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referred_level ON referral_bonuses(referred_id, level);
CREATE INDEX IF NOT EXISTS idx_referral_bonuses_created_at ON referral_bonuses(created_at);

CREATE INDEX IF NOT EXISTS idx_referral_stats_user_id ON referral_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_stats_last_updated ON referral_stats(last_updated);

-- Триггер для автоматического обновления статистики при добавлении реферала
CREATE TRIGGER IF NOT EXISTS update_referral_stats_on_insert
AFTER INSERT ON referral_tree
BEGIN
    -- Обновляем статистику для реферера
    INSERT OR REPLACE INTO referral_stats (
        user_id,
        level_1_count,
        level_2_count,
        level_3_count,
        total_referrals,
        last_updated
    )
    SELECT 
        NEW.referrer_id,
        COUNT(CASE WHEN level = 1 THEN 1 END),
        COUNT(CASE WHEN level = 2 THEN 1 END),
        COUNT(CASE WHEN level = 3 THEN 1 END),
        COUNT(*),
        CURRENT_TIMESTAMP
    FROM referral_tree 
    WHERE referrer_id = NEW.referrer_id
    ON CONFLICT(user_id) DO UPDATE SET
        level_1_count = excluded.level_1_count,
        level_2_count = excluded.level_2_count,
        level_3_count = excluded.level_3_count,
        total_referrals = excluded.total_referrals,
        last_updated = CURRENT_TIMESTAMP;
END;

-- Триггер для обновления статистики при начислении бонусов
CREATE TRIGGER IF NOT EXISTS update_referral_earnings_on_bonus
AFTER INSERT ON referral_bonuses
BEGIN
    -- Обновляем доходы в статистике
    UPDATE referral_stats SET
        level_1_earnings = (
            SELECT COALESCE(SUM(bonus_amount), 0) 
            FROM referral_bonuses 
            WHERE referrer_id = NEW.referrer_id AND level = 1
        ),
        level_2_earnings = (
            SELECT COALESCE(SUM(bonus_amount), 0) 
            FROM referral_bonuses 
            WHERE referrer_id = NEW.referrer_id AND level = 2
        ),
        level_3_earnings = (
            SELECT COALESCE(SUM(bonus_amount), 0) 
            FROM referral_bonuses 
            WHERE referrer_id = NEW.referrer_id AND level = 3
        ),
        total_earnings = (
            SELECT COALESCE(SUM(bonus_amount), 0) 
            FROM referral_bonuses 
            WHERE referrer_id = NEW.referrer_id
        ),
        last_updated = CURRENT_TIMESTAMP
    WHERE user_id = NEW.referrer_id;
END;

-- Добавляем комментарии к таблицам
-- SQLite не поддерживает COMMENT, но оставляем для документации
-- referral_tree: Основная таблица дерева рефералов с поддержкой 3 уровней
-- referral_bonuses: Таблица начисленных бонусов по уровням
-- referral_stats: Агрегированная статистика для быстрого доступа
