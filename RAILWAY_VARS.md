# Railway Environment Variables

## Обязательные переменные для Railway

### 🤖 Telegram Bot
```
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_admin_telegram_id
```

### 🗄️ Database
```
DATABASE_URL=postgresql://postgres:password@postgres.railway.internal:5432/railway
```

### 🔴 Redis
```
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

### 🔐 Security
```
SECRET_KEY=your_very_long_and_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### 🌐 WebApp
```
WEBHOOK_URL=https://your-app.railway.app
WEBHOOK_SECRET=your_webhook_secret_here
```

### 📊 Monitoring
```
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO
```

### ⚙️ Application
```
ENVIRONMENT=production
PORT=8000
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

## 🚀 Railway Configuration

### Railway.json уже настроен:
- ✅ PostgreSQL plugin enabled
- ✅ Redis plugin enabled
- ✅ Health check на `/health`
- ✅ Start command: `python start.py`
- ✅ Build command: `pip install -r requirements.txt`

### Dockerfile готов:
- ✅ Python 3.11-slim base image
- ✅ Все зависимости установлены
- ✅ Порт 8080 экспонирован
- ✅ Команда запуска настроена

## 📋 Checklist для деплоя:

1. ✅ **Создать проект на Railway**
2. ✅ **Подключить GitHub репозиторий**
3. ✅ **Добавить PostgreSQL service**
4. ✅ **Добавить Redis service**
5. ✅ **Настроить переменные окружения**
6. ✅ **Деплой автоматически запустится**

## 🔧 Настройка переменных в Railway:

1. Перейти в Railway Dashboard
2. Выбрать ваш проект
3. Перейти в Variables
4. Добавить все переменные из списка выше
5. Сохранить изменения

## 🚨 Важные моменты:

- **BOT_TOKEN** - получить у @BotFather в Telegram
- **ADMIN_ID** - ваш Telegram ID
- **DATABASE_URL** - Railway автоматически создаст
- **REDIS_URL** - Railway автоматически создаст
- **SECRET_KEY** - сгенерировать случайную строку
- **WEBHOOK_URL** - будет автоматически установлен Railway

## 🎯 После деплоя:

1. Проверить логи в Railway Dashboard
2. Убедиться что health check проходит
3. Протестировать бота в Telegram
4. Проверить WebApp интерфейс
