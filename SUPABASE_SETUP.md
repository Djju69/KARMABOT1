# 🔧 НАСТРОЙКА SUPABASE ДЛЯ KARMABOT

## 🚨 ПРОБЛЕМА
Система использует SQLite вместо PostgreSQL (Supabase), поэтому функции создания карточек и партнерства не работают.

## ✅ РЕШЕНИЕ

### 1. Получить данные Supabase
1. Зайти в [Supabase Dashboard](https://supabase.com/dashboard)
2. Выбрать ваш проект
3. Перейти в **Settings** → **Database**
4. Скопировать **Connection string** (URI)

### 2. Настроить переменные окружения

#### Для локальной разработки:
Создать файл `.env` в корне проекта:
```env
# Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Включить миграции
APPLY_MIGRATIONS=1

# Другие переменные
BOT_TOKEN=your_bot_token
REDIS_URL=redis://localhost:6379/0
```

#### Для Railway (Production):
В Railway Dashboard → Variables добавить:
```
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
APPLY_MIGRATIONS=1
```

### 3. Проверить подключение
```bash
python test_supabase_functions.py
```

## 🔍 ПРОВЕРКА

После настройки `DATABASE_URL` система должна:
- ✅ Подключаться к PostgreSQL (Supabase)
- ✅ Создавать таблицы через миграции
- ✅ Позволять создавать партнеров
- ✅ Позволять создавать карточки

## 📋 СЛЕДУЮЩИЕ ШАГИ

1. **Настроить DATABASE_URL** для Supabase
2. **Включить миграции** (APPLY_MIGRATIONS=1)
3. **Протестировать функции** создания партнеров и карточек
4. **Проверить WebApp** кабинеты

## 🆘 ЕСЛИ НЕТ SUPABASE ПРОЕКТА

Создать новый проект:
1. Зайти на [supabase.com](https://supabase.com)
2. Нажать **"New Project"**
3. Выбрать организацию
4. Ввести название проекта
5. Сгенерировать пароль
6. Выбрать регион
7. Нажать **"Create new project"**
8. Дождаться создания (2-3 минуты)
9. Скопировать Connection string из Settings → Database
