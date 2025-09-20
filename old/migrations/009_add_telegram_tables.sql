-- Add Telegram integration tables

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create telegram_users table
CREATE TABLE IF NOT EXISTS telegram_users (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_auth(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    is_bot BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_telegram_user UNIQUE (user_id, telegram_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_telegram_users_telegram_id ON telegram_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_telegram_users_user_id ON telegram_users(user_id);

-- Create telegram_auth_tokens table
CREATE TABLE IF NOT EXISTS telegram_auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_auth(id) ON DELETE CASCADE,
    token VARCHAR(100) NOT NULL UNIQUE,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_telegram_auth_token UNIQUE (token)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_telegram_auth_tokens_token ON telegram_auth_tokens(token);
CREATE INDEX IF NOT EXISTS idx_telegram_auth_tokens_user_id ON telegram_auth_tokens(user_id);

-- Add comment to the tables
COMMENT ON TABLE telegram_users IS 'Хранит привязку аккаунтов Telegram к пользователям системы';
COMMENT ON TABLE telegram_auth_tokens IS 'Хранит токены для авторизации через Telegram';

-- Add comments to the columns
COMMENT ON COLUMN telegram_users.telegram_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN telegram_users.username IS 'Имя пользователя в Telegram (без @)';
COMMENT ON COLUMN telegram_users.is_active IS 'Активна ли привязка аккаунта';

-- Add function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW; 
END;
$$ LANGUAGE plpgsql;

-- Create trigger for telegram_users
CREATE TRIGGER update_telegram_users_modtime
BEFORE UPDATE ON telegram_users
FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Insert default admin user if not exists (password: admin123)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users_auth WHERE email = 'admin@example.com') THEN
        INSERT INTO users_auth (
            email, 
            username, 
            hashed_password, 
            is_active, 
            is_verified, 
            status, 
            role
        ) VALUES (
            'admin@example.com',
            'admin',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- bcrypt hash of 'admin123'
            TRUE,
            TRUE,
            'active',
            'admin'
        );
    END IF;
END $$;
