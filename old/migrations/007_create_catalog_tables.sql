-- Миграция для создания таблиц каталога заведений

-- Таблица мест (заведений)
CREATE TABLE IF NOT EXISTS places (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    address VARCHAR(500) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    phone VARCHAR(50),
    email VARCHAR(100),
    website VARCHAR(200),
    working_hours JSONB,
    rating FLOAT DEFAULT 0.0,
    reviews_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Таблица категорий (если еще не существует)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Связь многие-ко-многим между местами и категориями
CREATE TABLE IF NOT EXISTS place_categories (
    place_id INTEGER REFERENCES places(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (place_id, category_id)
);

-- Таблица медиа (фото, видео)
CREATE TABLE IF NOT EXISTS media (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL,
    is_cover BOOLEAN DEFAULT FALSE,
    place_id INTEGER REFERENCES places(id) ON DELETE CASCADE,
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Таблица отзывов
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    place_id INTEGER REFERENCES places(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Создаем индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_places_name ON places(name);
CREATE INDEX IF NOT EXISTS idx_places_owner ON places(owner_id);
CREATE INDEX IF NOT EXISTS idx_places_verified ON places(is_verified) WHERE is_verified = TRUE;
CREATE INDEX IF NOT EXISTS idx_media_place ON media(place_id);
CREATE INDEX IF NOT EXISTS idx_reviews_place ON reviews(place_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);

-- Комментарии к таблицам и полям
COMMENT ON TABLE places IS 'Таблица заведений (мест)';
COMMENT ON COLUMN places.working_hours IS 'График работы в формате JSON';
COMMENT ON COLUMN places.rating IS 'Средний рейтинг на основе отзывов (1-5)';

-- Добавляем триггер для обновления поля updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создаем триггеры для обновления временных меток
DO $$
BEGIN
    -- Для таблицы places
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_places_updated_at') THEN
        CREATE TRIGGER update_places_updated_at
        BEFORE UPDATE ON places
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    END IF;

    -- Для таблицы categories
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_categories_updated_at') THEN
        CREATE TRIGGER update_categories_updated_at
        BEFORE UPDATE ON categories
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    END IF;

    -- Для таблицы media
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_media_updated_at') THEN
        CREATE TRIGGER update_media_updated_at
        BEFORE UPDATE ON media
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    END IF;

    -- Для таблицы reviews
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_reviews_updated_at') THEN
        CREATE TRIGGER update_reviews_updated_at
        BEFORE UPDATE ON reviews
        FOR EACH ROW EXECUTE FUNCTION update_modified_column();
    END IF;
END
$$;
