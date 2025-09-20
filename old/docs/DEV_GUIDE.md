# 👨‍💻 Руководство разработчика KARMABOT1

## 🏗️ Архитектура системы

### Компоненты:
- **Telegram Bot** - основной интерфейс (aiogram 3.x)
- **WebApp** - веб-интерфейс для QR-кодов
- **Database** - PostgreSQL/SQLite для данных
- **Redis** - leader election для polling
- **Odoo Integration** - CRM система (опционально)

### Структура проекта:
```
core/
├── handlers/          # Обработчики команд и сообщений
│   ├── main_menu_router.py
│   ├── cabinet_router.py
│   ├── partner.py
│   ├── admin_cabinet.py
│   └── category_handlers_v2.py
├── keyboards/          # Клавиатуры
│   ├── reply_v2.py    # Reply клавиатуры
│   └── inline_v2.py   # Inline клавиатуры
├── services/           # Бизнес-логика
│   ├── profile.py
│   ├── admins_service.py
│   ├── loyalty_service.py
│   └── odoo_api.py
├── database/           # Работа с БД
│   ├── db_v2.py
│   └── migrations.py
├── utils/              # Утилиты
│   ├── locales_v2.py  # Локализация
│   └── helpers.py
└── settings.py         # Настройки и фича-флаги
```

## 🚫 Non-Breaking Dev Guide

### Жёсткие ограничения:
- ❌ НЕ создавать новые файлы/папки/миграции
- ❌ НЕ удалять i18n ключи
- ❌ НЕ менять названия/иконки кнопок
- ❌ НЕ менять архитектуру проекта
- ❌ НЕ использовать Inline для навигации

### Разрешённые изменения:
- ✅ Рефакторинг внутренней логики
- ✅ Исправление багов
- ✅ Добавление новых i18n ключей
- ✅ Использование фича-флагов
- ✅ Inline только для карточек/подтверждений

## 🎛️ Фича-флаги

### Настройка в `.env`:
```env
FEATURE_PARTNER_FSM=true          # FSM для партнёров
FEATURE_MODERATION=true           # Система модерации
FEATURE_VERBOSE_ADMIN_BACK=false # Подробные кнопки "Назад"
FEATURE_MENU_V2=false            # Новое главное меню
FEATURE_QR_WEBAPP=false          # WebApp для QR
```

### Использование в коде:
```python
from core.settings import settings

if settings.features.partner_fsm:
    # Новая функциональность
    pass
else:
    # Старая функциональность
    pass
```

## 🌐 Система локализации (i18n)

### Структура:
- `locales/ru.json` - русский (эталонный)
- `locales/en.json` - английский
- `locales/deprecated.json` - устаревшие ключи
- `core/utils/locales_v2.py` - расширенные переводы

### Неймспейсы:
- `common.*` - общие элементы
- `keyboard.*` - кнопки клавиатур
- `menu.*` - навигация по меню
- `partner.*` - партнёрские функции
- `admin.*` - админские функции
- `user.*` - пользовательские функции
- `errors.*` - сообщения об ошибках
- `messages.*` - информационные сообщения

### Добавление новых ключей:
```python
# 1. Добавить в JSON файлы
# locales/ru.json
{
  "new_key": "Новый текст"
}

# 2. Использовать в коде
from core.utils.locales_v2 import get_text
text = get_text('new_key', lang='ru')
```

### Система алиасов:
```python
ALIASES = {
    "old_key": "new_key"  # Обратная совместимость
}
```

## 🗄️ Работа с базой данных

### Основные таблицы:
- `users` - пользователи
- `partners_v2` - партнёры
- `cards_v2` - карточки заведений
- `card_photos` - фотографии карточек
- `user_roles` - роли пользователей
- `karma_transactions` - транзакции баллов
- `cards_generated` - сгенерированные QR-коды

### Миграции:
```python
# Создание миграции
python -m core.database.migrations

# Проверка миграций
python -m core.database.migrations --check
```

