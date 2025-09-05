-- Миграция для системы профилей пользователей с уровнями
-- Дата: 2025-12-19
-- Описание: Создание таблиц для расширенного профиля пользователя

-- Создание таблицы профилей пользователей
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    
    -- Система уровней
    level VARCHAR(20) DEFAULT 'bronze' CHECK (level IN ('bronze', 'silver', 'gold', 'platinum')),
    level_points INTEGER DEFAULT 0,
    level_progress DECIMAL(5, 2) DEFAULT 0,
    
    -- Статистика активности
    total_visits INTEGER DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    total_qr_scans INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    total_spent DECIMAL(10, 2) DEFAULT 0,
    
    -- Реферальная статистика
    total_referrals INTEGER DEFAULT 0,
    referral_earnings DECIMAL(10, 2) DEFAULT 0,
    
    -- Настройки профиля
    notifications_enabled BOOLEAN DEFAULT 1,
    email_notifications BOOLEAN DEFAULT 1,
    push_notifications BOOLEAN DEFAULT 1,
    privacy_level VARCHAR(50) DEFAULT 'standard',
    
    -- Дополнительная информация
    bio TEXT,
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC+7',
    language VARCHAR(10) DEFAULT 'ru',
    
    -- Временные метки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы логов активности
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_data TEXT,
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы достижений
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(255) NOT NULL,
    achievement_description TEXT,
    points_reward INTEGER DEFAULT 0,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_level ON user_profiles(level);
CREATE INDEX IF NOT EXISTS idx_user_profiles_level_points ON user_profiles(level_points);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_activity ON user_profiles(last_activity);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_type ON user_achievements(achievement_type);
CREATE INDEX IF NOT EXISTS idx_user_achievements_unlocked_at ON user_achievements(unlocked_at);

-- Триггер для автоматического обновления статистики при активности
CREATE TRIGGER IF NOT EXISTS update_user_profile_stats
AFTER INSERT ON user_activity_logs
BEGIN
    UPDATE user_profiles SET
        last_activity = CURRENT_TIMESTAMP,
        level_points = level_points + NEW.points_earned,
        level_progress = (
            CASE 
                WHEN level = 'bronze' THEN MIN(100.0, ((level_points + NEW.points_earned) / 1000.0) * 100.0)
                WHEN level = 'silver' THEN MIN(100.0, (((level_points + NEW.points_earned) - 1000) / 4000.0) * 100.0)
                WHEN level = 'gold' THEN MIN(100.0, (((level_points + NEW.points_earned) - 5000) / 10000.0) * 100.0)
                ELSE 100.0
            END
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
    
    -- Проверяем повышение уровня
    UPDATE user_profiles SET
        level = CASE
            WHEN level = 'bronze' AND level_points >= 1000 THEN 'silver'
            WHEN level = 'silver' AND level_points >= 5000 THEN 'gold'
            WHEN level = 'gold' AND level_points >= 15000 THEN 'platinum'
            ELSE level
        END,
        level_progress = CASE
            WHEN level = 'bronze' AND level_points >= 1000 THEN 0.0
            WHEN level = 'silver' AND level_points >= 5000 THEN 0.0
            WHEN level = 'gold' AND level_points >= 15000 THEN 0.0
            ELSE level_progress
        END
    WHERE user_id = NEW.user_id;
END;

-- Триггер для обновления статистики посещений
CREATE TRIGGER IF NOT EXISTS update_visit_stats
AFTER INSERT ON user_activity_logs
WHEN NEW.activity_type = 'visit'
BEGIN
    UPDATE user_profiles SET
        total_visits = total_visits + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
END;

-- Триггер для обновления статистики отзывов
CREATE TRIGGER IF NOT EXISTS update_review_stats
AFTER INSERT ON user_activity_logs
WHEN NEW.activity_type = 'review'
BEGIN
    UPDATE user_profiles SET
        total_reviews = total_reviews + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
END;

-- Триггер для обновления статистики QR сканирований
CREATE TRIGGER IF NOT EXISTS update_qr_scan_stats
AFTER INSERT ON user_activity_logs
WHEN NEW.activity_type = 'qr_scan'
BEGIN
    UPDATE user_profiles SET
        total_qr_scans = total_qr_scans + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
END;

-- Триггер для обновления статистики покупок
CREATE TRIGGER IF NOT EXISTS update_purchase_stats
AFTER INSERT ON user_activity_logs
WHEN NEW.activity_type = 'purchase'
BEGIN
    UPDATE user_profiles SET
        total_purchases = total_purchases + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
END;

-- Добавляем комментарии к таблицам
-- user_profiles: Расширенный профиль пользователя с системой уровней и статистикой
-- user_activity_logs: Лог активности для отслеживания действий пользователей
-- user_achievements: Достижения и награды пользователей
