# Настройка Supabase для KARMABOT1

## 1. Создание проекта в Supabase

1. Перейти на [supabase.com](https://supabase.com)
2. Войти в аккаунт или зарегистрироваться
3. Нажать "New Project"
4. Выбрать организацию
5. Ввести название проекта: `karmabot1`
6. Ввести пароль для базы данных
7. Выбрать регион (ближайший к Railway)
8. Нажать "Create new project"

## 2. Получение данных подключения

1. В проекте перейти в Settings → API
2. Скопировать:
   - **Project URL** (например: `https://your-project.supabase.co`)
   - **anon public** ключ (начинается с `eyJ...`)

## 3. Настройка переменных окружения в Railway

1. Перейти в Railway Dashboard
2. Выбрать проект KARMABOT1
3. Перейти в Variables
4. Добавить переменные:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ... (ваш anon public ключ)
```

## 4. Создание таблиц в Supabase

Выполнить SQL в Supabase SQL Editor:

```sql
-- Таблица профилей пользователей
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT DEFAULT 'ru',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица лояльности
CREATE TABLE loyalty_points (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    points INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица транзакций лояльности
CREATE TABLE loyalty_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    points_spent INTEGER NOT NULL,
    reason TEXT,
    partner_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица партнерских карт
CREATE TABLE partner_cards (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    card_number TEXT NOT NULL,
    partner_id BIGINT NOT NULL,
    activated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_loyalty_points_user_id ON loyalty_points(user_id);
CREATE INDEX idx_loyalty_transactions_user_id ON loyalty_transactions(user_id);
CREATE INDEX idx_partner_cards_user_id ON partner_cards(user_id);
```

## 5. Настройка Row Level Security (RLS)

```sql
-- Включить RLS для всех таблиц
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE partner_cards ENABLE ROW LEVEL SECURITY;

-- Политики для анонимного доступа (для бота)
CREATE POLICY "Allow anonymous access" ON user_profiles FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON loyalty_points FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON loyalty_transactions FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON partner_cards FOR ALL USING (true);
```

## 6. Проверка подключения

После настройки в логах Railway должно появиться:
```
✅ Supabase client initialized successfully
```

## 7. Архитектура баз данных

**Railway PostgreSQL (основная БД):**
- Основной функционал бота
- Таблицы: cards_v2, card_photos, users, partners_v2
- Каталоги, категории, партнеры

**Supabase (дополнительная БД):**
- Система лояльности
- Профили пользователей
- Партнерские карты
- История транзакций

## 8. Fallback механизм

Если Supabase недоступен, система автоматически переключается на заглушки:
- Все операции возвращают успешный результат
- Данные сохраняются в локальном кеше
- При восстановлении Supabase данные синхронизируются

## 9. Мониторинг

Проверить статус Supabase можно через:
- Логи Railway
- Supabase Dashboard → Logs
- Health check endpoint (если реализован)
