-- Миграция для системы лояльности и реферальной программы

-- Таблица транзакций лояльности
CREATE TABLE IF NOT EXISTS loyalty_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    points INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('activity', 'referral_bonus', 'spend', 'manual')),
    activity_type VARCHAR(20) CHECK (activity_type IN (
        'daily_checkin', 'profile_completion', 'card_binding', 'geo_checkin', 'referral_signup'
    )),
    reference_id UUID,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    CONSTRAINT chk_points_not_zero
        CHECK (points != 0)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_loyalty_transactions_user_id ON loyalty_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_loyalty_transactions_created_at ON loyalty_transactions(created_at);

-- Таблица балансов лояльности
CREATE TABLE IF NOT EXISTS loyalty_balances (
    user_id UUID PRIMARY KEY,
    total_points INTEGER NOT NULL DEFAULT 0 CHECK (total_points >= 0),
    available_points INTEGER NOT NULL DEFAULT 0 CHECK (available_points >= 0 AND available_points <= total_points),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_user_balance
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Таблица правил активностей
CREATE TABLE IF NOT EXISTS loyalty_activity_rules (
    activity_type VARCHAR(20) PRIMARY KEY CHECK (activity_type IN (
        'daily_checkin', 'profile_completion', 'card_binding', 'geo_checkin', 'referral_signup'
    )),
    points INTEGER NOT NULL CHECK (points > 0),
    cooldown_hours INTEGER NOT NULL CHECK (cooldown_hours >= 0),
    daily_cap INTEGER CHECK (daily_cap IS NULL OR daily_cap > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Таблица реферальных ссылок
CREATE TABLE IF NOT EXISTS referral_links (
    user_id UUID PRIMARY KEY,
    referral_code VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    CONSTRAINT fk_user_referral
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Таблица рефералов
CREATE TABLE IF NOT EXISTS referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID NOT NULL,
    referee_id UUID NOT NULL UNIQUE,
    referral_code VARCHAR(50) NOT NULL,
    referrer_bonus_awarded BOOLEAN NOT NULL DEFAULT FALSE,
    referee_bonus_awarded BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bonus_awarded_at TIMESTAMPTZ,
    
    CONSTRAINT fk_referrer
        FOREIGN KEY (referrer_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_referee
        FOREIGN KEY (referee_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_referral_code
        FOREIGN KEY (referral_code)
        REFERENCES referral_links(referral_code)
        ON DELETE CASCADE,
    
    CONSTRAINT chk_different_users
        CHECK (referrer_id != referee_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_created_at ON referrals(created_at);

-- Таблица истории активности пользователей
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    activity_type VARCHAR(20) NOT NULL,
    points_awarded INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_user_activity
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Создаем индекс для быстрого поиска по пользователю и типу активности
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_activity 
ON user_activity_logs(user_id, activity_type, created_at);

-- Триггер для обновления времени обновления
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем триггер к таблицам
CREATE TRIGGER update_loyalty_transactions_updated_at
BEFORE UPDATE ON loyalty_transactions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_loyalty_activity_rules_updated_at
BEFORE UPDATE ON loyalty_activity_rules
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Вставляем стандартные правила активностей
INSERT INTO loyalty_activity_rules (activity_type, points, cooldown_hours, daily_cap, is_active)
VALUES 
    ('daily_checkin', 10, 24, 10, true),
    ('profile_completion', 50, 0, NULL, true),
    ('card_binding', 100, 0, NULL, true),
    ('geo_checkin', 20, 4, 3, true),
    ('referral_signup', 50, 0, NULL, true)
ON CONFLICT (activity_type) DO NOTHING;

-- Создаем функцию для начисления баллов
CREATE OR REPLACE FUNCTION award_loyalty_points(
    p_user_id UUID,
    p_points INTEGER,
    p_transaction_type VARCHAR(20),
    p_activity_type VARCHAR(20) DEFAULT NULL,
    p_reference_id UUID DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_transaction_id UUID;
    v_new_balance INTEGER;
BEGIN
    -- Начинаем транзакцию
    BEGIN
        -- Вставляем запись о транзакции
        INSERT INTO loyalty_transactions (
            user_id, 
            points, 
            transaction_type, 
            activity_type, 
            reference_id, 
            description
        ) VALUES (
            p_user_id,
            p_points,
            p_transaction_type,
            p_activity_type,
            p_reference_id,
            p_description
        )
        RETURNING id INTO v_transaction_id;
        
        -- Обновляем баланс пользователя
        INSERT INTO loyalty_balances (user_id, total_points, available_points)
        VALUES (p_user_id, p_points, p_points)
        ON CONFLICT (user_id) 
        DO UPDATE SET
            total_points = loyalty_balances.total_points + EXCLUDED.total_points,
            available_points = loyalty_balances.available_points + EXCLUDED.available_points,
            last_updated = NOW()
        RETURNING available_points INTO v_new_balance;
        
        -- Логируем активность
        IF p_activity_type IS NOT NULL THEN
            INSERT INTO user_activity_logs (user_id, activity_type, points_awarded)
            VALUES (p_user_id, p_activity_type, p_points);
        END IF;
        
        -- Фиксируем транзакцию
        RETURN v_transaction_id;
        
    EXCEPTION WHEN OTHERS THEN
        ROLLBACK;
        RAISE EXCEPTION 'Ошибка при начислении баллов: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;
