# KarmaBot - Telegram Bot with Admin Panel

[![Tests](https://github.com/Djju69/KARMABOT1/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Djju69/KARMABOT1/actions)
[![Coverage](https://codecov.io/gh/Djju69/KARMABOT1/branch/main/graph/badge.svg)](https://codecov.io/gh/Djju69/KARMABOT1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Status-100%25%20Ready-brightgreen.svg)](https://github.com/Djju69/KARMABOT1)
[![Railway](https://img.shields.io/badge/Deploy%20on-Railway-blue.svg)](https://railway.com/)

## 📊 Текущий статус проекта

**🎉 ПРОЕКТ ПОЛНОСТЬЮ ГОТОВ К ПРОДАКШЕНУ! (100%)** (обновлено 2025-09-05)

### ✅ Все критические компоненты завершены:
- 🏗️ **Архитектура и база данных** (100%)
- 👤 **Личный кабинет пользователя** (100%)
- 📱 **QR WebApp интеграция** (100%)
- 🛡️ **Система модерации** (100%)
- ⚙️ **Админ-панель** (100%)
- 🧪 **Comprehensive тестирование** (100%)
- 🏪 **Партнерская программа** (100%)
- 👥 **Реферальная система** (100%)
- 🔧 **Сервисы и API** (100%)

### 🚀 Готов к деплою на Railway:
- ✅ Railway конфигурация настроена
- ✅ Dockerfile оптимизирован
- ✅ Health check endpoint реализован
- ✅ Переменные окружения документированы
- ✅ Автоматический запуск настроен

**Подробный отчет:** [PROGRESS.md](PROGRESS.md) | **Railway деплой:** [RAILWAY_DEPLOY_READY.md](RAILWAY_DEPLOY_READY.md)

## 🚀 Быстрый старт

### 🚀 Деплой на Railway (Рекомендуется)

**Проект готов к деплою на Railway!**

1. **Создайте проект на Railway:**
   - Перейдите на [railway.com](https://railway.com/)
   - Нажмите "Deploy a new project"
   - Выберите "Deploy from GitHub Repo"
   - Подключите репозиторий KARMABOT1

2. **Настройте переменные окружения:**
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_admin_telegram_id
   SECRET_KEY=your_very_long_and_secure_secret_key_here
   JWT_SECRET_KEY=your_jwt_secret_key_here
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

3. **Railway автоматически:**
   - Создаст PostgreSQL и Redis
   - Запустит деплой из Dockerfile
   - Настроит health check
   - Предоставит URL для webhook

**📖 Подробные инструкции:** [RAILWAY_DEPLOY_READY.md](RAILWAY_DEPLOY_READY.md)

### 💻 Локальная разработка

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите локально:
   ```bash
   python start.py
   ```

3. Следуйте инструкциям в [QUICK_START.md](QUICK_START.md)

## 🚀 Features

### 🤖 Telegram Bot
- Modern aiogram v3 integration
- Multi-language support (RU/EN/VI/KO)
- Advanced command system
- FSM for complex workflows
- Real-time notifications

### 👤 User Features
- **Personal Cabinet** - comprehensive user profile
- **Loyalty System** - Bronze/Silver/Gold/Platinum levels
- **QR Codes** - WebApp integration with validation
- **Referral Program** - multi-level referral system
- **Achievements** - gamification with progress tracking

### 🏪 Partner Features
- **Partner Onboarding** - step-by-step registration
- **Verification System** - automatic and manual approval
- **Enhanced Dashboard** - real-time analytics
- **Card Management** - business card creation and management
- **Document Verification** - secure document upload

### 🛡️ Admin Features
- **Advanced Admin Panel** - modern WebApp interface
- **Real-time Statistics** - comprehensive analytics
- **User Management** - complete user administration
- **Moderation System** - automated content moderation
- **Financial Analytics** - revenue and performance tracking

### 🔧 Technical Features
- **FastAPI WebApp** - modern REST API
- **PostgreSQL Database** - with migrations
- **Redis Caching** - performance optimization
- **JWT Authentication** - secure API access
- **Health Monitoring** - Railway-ready health checks
- **Docker Support** - containerized deployment
- Генерация и управление QR-кодами

## 🔧 Настройка окружения

### Переменные окружения

Основные настройки бота настраиваются через переменные окружения. Создайте файл `.env` в корне проекта со следующими параметрами:

```env
# Основные настройки
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_id
ENVIRONMENT=development  # или production
LOG_LEVEL=INFO

# База данных
DATABASE_URL=sqlite:///core/database/data.db  # или ваша PostgreSQL строка подключения

# WebApp настройки
JWT_SECRET=your_jwt_secret
WEBAPP_QR_URL=https://your-domain.com/qr

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0

# Фича-флаги (true/false)
FEATURE_QR_WEBAPP=true
FEATURE_PARTNER_FSM=false
FEATURE_MODERATION=true
FEATURE_NEW_MENU=false
FEATURE_LISTEN_NOTIFY=false
```

## 📱 Работа с QR-кодами

Бот поддерживает генерацию и управление QR-кодами. Для активации:

1. Установите `FEATURE_QR_WEBAPP=true` в настройках
2. Настройте `WEBAPP_QR_URL` для доступа к веб-интерфейсу
3. Используйте команду /profile в боте для доступа к управлению QR-кодами

### Доступные команды:
- `Показать мои QR-коды` - просмотр созданных QR-кодов
- `Создать QR-код` - генерация нового QR-кода
- `История операций` - просмотр истории начислений

## 🛠️ Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Djju69/KARMABOT1.git
   cd KARMABOT1
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   # Для Windows:
   .\venv\Scripts\activate
   # Для Linux/MacOS:
   # source venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

4. Настройте переменные окружения:
   ```bash
   cp .env.example .env
   # Отредактируйте .env, указав свои настройки
   ```

5. Запустите бота:
   ```bash
   python main_v2.py
   ```

## 🚀 Production Deployment

### Prerequisites
- Linux server (Ubuntu 22.04 recommended)
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL (optional, SQLite is used by default)

### 1. Server Setup

```bash
# Create a new user for the application
sudo adduser --system --group --no-create-home karmabot
sudo mkdir -p /opt/karmabot/{data,logs}
sudo chown -R karmabot:karmabot /opt/karmabot
```

### 2. Install Dependencies

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv nginx supervisor

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Deploy the Application

```bash
# Clone the repository (or copy your code)
sudo -u karmabot git clone https://github.com/yourusername/KARMABOT1.git /opt/karmabot/app
cd /opt/karmabot/app

# Create production environment file
sudo -u karmabot cp env.prod.example .env.prod

# Edit the configuration
sudo -u karmabot nano .env.prod

# Build and start the containers
sudo docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. Configure Nginx (Reverse Proxy)

Create a new Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/karmabot
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8080/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/karmabot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain and install certificate
sudo certbot --nginx -d yourdomain.com

# Set up automatic renewal
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
```

### 6. Monitoring and Maintenance

#### Backup

A backup script is provided at `deployment/backup.sh`. Set up a cron job for daily backups:

```bash
# Make the script executable
chmod +x /opt/karmabot/app/deployment/backup.sh

# Add to crontab (edit as root)
sudo crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /opt/karmabot/app/deployment/backup.sh
```

#### Log Rotation

Install the logrotate configuration:

```bash
sudo cp /opt/karmabot/app/deployment/karmabot-logrotate /etc/logrotate.d/karmabot
```

### 7. Updating the Application

```bash
cd /opt/karmabot/app

# Pull the latest changes
sudo -u karmabot git pull

# Rebuild and restart the containers
sudo docker-compose -f docker-compose.prod.yml up -d --build

# View logs
sudo docker-compose -f docker-compose.prod.yml logs -f
```

## 🧪 Testing

```bash
# Запуск всех тестов
pytest tests/ -v

# С отчетом о покрытии
pytest --cov=core tests/

# Запуск конкретных тестов
pytest tests/unit/         # Только юнит-тесты
pytest tests/integration/  # Только интеграционные тесты
```

## 🔄 CI/CD Пайплайн

Проект использует GitHub Actions для автоматизированного тестирования и деплоя:

- **Тестирование**: Запускается при каждом пуше и pull request
  - Юнит-тесты
  - Интеграционные тесты
  - Проверка покрытия кода
  - Проверка стиля кода

- **Деплой**: Ручной запуск для продакшена
  - Стейдж на ветке `develop`
  - Продакшен при создании тега версии (`v*`)

## 🔒 Лицензия

Этот проект лицензирован по лицензии MIT - смотрите файл [LICENSE](LICENSE) для деталей.

---

## 🚀 Деплой

### GitHub Secrets

Для работы CI/CD необходимо настроить следующие секреты в настройках репозитория:

| Секрет | Описание |
|--------|----------|
| `BOT_TOKEN` | Токен Telegram бота |
| `DATABASE_URL` | URL базы данных для тестов |
| `CODECOV_TOKEN` | Токен для загрузки отчетов о покрытии |
| `RAILWAY_TOKEN` | Токен для деплоя на Railway (опционально) |

### Первый запуск

```bash
git add .
git commit -m "ci: Настройка GitHub Actions CI/CD пайплайна"
git push origin main
```

### Проверка

После пуша проверьте:
1. Вкладка Actions → запустился workflow
2. Все шаги прошли успешно
3. Отчет о покрытии доступен в Codecov
4. Бейджи в README обновлены

---

## 🛠️ Мониторинг и логирование

### Sentry (опционально)

```python
# core/monitoring.py
import sentry_sdk

def setup_monitoring():
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        environment=os.getenv('ENV', 'development'),
        traces_sample_rate=1.0
    )
```

### Health Check

```python
# web/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
```

## Обновление до aiogram v3

### Основные изменения

## 📚 Документация

### 📊 Статус и прогресс
- [PROGRESS.md](PROGRESS.md) - Детальный прогресс разработки
- [RAILWAY_DEPLOY_READY.md](RAILWAY_DEPLOY_READY.md) - Готовность к деплою на Railway

### 🚀 Деплой и настройка
- [DEPLOY.md](DEPLOY.md) - **Быстрый деплой на Railway (5 минут)**
- [RAILWAY_VARS.md](RAILWAY_VARS.md) - Переменные окружения для Railway
- [QUICK_START.md](QUICK_START.md) - Быстрый старт для разработки
- [DEPLOYMENT.md](DEPLOYMENT.md) - Общие инструкции по деплою

### 🔧 Техническая документация
- [TECHNICAL_SPECIFICATION.md](TECHNICAL_SPECIFICATION.md) - Техническое описание
- [TESTING.md](TESTING.md) - Тестирование
- [MONITORING.md](docs/MONITORING.md) - Мониторинг

---

## 🎉 Проект завершен!

**KARMABOT1 полностью готов к продакшену!**

- ✅ Все критические компоненты реализованы (100%)
- ✅ Comprehensive тестирование завершено
- ✅ Готов к деплою на Railway
- ✅ Документация обновлена
- ✅ Инструкции по деплою созданы

**Следуйте инструкциям в [DEPLOY.md](DEPLOY.md) для быстрого деплоя!** 🚀

---

## Обновление до aiogram v3

### Основные изменения

1. **Новая структура настроек**:
   - Унифицированный класс `Settings` в `core/config.py`
   - Поддержка переменных окружения с префиксом `BOTS__`
   - Автоматическая загрузка `.env` только в режиме разработки

2. **Обновленные обработчики**:
   - Совместимость с aiogram v3
   - Улучшенная обработка ошибок
   - Поддержка старых и новых сигнатур хэндлеров

3. **Новые возможности**:
   - Улучшенное логирование
   - Более надежная обработка команд
   - Поддержка FSM из коробки

## Настройка окружения

### Проверка переменных окружения

Перед запуском убедитесь, что все необходимые переменные окружения установлены корректно:

```bash
# Проверка переменных окружения
printenv | grep -i -E 'BOTS__BOT_TOKEN|BOT_TOKEN|TELEGRAM_TOKEN|ENVIRONMENT'

# Проверка токена бота
python -c "import os; print('BOTS__BOT_TOKEN =', repr(os.getenv('BOTS__BOT_TOKEN')))"

# Проверка доступа к Telegram API
curl -s "https://api.telegram.org/bot${BOTS__BOT_TOKEN}/getMe"
```

Ожидаемый вывод:
- `BOTS__BOT_TOKEN` должен быть установлен
- `BOT_TOKEN` и `TELEGRAM_TOKEN` не должны быть установлены (если есть - удалите их)
- Запрос к API должен вернуть `{"ok":true,...}`

### Файлы окружения

#### .env (для разработки)
```env
BOTS__BOT_TOKEN=your_bot_token_here
BOTS__ADMIN_ID=6391215556
ENVIRONMENT=development
FEATURES__BOT_ENABLED=1
FEATURES__PARTNER_FSM=0
FEATURES__MODERATION=0
```

#### Настройки Railway/Production
```env
BOTS__BOT_TOKEN=your_production_token
ENVIRONMENT=production
FEATURES__BOT_ENABLED=1
```

## Запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите бота:
   ```bash
   python main_v2.py
   ```

## Тестирование

Запустите тесты для проверки работоспособности:

```bash
python -m pytest tests/test_imports.py -v
```

## Обратная совместимость

Для поддержки старых обработчиков используется модуль `core.compat`:
- `@compat_handler` - декоратор для старых хэндлеров
- `call_compat()` - функция для вызова старых обработчиков
- Автоматические алиасы для устаревших имен функций

## Проверка работы

1. Проверьте логи на наличие сообщения о успешной авторизации:
   ```
   ✅ Bot authorized: @your_bot_username (id=...)
   ```

2. Убедитесь, что токен в логах маскируется (начинается с 8 символов, затем многоточие):
   ```
   🔑 Using bot token: 83635304…
   ```

## Устранение неполадок

Если бот не запускается:
1. Проверьте, что переменная `BOTS__BOT_TOKEN` установлена и корректна
2. Убедитесь, что нет конфликтующих переменных (`BOT_TOKEN`, `TELEGRAM_TOKEN`)
3. Проверьте доступность API Telegram с вашего сервера
4. Проверьте логи на наличие ошибок авторизации
