# 🤖 KARMABOT1 - Система лояльности

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?template=https://github.com/your-username/KARMABOT1-fixed)

> Комплексная система лояльности на базе Telegram бота с WebApp кабинетами, системой баллов и партнерской программой.

## ✨ Основные возможности

### 👥 Для пользователей
- 💎 **Система баллов лояльности** с Welcome бонусом 167 баллов
- 🏪 **Каталог заведений** с QR-кодами и скидками
- 💳 **Привязка карт** и виртуальные карты
- 🌐 **WebApp кабинеты** для удобного управления
- 🌍 **Многоязычность** (RU, EN, VI, KO)

### 🤝 Для партнеров
- 📊 **Управление картами** заведений
- 📈 **Статистика продаж** и аналитика
- 🎯 **QR-коды** для скидок
- 💼 **Тарифные планы** (FREE, BUSINESS, ENTERPRISE)

### 👑 Для администраторов
- 🔍 **Модерация партнеров** и заявок
- 📊 **Расширенная аналитика** пользователей и транзакций
- ⚙️ **Настройки лояльности** и тарифов
- 🚨 **Системные алерты** и уведомления

## 🚀 Быстрый старт

### 1. Клонирование
```bash
git clone https://github.com/your-username/KARMABOT1-fixed.git
cd KARMABOT1-fixed
```

### 2. Настройка окружения
```bash
cp .env.example .env
# Заполните переменные в .env
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Запуск
```bash
python main_v2.py
```

## 🔧 Настройка

### Обязательные переменные
```bash
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your_secret_key
```

### Опциональные переменные
```bash
REDIS_URL=redis://localhost:6379
WEBAPP_BASE_URL=https://your-domain.com/webapp
APPLY_MIGRATIONS=1
APP_ENV=production
```

## 📱 Команды бота

### Основные команды
- `/start` - Начало работы
- `/help` - Справка
- `/profile` - Личный кабинет
- `/catalog` - Каталог заведений

### Админские команды
- `/admin` - Админский кабинет
- `/analytics` - Аналитика
- `/perf_stats` - Статистика производительности
- `/alerts` - Системные алерты

## 🌐 WebApp кабинеты

- **Пользовательский:** `/webapp/user-cabinet.html`
- **Партнерский:** `/webapp/partner-cabinet.html`
- **Админский:** `/webapp/admin-cabinet.html`

## 🧪 Тестирование

```bash
# Комплексное тестирование
python test_system_comprehensive.py

# Тестирование критических функций
python test_critical_functions.py

# Тестирование интеграций
python test_integrations.py
```

## 📊 Архитектура

```
Telegram Bot ←→ WebApp UI ←→ PostgreSQL
     ↓              ↓            ↓
  Services ←→ Analytics ←→ Notifications
```

## 🛠️ Технологии

- **Backend:** Python 3.11, aiogram 3.x
- **Database:** PostgreSQL, SQLite (dev)
- **Cache:** Redis, Memory fallback
- **Frontend:** HTML5, CSS3, JavaScript
- **Deploy:** Railway, Docker

## 📚 Документация

- 📖 [Полная документация](FINAL_DOCUMENTATION.md)
- 🚀 [Руководство по развертыванию](DEPLOYMENT_GUIDE.md)
- 🧪 [Тестирование](test_*.py)

## 🔄 Развертывание

### Railway (рекомендуется)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?template=https://github.com/your-username/KARMABOT1-fixed)

### Docker
```bash
docker build -t karmabot1 .
docker run -p 8080:8080 karmabot1
```

## 📈 Производительность

- ⚡ **Кэширование** запросов (Redis/Memory)
- 🗄️ **Пул соединений** PostgreSQL
- 📊 **Мониторинг** производительности
- 🔧 **Автоматическая оптимизация**

## 🌍 Многоязычность

Поддерживаемые языки:
- 🇷🇺 Русский (по умолчанию)
- 🇺🇸 Английский
- 🇻🇳 Вьетнамский
- 🇰🇷 Корейский

## 🔐 Безопасность

- 🔑 **Подписанные URL** для WebApp
- 🛡️ **Валидация** всех входных данных
- 🔒 **SSL/TLS** подключения
- 🚫 **Rate limiting** для API

## 📞 Поддержка

- 📧 **Issues:** GitHub Issues
- 📖 **Документация:** FINAL_DOCUMENTATION.md
- 🧪 **Тесты:** test_*.py
- 📊 **Мониторинг:** Railway Dashboard

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## 🤝 Вклад в проект

1. Fork репозиторий
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request

## 🎯 Roadmap

- [ ] Мобильное приложение
- [ ] Интеграция с платежными системами
- [ ] Машинное обучение для рекомендаций
- [ ] Расширенная аналитика
- [ ] API для внешних интеграций

---

## 🎉 Статус проекта

![Status](https://img.shields.io/badge/status-production%20ready-green)
![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**KARMABOT1** - это полнофункциональная система лояльности, готовая к продакшену! 🚀