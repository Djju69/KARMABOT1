# KarmaBot - Telegram Bot with Admin Panel

[![Tests](https://github.com/Djju69/KARMABOT1/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Djju69/KARMABOT1/actions)
[![Coverage](https://codecov.io/gh/Djju69/KARMABOT1/branch/main/graph/badge.svg)](https://codecov.io/gh/Djju69/KARMABOT1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

## 🚀 Быстрый старт

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите деплой:
   ```powershell
   .\deploy.ps1
   ```

3. Следуйте инструкциям в [QUICK_START.md](QUICK_START.md)

## 🚀 Features
- Advanced Admin Panel
- Real-time Moderation Queue  
- Automated Reports
- CI/CD with GitHub Actions
- Modern aiogram v3 integration
- PostgreSQL database support

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
