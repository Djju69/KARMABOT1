# 📊 Система мониторинга KarmaBot

## 🚀 Быстрый старт

1. **Добавьте переменные окружения:**
```bash
# .env
SENTRY_DSN=https://your_actual_dsn.ingest.sentry.io/your_project
ENVIRONMENT=production
APP_VERSION=1.0.0
LOG_LEVEL=INFO
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите приложение:
```bash
uvicorn web.main:app --host 0.0.0.0 --port 8080
```

## 📋 Эндпоинты мониторинга

### Health Check
```
GET /api/health
```
Проверка работоспособности приложения

### Тестовые эндпоинты
```
GET /api/test/error      # Тест ошибок
GET /api/test/metrics    # Тест метрик
GET /api/test/logs       # Тест логирования
```

## 🔧 Настройка Sentry
1. Создайте проект в [Sentry.io](https://sentry.io)
2. Получите DSN из настроек проекта
3. Добавьте DSN в переменные окружения

## 📊 Ключевые метрики
- `bot.messages_processed` - обработанные сообщения
- `bot.errors_total` - общее количество ошибок
- `response_time_ms` - время ответа API
- `database.query_duration` - время запросов к БД

## 🚨 Аларты и уведомления
Настройте в Sentry Dashboard:
- Критические ошибки → Slack/Email
- Проблемы с производительностью → Slack
- Доступность сервиса → PagerDuty

## 🐳 Docker развертывание

```bash
# Сборка образа
docker build -t karmabot .

# Запуск контейнера
docker run -d --name karmabot \
  -p 8080:8080 \
  --env-file .env \
  karmabot
```

## 🔍 Проверка работы

1. Проверка health check:
```bash
curl http://localhost:8080/api/health
```

2. Тест ошибок (должна появиться в Sentry):
```bash
curl http://localhost:8080/api/test/error
```

3. Проверка метрик:
```bash
curl http://localhost:8080/api/test/metrics
```

## 🛠️ Устранение неполадок

1. **Ошибки Sentry**
   - Проверьте DSN в настройках
   - Убедитесь, что приложение имеет доступ в интернет
   - Проверьте логи приложения

2. **Проблемы с метриками**
   - Убедитесь, что Sentry SDK инициализирован
   - Проверьте правильность имен метрик
   - Проверьте настройки сэмплирования

## 📈 Оптимизация производительности

1. **Настройка сэмплинга**
   ```python
   # В core/config/monitoring.py
   class SentrySettings:
       traces_sample_rate = 0.2  # 20% трафика
       profiles_sample_rate = 0.1  # 10% профилирований
   ```

2. **Фильтрация событий**
   ```python
   # В core/monitoring.py
   def before_send(event, hint):
       if 'exc_info' in hint:
           exc_type, exc_value, tb = hint['exc_info']
           if isinstance(exc_value, SomeExpectedException):
               return None  # Игнорируем ожидаемые исключения
       return event
   ```
