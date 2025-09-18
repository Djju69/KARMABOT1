# 🔧 НАСТРОЙКА ПОДКЛЮЧЕНИЯ К SUPABASE

## ✅ У ВАС ЕСТЬ ПРОЕКТ SUPABASE!

**Project URL:** `https://svtotgesqufeazjkztlv.supabase.co`  
**API Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## 🚀 ШАГ 1: ПОЛУЧИТЬ DATABASE CONNECTION STRING

1. **Зайти в Supabase Dashboard:** https://supabase.com/dashboard
2. **Выбрать проект:** `svtotgesqufeazjkztlv`
3. **Перейти в:** Settings → Database
4. **Найти секцию:** "Connection string"
5. **Выбрать:** "URI" (не "psql")
6. **Скопировать строку** вида:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.svtotgesqufeazjkztlv.supabase.co:5432/postgres
   ```

## 🚀 ШАГ 2: НАСТРОИТЬ В RAILWAY

### В Railway Dashboard:
1. **Перейти в:** Variables
2. **Добавить переменные:**
   ```
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.svtotgesqufeazjkztlv.supabase.co:5432/postgres
   APPLY_MIGRATIONS=1
   ```

## 🚀 ШАГ 3: ПРОВЕРИТЬ РАБОТУ

После настройки:
1. **Перезапустить бота** в Railway
2. **Протестировать:** `python test_supabase_functions.py`
3. **Проверить функции** создания карточек и партнерства

## 🔍 ЕСЛИ НЕ НАХОДИТЕ CONNECTION STRING

В Supabase Dashboard:
1. **Settings** → **Database**
2. **Прокрутить вниз** до секции "Connection string"
3. **Выбрать вкладку "URI"**
4. **Скопировать строку** с вашим паролем

## ⚠️ ВАЖНО

- **Замените `[YOUR-PASSWORD]`** на реальный пароль от проекта
- **Пароль** был создан при создании проекта Supabase
- **Если забыли пароль** - можно сбросить в Settings → Database → Reset database password
