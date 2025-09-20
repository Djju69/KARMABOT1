-- Создание таблицы для хранения настроек двухфакторной аутентификации
CREATE TABLE IF NOT EXISTS two_factor_auth (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    secret_key VARCHAR(64) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    
    -- Ограничения
    CONSTRAINT fk_user
        FOREIGN KEY (user_id) 
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_user_id
        UNIQUE (user_id)
);

-- Создание таблицы для аудита действий пользователей
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id BIGINT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Ограничения
    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- Создаем индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- Создаем функцию для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создаем триггер для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_two_factor_auth_updated_at ON two_factor_auth;
CREATE TRIGGER update_two_factor_auth_updated_at
BEFORE UPDATE ON two_factor_auth
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Добавляем комментарии к таблицам и колонкам
COMMENT ON TABLE two_factor_auth IS 'Настройки двухфакторной аутентификации пользователей';
COMMENT ON COLUMN two_factor_auth.user_id IS 'ID пользователя';
COMMENT ON COLUMN two_factor_auth.secret_key IS 'Секретный ключ для генерации кодов';
COMMENT ON COLUMN two_factor_auth.is_enabled IS 'Включена ли 2FA';
COMMENT ON COLUMN two_factor_auth.created_at IS 'Дата создания записи';
COMMENT ON COLUMN two_factor_auth.updated_at IS 'Дата последнего обновления записи';
COMMENT ON COLUMN two_factor_auth.last_used_at IS 'Дата последнего успешного использования';

COMMENT ON TABLE audit_log IS 'Лог аудита действий пользователей';
COMMENT ON COLUMN audit_log.user_id IS 'ID пользователя, выполнившего действие';
COMMENT ON COLUMN audit_log.action IS 'Тип действия';
COMMENT ON COLUMN audit_log.entity_type IS 'Тип сущности, к которой относится действие';
COMMENT ON COLUMN audit_log.entity_id IS 'ID сущности, к которой относится действие';
COMMENT ON COLUMN audit_log.ip_address IS 'IP-адрес, с которого выполнено действие';
COMMENT ON COLUMN audit_log.user_agent IS 'User-Agent пользователя';
COMMENT ON COLUMN audit_log.metadata IS 'Дополнительные метаданные действия';
COMMENT ON COLUMN audit_log.created_at IS 'Дата и время действия';

-- Добавляем права доступа
GRANT SELECT, INSERT, UPDATE ON two_factor_auth TO karma_bot;
GRANT USAGE, SELECT ON SEQUENCE two_factor_auth_id_seq TO karma_bot;

GRANT SELECT, INSERT ON audit_log TO karma_bot;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO karma_bot;
