# 🚀 KARMABOT1 - Деплой на Railway.app

## 📋 Что нужно от вас

### 1. Подготовка GitHub репозитория
```bash
# Перейти в папку проекта
cd C:\Users\d9955\CascadeProjects\KARMABOT1-fixed

# Инициализировать git (если еще не сделано)
git init
git add .
git commit -m "Initial KARMABOT1 v2.0 deployment ready"

# Подключить к вашему GitHub репозиторию
git remote add origin https://github.com/YOUR_USERNAME/KARMABOT1.git
git push -u origin main
```

### 2. Настройка Railway проекта

#### В Railway Dashboard:
1. **Connect GitHub** - подключите ваш репозиторий
2. **Add Variables** - добавьте переменные окружения:

```bash
# Обязательные переменные
BOT_TOKEN=7619342315:AAFU8c7uNN6KClV0MSGDKnWWAWw2X5ho-Fg
ADMIN_ID=6391215556
FERNET_KEY_HEX=729191104e4400c325e25b204175bd896297e2bc83520c968a9c105aaad9f9cc

# База данных (Railway автоматически создаст PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (если нужен)
REDIS_URL=${{Redis.REDIS_URL}}

# Настройки
LOG_LEVEL=INFO
ENVIRONMENT=production
RAILWAY_ENVIRONMENT=production

# Фича-флаги (начните с выключенными для безопасности)
FEATURE_PARTNER_FSM=false
FEATURE_MODERATION=false
FEATURE_NEW_MENU=false
FEATURE_QR_WEBAPP=false
FEATURE_LISTEN_NOTIFY=false
```

#### Получить ваш ADMIN_ID:
1. Напишите боту @userinfobot в Telegram
2. Он покажет ваш ID - используйте его как ADMIN_ID

### 3. Добавление сервисов в Railway

#### PostgreSQL Database:
1. В Railway проекте нажмите **"+ New"**
2. Выберите **"Database" → "PostgreSQL"**
3. Railway автоматически создаст переменную `DATABASE_URL`

#### Redis (опционально):
1. Нажмите **"+ New"**
2. Выберите **"Database" → "Redis"**
3. Railway создаст переменную `REDIS_URL`

## 🚀 Деплой

### Автоматический деплой
После push в GitHub, Railway автоматически:
1. Установит зависимости из `requirements.txt`
2. Запустит `python main_v2.py` (из `Procfile`)
3. Применит миграции БД автоматически

### Проверка деплоя
1. В Railway Dashboard смотрите **Logs**
2. Должны увидеть:
```
🤖 KARMABOT1 v2.0 starting...
✅ Database migrations completed
🚀 Bot started successfully
```

## 🔧 Поэтапное включение функций

### Фаза 1: Базовая работа (текущая)
```bash
FEATURE_PARTNER_FSM=false
FEATURE_MODERATION=false
FEATURE_NEW_MENU=false
```
Бот работает в legacy режиме - полная совместимость.

### Фаза 2: Новые функции
```bash
FEATURE_PARTNER_FSM=true      # Включить FSM для партнеров
FEATURE_MODERATION=true       # Включить модерацию
```

### Фаза 3: Полная функциональность
```bash
FEATURE_NEW_MENU=true         # Новое главное меню
FEATURE_QR_WEBAPP=true        # QR коды и веб-приложения
```

## 🐛 Troubleshooting

### Если бот не запускается:
1. Проверьте логи в Railway Dashboard
2. Убедитесь что `BOT_TOKEN` правильный
3. Проверьте что `ADMIN_ID` - это число

### Если ошибки с БД:
1. Убедитесь что PostgreSQL сервис создан
2. Проверьте что `DATABASE_URL` автоматически подставлен
3. Миграции применяются автоматически при старте

### Если нужна помощь:
1. Смотрите логи в Railway
2. Все ошибки логируются с подробностями
3. Контракт-тесты гарантируют стабильность

## ✅ Готово к запуску

Проект полностью подготовлен для Railway:
- ✅ `Procfile` - команда запуска
- ✅ `requirements.txt` - зависимости с PostgreSQL
- ✅ `railway.json` - конфигурация деплоя
- ✅ Автоматические миграции БД
- ✅ Безопасные настройки по умолчанию
- ✅ Полная обратная совместимость

**Следующий шаг:** Push в GitHub и подключение к Railway!
