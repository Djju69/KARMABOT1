-- Создание таблицы user_cards для хранения пластиковых карт
CREATE TABLE IF NOT EXISTS user_cards (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_uid TEXT NOT NULL UNIQUE,
    card_hash TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

COMMENT ON TABLE user_cards IS 'Пластиковые карты пользователей для оффлайн-идентификации';
COMMENT ON COLUMN user_cards.card_uid IS 'Уникальный идентификатор карты (видимый номер/UID)';
COMMENT ON COLUMN user_cards.card_hash IS 'Хэш номера карты (SHA-256 + соль)';
COMMENT ON COLUMN user_cards.pin_hash IS 'Хэш PIN-кода (Argon2id/bcrypt)';
COMMENT ON COLUMN user_cards.status IS 'Статус карты: active или blocked';

-- Создание таблицы redeem_receipts для хранения чеков погашения скидок
CREATE TABLE IF NOT EXISTS redeem_receipts (
    id BIGSERIAL PRIMARY KEY,
    jti UUID REFERENCES qr_issues(jti) ON DELETE SET NULL,
    listing_id BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    partner_profile_id BIGINT NOT NULL REFERENCES partner_profiles(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    bill_amount BIGINT NOT NULL,
    discount_rule JSONB NOT NULL,
    discount_amount BIGINT NOT NULL,
    final_amount BIGINT NOT NULL,
    points_earned INTEGER DEFAULT 0,
    redemption_method TEXT NOT NULL CHECK (redemption_method IN ('qr', 'card')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Создание индексов для таблицы redeem_receipts
CREATE INDEX IF NOT EXISTS idx_redeem_receipts_listing_created ON redeem_receipts(listing_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_redeem_receipts_partner_created ON redeem_receipts(partner_profile_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_redeem_receipts_user_created ON redeem_receipts(user_id, created_at DESC) WHERE user_id IS NOT NULL;

COMMENT ON TABLE redeem_receipts IS 'Чеки погашения скидок';
COMMENT ON COLUMN redeem_receipts.jti IS 'Идентификатор QR-кода (если погашение по QR)';
COMMENT ON COLUMN redeem_receipts.bill_amount IS 'Сумма чека в копейках';
COMMENT ON COLUMN redeem_receipts.discount_rule IS 'Правило скидки (слепок offer_details на момент погашения)';
COMMENT ON COLUMN redeem_receipts.discount_amount IS 'Сумма скидки в копейках';
COMMENT ON COLUMN redeem_receipts.final_amount IS 'Итоговая сумма к оплате в копейках';
COMMENT ON COLUMN redeem_receipts.points_earned IS 'Начисленные баллы лояльности';
COMMENT ON COLUMN redeem_receipts.redemption_method IS 'Способ погашения: qr или card';

-- Создание или обновление таблицы qr_issues, если она еще не существует
CREATE TABLE IF NOT EXISTS qr_issues (
    id BIGSERIAL PRIMARY KEY,
    jti UUID NOT NULL UNIQUE,
    listing_id BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'issued' CHECK (status IN ('issued', 'redeemed', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exp_at TIMESTAMPTZ NOT NULL,
    redeemed_at TIMESTAMPTZ,
    redeemed_by_partner_id BIGINT REFERENCES partner_profiles(id) ON DELETE SET NULL
);

-- Создание индексов для таблицы qr_issues
CREATE INDEX IF NOT EXISTS idx_qr_issues_jti ON qr_issues(jti);
CREATE INDEX IF NOT EXISTS idx_qr_issues_user_id ON qr_issues(user_id);
CREATE INDEX IF NOT EXISTS idx_qr_issues_status ON qr_issues(status);
CREATE INDEX IF NOT EXISTS idx_qr_issues_exp_at ON qr_issues(exp_at) WHERE status = 'issued';

-- Добавление комментариев к таблице qr_issues, если их еще нет
COMMENT ON TABLE qr_issues IS 'Выпущенные QR-коды для скидок';
COMMENT ON COLUMN qr_issues.jti IS 'Уникальный идентификатор QR-кода (JWT ID)';
COMMENT ON COLUMN qr_issues.status IS 'Статус: issued, redeemed или expired';
COMMENT ON COLUMN qr_issues.exp_at IS 'Срок действия кода';

-- Функция для обновления временных меток
CREATE OR REPLACE FUNCTION update_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_user_cards_timestamp ON user_cards;
CREATE TRIGGER update_user_cards_timestamp
BEFORE UPDATE ON user_cards
FOR EACH ROW
EXECUTE FUNCTION update_timestamps();

-- Функция для пометки просроченных QR-кодов
CREATE OR REPLACE FUNCTION mark_expired_qr_codes()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE qr_issues 
    SET status = 'expired' 
    WHERE status = 'issued' 
    AND exp_at < NOW();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер для пометки просроченных кодов
DROP TRIGGER IF EXISTS trigger_mark_expired_qr_codes ON qr_issues;
CREATE TRIGGER trigger_mark_expired_qr_codes
AFTER INSERT OR UPDATE ON qr_issues
EXECUTE FUNCTION mark_expired_qr_codes();

-- Добавление i18n строк, если их еще нет
INSERT INTO i18n (key, ru, en) VALUES 
    ('btn.create_qr', '🎫 Создать QR', '🎫 Create QR'),
    ('qr_issue_rate_limited', '⚠️ Слишком часто. Попробуйте позже.', '⚠️ Too many requests. Please try again later.'),
    ('redeem.success', '✅ Скидка применена: −%{discount} • к оплате %{final}', '✅ Discount applied: −%{discount} • to pay %{final}'),
    ('scan.alt_card_entry', '🔢 Ввести номер карты', '🔢 Enter card number'),
    ('card.bind.prompt', 'Введите номер карты (UID)', 'Enter card number (UID)'),
    ('card.bind.ok', '✅ Карта привязана к профилю', '✅ Card linked to profile'),
    ('card.bind.occupied', '⛔ Карта уже привязана', '⛔ Card already in use'),
    ('card.bind.blocked', '⛔ Карта заблокирована', '⛔ Card is blocked'),
    ('card.redeem.success', '✅ Скидка применена по карте', '✅ Discount applied using card'),
    ('card.redeem.pin_invalid', '⛔ Неверный PIN', '⛔ Invalid PIN'),
    ('card.redeem.card_blocked', '⛔ Карта заблокирована', '⛔ Card is blocked'),
    ('cap.missing', 'Недостаточно прав для действия', 'Insufficient permissions')
ON CONFLICT (key) DO NOTHING;
