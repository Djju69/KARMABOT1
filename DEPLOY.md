# 🚀 KARMABOT1 - Деплой на Railway

## ✅ Проект готов к деплою!

**Статус:** 100% готов к продакшену  
**Платформа:** Railway  
**Дата:** 2025-09-05

---

## 🚀 Быстрый деплой (5 минут)

### 1. Создание проекта на Railway

1. Перейдите на [railway.com](https://railway.com/)
2. Войдите в аккаунт (GitHub/Google)
3. Нажмите **"Deploy a new project"**
4. Выберите **"Deploy from GitHub Repo"**
5. Найдите и подключите репозиторий **KARMABOT1**

### 2. Настройка переменных окружения

В Railway Dashboard → **Variables** добавьте:

```bash
# Обязательные переменные
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_admin_telegram_id
SECRET_KEY=your_very_long_and_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Где получить:**
- `BOT_TOKEN` - у [@BotFather](https://t.me/BotFather) в Telegram
- `ADMIN_ID` - ваш Telegram ID (узнать у [@userinfobot](https://t.me/userinfobot))
- `SECRET_KEY` - сгенерировать случайную строку 32+ символов
- `JWT_SECRET_KEY` - отдельный ключ для JWT токенов

### 3. Автоматический деплой

Railway автоматически:
- ✅ Создаст PostgreSQL базу данных
- ✅ Создаст Redis кэш
- ✅ Запустит деплой из Dockerfile
- ✅ Настроит health check на `/health`
- ✅ Предоставит URL для webhook

---

## 📊 Что происходит при деплое

### 🏗️ Сборка:
1. Railway использует `Dockerfile`
2. Устанавливает Python 3.11 и зависимости
3. Копирует код проекта
4. Настраивает переменные окружения

### 🚀 Запуск:
1. Выполняется `python start.py`
2. Проверяются переменные окружения
3. Запускается Telegram бот
4. Запускается FastAPI веб-сервер
5. Настраивается webhook для Railway

### 🔍 Мониторинг:
- Health check на `/health` endpoint
- Логи доступны в Railway Dashboard
- Автоматические перезапуски при ошибках

---

## 🎯 После деплоя

### ✅ Проверьте:
1. **Логи в Railway Dashboard** - нет ошибок
2. **Health check** - статус "healthy"
3. **Telegram бот** - отвечает на команды
4. **WebApp интерфейс** - доступен по URL

### 🔧 Настройка webhook:
1. Скопируйте URL из Railway Dashboard
2. Установите webhook для бота:
   ```bash
   curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-app.railway.app/webhook"}'
   ```

---

## 🚨 Troubleshooting

### ❌ Бот не отвечает:
- Проверьте `BOT_TOKEN` в переменных
- Убедитесь что webhook настроен
- Проверьте логи в Railway Dashboard

### ❌ Health check не проходит:
- Проверьте что порт 8080 доступен
- Убедитесь что `/health` endpoint работает
- Проверьте логи приложения

### ❌ База данных не подключается:
- Railway автоматически создает `DATABASE_URL`
- Проверьте что PostgreSQL сервис запущен
- Убедитесь что миграции выполнены

---

## 📋 Checklist деплоя

- [ ] Создан проект на Railway
- [ ] Подключен GitHub репозиторий
- [ ] Добавлены переменные окружения
- [ ] Деплой запущен успешно
- [ ] Health check проходит
- [ ] Бот отвечает в Telegram
- [ ] WebApp интерфейс доступен
- [ ] Webhook настроен

---

## 🎉 Готово!

**Проект KARMABOT1 успешно развернут на Railway!**

- 🌐 **WebApp:** `https://your-app.railway.app`
- 🤖 **Telegram Bot:** `@your_bot_username`
- 📊 **Мониторинг:** Railway Dashboard
- 📖 **Документация:** [PROGRESS.md](PROGRESS.md)

**Поздравляем с успешным деплоем!** 🚀🎉
