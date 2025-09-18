-- SQL скрипт для создания таблиц в Supabase PostgreSQL
-- Выполните этот скрипт в Supabase Dashboard → SQL Editor

-- Создание таблицы категорий
CREATE TABLE IF NOT EXISTS categories_v2 (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    emoji VARCHAR(10),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    priority_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы партнеров
CREATE TABLE IF NOT EXISTS partners_v2 (
    id SERIAL PRIMARY KEY,
    tg_user_id BIGINT UNIQUE NOT NULL,
    display_name VARCHAR(200),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы карточек
CREATE TABLE IF NOT EXISTS cards_v2 (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL REFERENCES partners_v2(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories_v2(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    address TEXT,
    contact VARCHAR(100),
    google_maps_url TEXT,
    discount_text TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы фотографий карточек
CREATE TABLE IF NOT EXISTS card_photos (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards_v2(id) ON DELETE CASCADE,
    file_id VARCHAR(200) NOT NULL,
    file_path VARCHAR(500),
    is_main BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_partners_tg_user_id ON partners_v2(tg_user_id);
CREATE INDEX IF NOT EXISTS idx_cards_category_id ON cards_v2(category_id);
CREATE INDEX IF NOT EXISTS idx_cards_status ON cards_v2(status);
CREATE INDEX IF NOT EXISTS idx_cards_partner_id ON cards_v2(partner_id);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories_v2(slug);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories_v2(is_active);

-- Добавление тестовых данных
INSERT INTO categories_v2 (name, slug, emoji, description, priority_level) VALUES
('Рестораны', 'restaurants', '🍽️', 'Рестораны и кафе', 100),
('SPA и красота', 'spa', '💆', 'SPA, салоны красоты', 90),
('Транспорт', 'transport', '🚗', 'Такси, аренда авто', 80),
('Отели', 'hotels', '🏨', 'Отели и гостиницы', 70),
('Туры', 'tours', '✈️', 'Туристические услуги', 60),
('Магазины', 'shops', '🛍️', 'Магазины и торговля', 50)
ON CONFLICT (slug) DO NOTHING;

-- Добавление тестового партнера
INSERT INTO partners_v2 (tg_user_id, display_name, phone, email, is_verified, is_active) VALUES
(7006636786, 'Тестовый партнер', '+7 (999) 123-45-67', 'test@example.com', true, true)
ON CONFLICT (tg_user_id) DO UPDATE SET display_name = EXCLUDED.display_name;

-- Добавление тестовых карточек
INSERT INTO cards_v2 (partner_id, category_id, title, description, address, contact, discount_text, status) VALUES
(1, 1, 'Ресторан "Вкусно"', 'Лучшие блюда города', 'ул. Центральная, 1', '+7 (999) 111-11-11', 'Скидка 20% на все блюда', 'approved'),
(1, 2, 'SPA "Релакс"', 'Полный спектр SPA услуг', 'ул. Мира, 15', '+7 (999) 222-22-22', 'Скидка 30% на массаж', 'approved'),
(1, 3, 'Такси "Быстро"', 'Быстрое и надежное такси', 'ул. Транспортная, 5', '+7 (999) 333-33-33', 'Скидка 15% на поездки', 'approved'),
(1, 4, 'Отель "Комфорт"', 'Уютные номера в центре', 'ул. Гостиничная, 10', '+7 (999) 444-44-44', 'Скидка 25% на проживание', 'approved'),
(1, 5, 'Туры "Приключения"', 'Интересные экскурсии', 'ул. Туристическая, 3', '+7 (999) 555-55-55', 'Скидка 20% на туры', 'approved'),
(1, 6, 'Магазин "Все для дома"', 'Товары для дома и сада', 'ул. Торговая, 7', '+7 (999) 666-66-66', 'Скидка 10% на все товары', 'approved');

-- Проверка созданных таблиц
SELECT 'categories_v2' as table_name, COUNT(*) as count FROM categories_v2
UNION ALL
SELECT 'partners_v2' as table_name, COUNT(*) as count FROM partners_v2
UNION ALL
SELECT 'cards_v2' as table_name, COUNT(*) as count FROM cards_v2;
