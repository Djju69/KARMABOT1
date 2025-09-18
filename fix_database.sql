-- Исправление проблем с базой данных Karma System
-- Дата: 2025-01-10

-- 1. Исправить дублирование karma_points
DO $$ 
BEGIN
    -- Проверяем, существует ли колонка karma_points
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='karma_points'
    ) THEN
        ALTER TABLE users ADD COLUMN karma_points INTEGER DEFAULT 0;
    END IF;
EXCEPTION
    WHEN duplicate_column THEN 
        -- Если колонка уже существует, просто продолжаем
        NULL;
END $$;

-- 2. Создать таблицу cards_generated если не существует
CREATE TABLE IF NOT EXISTS cards_generated (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    card_number VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- 3. Создать индексы для производительности
CREATE INDEX IF NOT EXISTS idx_cards_generated_user_id ON cards_generated(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_generated_active ON cards_generated(is_active);
CREATE INDEX IF NOT EXISTS idx_cards_generated_card_number ON cards_generated(card_number);

-- 4. Добавить недостающие колонки в users если их нет
DO $$
BEGIN
    -- Добавляем policy_accepted если не существует
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='policy_accepted'
    ) THEN
        ALTER TABLE users ADD COLUMN policy_accepted BOOLEAN DEFAULT false;
    END IF;
    
    -- Добавляем referral_code если не существует
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='referral_code'
    ) THEN
        ALTER TABLE users ADD COLUMN referral_code VARCHAR(20) UNIQUE;
    END IF;
    
    -- Добавляем referred_by если не существует
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='referred_by'
    ) THEN
        ALTER TABLE users ADD COLUMN referred_by BIGINT REFERENCES users(telegram_id);
    END IF;
END $$;

-- 5. Создать таблицу для избранного если не существует
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    card_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE,
    UNIQUE(user_id, card_id)
);

-- 6. Создать таблицу для логов кармы если не существует
CREATE TABLE IF NOT EXISTS karma_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- 7. Создать индексы для всех таблиц
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_karma_log_user_id ON karma_log(user_id);

-- 8. Обновить политику конфиденциальности для существующих пользователей (опционально)
-- UPDATE users SET policy_accepted = true WHERE created_at < '2025-01-01';

-- Вывести сообщение об успешном выполнении
DO $$
BEGIN
    RAISE NOTICE 'Database fixes applied successfully!';
END $$;