### Работа с данными:
```python
from core.database import db_v2

# Получение пользователя
user = db_v2.get_or_create_user(user_id, username)

# Создание карточки
card_id = db_v2.create_card(partner_id, data)

# Обновление статуса
db_v2.update_card_status(card_id, 'published')
```

## 🔧 Разработка новых функций

### 1. Планирование:
- Определить необходимость фича-флага
- Спроектировать без изменения UI
- Учесть обратную совместимость

### 2. Реализация:
```python
# Добавить фича-флаг в settings.py
class Features:
    new_feature: bool = field(default=False)

# Использовать в коде
if settings.features.new_feature:
    # Новая логика
    pass
else:
    # Старая логика
    pass
```

### 3. Тестирование:
```bash
# Запуск тестов
python -m pytest tests/

# Проверка i18n
python tests/test_i18n_consistency.py

# Проверка миграций
python -m core.database.migrations --check
```

## 🧪 Тестирование

### Структура тестов:
```
tests/
├── test_i18n_consistency.py  # Тесты локализации
├── test_database.py          # Тесты БД
├── test_handlers.py          # Тесты обработчиков
└── test_services.py          # Тесты сервисов
```

### Запуск тестов:
```bash
# Все тесты
python -m pytest

# Конкретный тест
python -m pytest tests/test_i18n_consistency.py

# С покрытием
python -m pytest --cov=core
```

### Тестирование i18n:
```python
def test_i18n_consistency():
    """Проверка консистентности локализации"""
    # Проверяет одинаковый набор ключей
    # Отсутствие дубликатов
    # Корректность JSON
```

## 🚀 Деплой

### Railway (рекомендуется):
```bash
# Установка CLI
npm install -g @railway/cli

# Авторизация
railway login

# Деплой
railway up

# Настройка переменных
railway variables set BOT_TOKEN=your_token
```

### Переменные окружения:
```env
# Обязательные
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
DATABASE_URL=postgresql://...

# Опциональные
REDIS_URL=redis://...
ODOO_BASE_URL=https://...
FEATURE_*=true/false
```

### Мониторинг:
```bash
# Логи
railway logs

# Статус
railway status

# Переменные
railway variables
```

## 🔍 Отладка

### Логирование:
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Информационное сообщение")
logger.error("Ошибка", exc_info=True)
```

### Отладка БД:
```python
# Проверка подключения
from core.database import db_v2
print(db_v2.get_stats())

# Проверка миграций
python -m core.database.migrations --check
```

### Отладка Redis:
```python
import redis
r = redis.from_url(os.environ.get('REDIS_URL'))
print(r.ping())
```

## 📝 Соглашения по коду

### Именование:
- Функции: `snake_case`
- Классы: `PascalCase`
- Константы: `UPPER_CASE`
- i18n ключи: `snake_case` с неймспейсами

### Структура файлов:
- Импорты в начале
- Константы после импортов
- Функции и классы
- Точка входа в конце

### Документация:
- Docstrings для всех функций
- Комментарии для сложной логики
- Типизация (Type hints)

## 🚨 Частые ошибки

### 1. Изменение UI без согласования:
```python
# ❌ Неправильно
button_text = "Новый текст"

# ✅ Правильно
button_text = get_text("existing_key", lang)
```

### 2. Удаление i18n ключей:
```python
# ❌ Неправильно
del translations["old_key"]

# ✅ Правильно
# Переместить в deprecated.json
# Добавить алиас
```

### 3. Создание новых файлов:
```python
# ❌ Неправильно
# Создание нового модуля

# ✅ Правильно
# Расширение существующего модуля
```

## 📞 Поддержка

### При возникновении проблем:
1. Проверьте логи: `railway logs`
2. Проверьте переменные: `railway variables`
3. Проверьте тесты: `python -m pytest`
4. Обратитесь к документации

### Полезные команды:
```bash
# Проверка статуса
railway status

# Перезапуск
railway restart

# Подключение к контейнеру
railway run bash

# Проверка БД
railway run python -c "from core.database import db_v2; print(db_v2.get_stats())"
```

