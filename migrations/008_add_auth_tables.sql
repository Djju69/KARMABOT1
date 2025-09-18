-- Add authentication tables

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users_auth (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending_verification' CHECK (status IN ('active', 'inactive', 'suspended', 'pending_verification')),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'partner', 'moderator', 'admin', 'superadmin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    verification_token VARCHAR(100),
    verification_token_expires TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(100),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    avatar_url VARCHAR(255),
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_auth_email ON users_auth (email);
CREATE INDEX IF NOT EXISTS idx_users_auth_username ON users_auth (username);
CREATE INDEX IF NOT EXISTS idx_users_auth_status ON users_auth (status);

-- Refresh tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_auth(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    user_agent TEXT,
    ip_address VARCHAR(45),
    is_revoked BOOLEAN DEFAULT FALSE
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens (token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens (expires_at);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_auth(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL UNIQUE,
    user_agent TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions (session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions (expires_at);

-- Create function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;   
END;
$$ LANGUAGE plpgsql;

-- Create trigger for users_auth table
DROP TRIGGER IF EXISTS update_users_auth_updated_at ON users_auth;
CREATE TRIGGER update_users_auth_updated_at
BEFORE UPDATE ON users_auth
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for refresh_tokens table
DROP TRIGGER IF EXISTS update_refresh_tokens_last_used_at ON refresh_tokens;
CREATE TRIGGER update_refresh_tokens_last_used_at
BEFORE UPDATE ON refresh_tokens
FOR EACH ROW
WHEN (NEW.last_used_at IS DISTINCT FROM OLD.last_used_at)
EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for user_sessions table
DROP TRIGGER IF EXISTS update_user_sessions_last_activity ON user_sessions;
CREATE TRIGGER update_user_sessions_last_activity
BEFORE UPDATE ON user_sessions
FOR EACH ROW
WHEN (NEW.last_activity IS DISTINCT FROM OLD.last_activity)
EXECUTE FUNCTION update_updated_at_column();

-- Add comments for tables and columns
COMMENT ON TABLE users_auth IS 'Stores user authentication and profile information';
COMMENT ON COLUMN users_auth.email IS 'User email address, must be unique';
COMMENT ON COLUMN users_auth.hashed_password IS 'Hashed password using bcrypt';
COMMENT ON COLUMN users_auth.status IS 'User account status: active, inactive, suspended, pending_verification';
COMMENT ON COLUMN users_auth.role IS 'User role: user, partner, moderator, admin, superadmin';

COMMENT ON TABLE refresh_tokens IS 'Stores refresh tokens for JWT authentication';
COMMENT ON COLUMN refresh_tokens.token IS 'The refresh token string';
COMMENT ON COLUMN refresh_tokens.expires_at IS 'When the token expires';

COMMENT ON TABLE user_sessions IS 'Tracks user sessions for active logins';
COMMENT ON COLUMN user_sessions.session_id IS 'Unique session identifier';
COMMENT ON COLUMN user_sessions.expires_at IS 'When the session expires';

-- Create a default admin user (password: admin123 - change this in production!)
-- This is just for initial setup and should be changed immediately after first login
INSERT INTO users_auth (
    email, 
    username, 
    hashed_password, 
    full_name, 
    is_active, 
    is_verified, 
    status, 
    role
) VALUES (
    'admin@example.com',
    'admin',
    -- bcrypt hash for 'admin123'
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Administrator',
    TRUE,
    TRUE,
    'active',
    'superadmin'
) ON CONFLICT (email) DO NOTHING;
