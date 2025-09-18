-- СРОЧНОЕ СОЗДАНИЕ НЕДОСТАЮЩИХ ТАБЛИЦ В POSTGRESQL

-- 1. Создай таблицу partners_v2
CREATE TABLE IF NOT EXISTS partners_v2 (
    id SERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    karma_points INTEGER DEFAULT 0,
    level_id INTEGER DEFAULT 1,
    avatar_url VARCHAR(500),
    bio TEXT,
    is_premium BOOLEAN DEFAULT FALSE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Создай таблицу cards_v2
CREATE TABLE IF NOT EXISTS cards_v2 (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    card_number VARCHAR(50) UNIQUE NOT NULL,
    card_status VARCHAR(50) DEFAULT 'active',
    balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(tg_user_id)
);

-- 3. Создай таблицу categories_v2
CREATE TABLE IF NOT EXISTS categories_v2 (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    emoji VARCHAR(10),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    priority_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Создай индексы
CREATE INDEX IF NOT EXISTS idx_partners_v2_tg_user_id ON partners_v2(tg_user_id);
CREATE INDEX IF NOT EXISTS idx_cards_v2_user_id ON cards_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_v2_card_number ON cards_v2(card_number);
CREATE INDEX IF NOT EXISTS idx_categories_v2_slug ON categories_v2(slug);

-- 5. Вставь базовые категории
INSERT INTO categories_v2 (name, slug, emoji, description, is_active, priority_level)
VALUES 
    ('Рестораны', 'restaurants', '🍽️', 'Рестораны и кафе', TRUE, 10),
    ('СПА и красота', 'spa', '💆', 'СПА, салоны красоты', TRUE, 9),
    ('Транспорт', 'transport', '🚗', 'Такси, аренда авто', TRUE, 8),
    ('Отели', 'hotels', '🏨', 'Отели и гостиницы', TRUE, 7),
    ('Туры', 'tours', '✈️', 'Туристические услуги', TRUE, 6),
    ('Магазины', 'shops', '🛍️', 'Розничная торговля', TRUE, 5)
ON CONFLICT (slug) DO NOTHING;

-- 6. Отметь миграцию как выполненную
INSERT INTO migrations (version, description) VALUES ('021', 'create_partners_v2_and_cards_v2') 
ON CONFLICT (version) DO NOTHING;
