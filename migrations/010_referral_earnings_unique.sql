-- Миграция для добавления UNIQUE ограничения на source_transaction_id в referral_earnings

-- Создаем таблицу referral_earnings если она не существует
CREATE TABLE IF NOT EXISTS referral_earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID NOT NULL,
    referee_id UUID NOT NULL,
    source_transaction_id UUID NOT NULL UNIQUE,
    amount INTEGER NOT NULL CHECK (amount > 0),
    level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1 AND level <= 3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_referral_earnings_referrer
        FOREIGN KEY (referrer_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_referral_earnings_referee
        FOREIGN KEY (referee_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_referral_earnings_source_transaction
        FOREIGN KEY (source_transaction_id)
        REFERENCES loyalty_transactions(id)
        ON DELETE CASCADE
);

-- Создаем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_referral_earnings_referrer_id ON referral_earnings(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_referee_id ON referral_earnings(referee_id);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_created_at ON referral_earnings(created_at);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_level ON referral_earnings(level);

-- Создаем уникальный индекс на source_transaction_id (если еще не существует)
CREATE UNIQUE INDEX IF NOT EXISTS idx_referral_earnings_source_transaction_unique 
ON referral_earnings(source_transaction_id);

-- Создаем функцию для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_referral_earnings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создаем триггер для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_referral_earnings_updated_at ON referral_earnings;
CREATE TRIGGER update_referral_earnings_updated_at
    BEFORE UPDATE ON referral_earnings
    FOR EACH ROW
    EXECUTE FUNCTION update_referral_earnings_updated_at();

-- Добавляем комментарии к таблице и колонкам
COMMENT ON TABLE referral_earnings IS 'Доходы от реферальной программы';
COMMENT ON COLUMN referral_earnings.referrer_id IS 'ID пользователя, который пригласил';
COMMENT ON COLUMN referral_earnings.referee_id IS 'ID приглашенного пользователя';
COMMENT ON COLUMN referral_earnings.source_transaction_id IS 'ID транзакции лояльности, которая стала источником дохода';
COMMENT ON COLUMN referral_earnings.amount IS 'Сумма дохода в баллах';
COMMENT ON COLUMN referral_earnings.level IS 'Уровень реферала (1-3)';
COMMENT ON COLUMN referral_earnings.created_at IS 'Дата создания записи';
COMMENT ON COLUMN referral_earnings.updated_at IS 'Дата последнего обновления записи';
