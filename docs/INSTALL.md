# 🚀 Установка и деплой KARMABOT1

## 📋 Требования

- Python 3.11+
- PostgreSQL 13+ или SQLite
- Redis (для leader election)
- Railway CLI (для деплоя)

## ⚙️ Установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd KARMABOT1-fixed
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env`:
```env
# Telegram Bot
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id

# Database
DATABASE_URL=postgresql://user:pass@host:port/db
# или для SQLite:
# DATABASE_URL=sqlite:///bot.db

# Redis
REDIS_URL=redis://localhost:6379

# Features
FEATURE_PARTNER_FSM=true
FEATURE_MODERATION=true
FEATURE_VERBOSE_ADMIN_BACK=false
FEATURE_MENU_V2=false

# Odoo Integration (опционально)
ODOO_BASE_URL=https://your-odoo-instance.com
ODOO_DB_USER=karmabot_odoo
ODOO_DB_PASSWORD=your_password
ODOO_DATABASE=odoo
```

## 🗄️ База данных

### Автоматическая миграция
```bash
python -m core.database.migrations
```

### Ручная настройка PostgreSQL
```bash
# Создание роли для Odoo
python scripts/setup_odoo_db.py
```

## 🚀 Деплой на Railway

### 1. Установка Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Авторизация
```bash
railway login
```

### 3. Деплой
```bash
railway up
```

### 4. Настройка переменных
```bash
railway variables set BOT_TOKEN=your_token
railway variables set ADMIN_ID=your_id
railway variables set DATABASE_URL=your_db_url
```

## 🧪 Тестирование

### Запуск тестов
```bash
python -m pytest tests/
```

### Проверка i18n
```bash
python tests/test_i18n_consistency.py
```

### Проверка миграций
```bash
python -m core.database.migrations --check
```

## 🔧 Разработка

### Структура проекта
```
core/
├── handlers/          # Обработчики команд
├── keyboards/          # Клавиатуры
├── services/           # Бизнес-логика
├── database/           # Работа с БД
├── utils/              # Утилиты
└── settings.py         # Настройки

locales/                # Локализация
├── ru.json            # Русский
├── en.json            # Английский
└── deprecated.json    # Устаревшие ключи

docs/                   # Документация
├── INSTALL.md         # Этот файл
├── USER_GUIDE.md      # Руководство пользователя
├── DEV_GUIDE.md       # Руководство разработчика
└── i18n_guide.md     # Руководство по локализации
```

### Правила разработки
- Следуйте Non-Breaking Dev Guide
- Не удаляйте старые i18n ключи
- Используйте фича-флаги для новых функций
- Тестируйте изменения

## 🐛 Отладка

### Логи
```bash
railway logs
```

### Подключение к БД
```bash
railway run python -c "from core.database import db_v2; print(db_v2.get_stats())"
```

### Проверка Redis
```bash
railway run python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `railway logs`
2. Проверьте переменные: `railway variables`
3. Проверьте статус: `railway status`
4. Обратитесь к документации в `docs/`

