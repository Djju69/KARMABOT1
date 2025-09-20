# 🚀 DEPLOYMENT GUIDE - KARMABOT1 Multi-Platform System

## 📋 Обзор развертывания

Система KARMABOT1 теперь полностью готова к развертыванию с новой архитектурой FastAPI и отказоустойчивостью.

## 🎯 Что было развернуто

### ✅ Новая архитектура
- **FastAPI сервер** (`main.py`) вместо старого `main_v2.py`
- **Отказоустойчивая система** с автоматическим переключением БД
- **Мульти-платформенные адаптеры** для всех типов клиентов
- **HTML Dashboard** для мониторинга в реальном времени
- **Система алертов** с Email и Telegram уведомлениями

### ✅ Файлы развертывания
- `Dockerfile` - Docker контейнеризация
- `railway.toml` - Railway конфигурация
- `requirements.txt` - Обновленные зависимости
- `env.example` - Пример переменных окружения

## 🚀 Способы развертывания

### 1. Railway.app (Рекомендуется)

```bash
# Установка Railway CLI
npm install -g @railway/cli

# Логин в Railway
railway login

# Развертывание
railway deploy
```

**Конфигурация Railway:**
- **Start Command**: `python main.py`
- **Port**: 8000 (автоматически)
- **Restart Policy**: ON_FAILURE с 10 попытками

### 2. Docker

```bash
# Сборка образа
docker build -t karmabot1-multiplatform .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env karmabot1-multiplatform
```

### 3. Локальное развертывание

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env.example .env
# Редактируйте .env файл

# Запуск системы
python main.py
```

## ⚙️ Переменные окружения

### Обязательные переменные

```bash
# Базы данных
RAILWAY_POSTGRES_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Сервер
PORT=8000
ENVIRONMENT=production

# Безопасность
SECRET_KEY=your-secret-key
ADMIN_TOKEN=admin_secret_token_2025
```

### Опциональные переменные

```bash
# Алерты и уведомления
ALERT_EMAIL=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_BOT_TOKEN=your-telegram-bot-token
ALERT_CHAT_ID=your-telegram-chat-id
```

## 🔍 Проверка развертывания

### 1. Проверка здоровья системы

```bash
curl http://localhost:8000/v1/admin/health
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "mode": "FULL_OPERATIONAL",
  "timestamp": "2025-01-28T...",
  "uptime": {
    "postgresql": 99.9,
    "supabase": 99.9,
    "overall": 99.9
  }
}
```

### 2. Проверка API документации

Откройте в браузере: `http://localhost:8000/docs`

### 3. Проверка Dashboard

Откройте в браузере: `http://localhost:8000/dashboard`

### 4. Проверка платформ

```bash
curl http://localhost:8000/v1/platforms
```

## 📊 Мониторинг

### Dashboard функции
- **Реальное время**: Автообновление каждые 30 секунд
- **Статус платформ**: Telegram, Website, Mobile, Desktop, API
- **Мониторинг БД**: PostgreSQL и Supabase
- **Очередь операций**: Количество отложенных операций
- **Локальный кеш**: Использование памяти
- **Алерты**: Активные предупреждения
- **Рекомендации**: Советы по оптимизации

### Система алертов
- **Email уведомления**: Критические алерты
- **Telegram уведомления**: Мгновенные алерты
- **Ежедневные отчеты**: Статистика работы системы

## 🧪 Тестирование

### Запуск тестов

```bash
# Комплексные тесты системы
python tests/test_full_system.py

# Тесты API endpoints
python tests/test_api_endpoints.py

# Тесты отказоустойчивости
python tests/test_fault_tolerance.py

# Тесты платформенных адаптеров
python tests/test_platform_adapters.py
```

### Покрытие тестами
- ✅ Создание пользователей на всех платформах
- ✅ Связывание аккаунтов между платформами
- ✅ Создание заказов со всех платформ
- ✅ Отказоустойчивость системы
- ✅ Обработка очереди операций
- ✅ Система мониторинга
- ✅ API endpoints
- ✅ Валидация данных

## 🔧 Режимы работы

### 🟢 FULL_OPERATIONAL
- ✅ PostgreSQL online
- ✅ Supabase online
- ✅ Полная функциональность

### 🟡 POSTGRESQL_ONLY
- ✅ PostgreSQL online
- ❌ Supabase offline
- 🔄 Операции через PostgreSQL

### 🟡 SUPABASE_ONLY
- ❌ PostgreSQL offline
- ✅ Supabase online
- 🔄 Операции через Supabase

### 🔴 CACHE_ONLY
- ❌ Обе базы данных offline
- 💾 Только кеш и очередь
- ⏳ Операции в очереди

## 📈 Производительность

### Ожидаемые метрики
- **Response Time**: < 100ms для большинства операций
- **Uptime**: 99.9% благодаря отказоустойчивости
- **Throughput**: 1000+ запросов в минуту
- **Memory Usage**: < 512MB RAM
- **CPU Usage**: < 50% при нормальной нагрузке

### Масштабирование
- **Horizontal**: Добавление новых инстансов
- **Vertical**: Увеличение ресурсов сервера
- **Database**: Read replicas для PostgreSQL
- **Cache**: Redis для распределенного кеширования

## 🚨 Troubleshooting

### Частые проблемы

1. **Ошибка подключения к БД**
   - Проверьте переменные окружения
   - Убедитесь в доступности PostgreSQL/Supabase

2. **Dashboard не загружается**
   - Проверьте доступность `/dashboard` endpoint
   - Убедитесь в правильности статических файлов

3. **API возвращает 500 ошибки**
   - Проверьте логи приложения
   - Убедитесь в инициализации всех компонентов

4. **Алерты не отправляются**
   - Проверьте настройки SMTP/Telegram
   - Убедитесь в правильности токенов

### Логи и отладка

```bash
# Просмотр логов
tail -f logs/app.log

# Проверка статуса системы
curl http://localhost:8000/status

# Проверка конфигурации
python -c "from core.database.enhanced_unified_service import enhanced_unified_db; print(enhanced_unified_db.health_check())"
```

## 📞 Поддержка

- **Документация API**: `/docs`
- **Dashboard**: `/dashboard`
- **Health Check**: `/v1/admin/health`
- **System Status**: `/v1/admin/status`

---

**🎉 Система готова к продакшену!**
