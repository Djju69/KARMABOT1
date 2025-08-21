# KARMABOT1 - Enhanced Telegram Bot

Система скидок и каталога заведений для Telegram с поддержкой партнерских карточек и модерации.

## 🚀 Быстрый старт

### 1. Клонирование и установка

```bash
git clone <repository-url>
cd KARMABOT1-fixed
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
# Скопируйте файл конфигурации
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

**Обязательные параметры:**
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id
```

### 3. Запуск

```bash
# Основной способ
python main_v2.py

# Или legacy версия (для совместимости)
python main.py
```

## 🔧 Конфигурация

### Переменные окружения (.env)

```env
# Основные настройки
BOT_TOKEN=1234567890:ABC...                 # Токен бота от BotFather
ADMIN_ID=123456789                          # Telegram ID администратора
DATABASE_URL=sqlite:///core/database/data.db # Путь к базе данных

# Фича-флаги (по умолчанию выключены для безопасности)
FEATURE_PARTNER_FSM=false                   # FSM для добавления карточек партнерами
FEATURE_MODERATION=false                    # Система модерации
FEATURE_NEW_MENU=false                      # Новое главное меню (3x2)
FEATURE_QR_WEBAPP=false                     # QR WebApp функциональность
FEATURE_LISTEN_NOTIFY=false                 # Уведомления через PUB/SUB

# Дополнительные настройки
LOG_LEVEL=INFO                              # Уровень логирования
ENVIRONMENT=development                     # Окружение (development/production)
```

### Поэтапное включение функций

**Фаза 1 - Базовая функциональность:**
```env
# Только основные функции (безопасно)
FEATURE_PARTNER_FSM=false
FEATURE_MODERATION=false
FEATURE_NEW_MENU=false
```

**Фаза 2 - Партнерские функции:**
```env
# Включаем FSM для партнеров
FEATURE_PARTNER_FSM=true
FEATURE_MODERATION=true
FEATURE_NEW_MENU=false
```

**Фаза 3 - Полная функциональность:**
```env
# Все функции включены
FEATURE_PARTNER_FSM=true
FEATURE_MODERATION=true
FEATURE_NEW_MENU=true
```

## 📋 Функциональность

### Для пользователей
- 🗂️ **Категории** - просмотр заведений по типам
- 📍 **Поиск рядом** - геолокационный поиск
- 🌆 **По районам** - выбор по местоположению
- 🌐 **Мультиязычность** - RU/EN/VI/KO
- 📱 **QR-коды** - получение скидок

### Для партнеров (при включенном FEATURE_PARTNER_FSM)
- ➕ **Добавление карточек** - пошаговый FSM процесс
- 📋 **Управление карточками** - просмотр статусов
- 👤 **Личный кабинет** - статистика и настройки
- ⏳ **Отслеживание модерации** - уведомления о статусе

### Для администраторов (при включенном FEATURE_MODERATION)
- 🔍 **Модерация карточек** - approve/reject workflow
- 📊 **Статистика** - аналитика по модерации
- ⭐ **Рекомендуемые** - выделение лучших карточек
- 🗂️ **Архивация** - управление неактивными карточками

## 🗄️ База данных

### Автоматические миграции

База данных инициализируется автоматически при первом запуске:

```python
# Проверка готовности БД
from core.database.migrations import ensure_database_ready
ensure_database_ready()
```

### Структура таблиц

**Основные таблицы:**
- `categories_v2` - категории заведений
- `partners_v2` - партнеры (владельцы бизнеса)
- `cards_v2` - карточки заведений
- `qr_codes_v2` - QR-коды для скидок
- `moderation_log` - журнал модерации

**Legacy таблицы (для совместимости):**
- `categories` - старые категории
- `restaurants` - старые рестораны
- `services` - старые услуги

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Только контракт-тесты
pytest tests/test_contracts.py

# С подробным выводом
pytest -v

# Конкретные группы тестов
pytest -m "core or api or bot"
```

### Контракт-тесты

Обязательные тесты перед каждым деплоем:

```bash
# Проверка callback паттернов
pytest tests/test_contracts.py::TestCallbackContracts

# Проверка i18n ключей
pytest tests/test_contracts.py::TestI18nContracts

# Проверка БД схемы
pytest tests/test_contracts.py::TestDatabaseContracts
```

## 🔄 Миграция с оригинального кода

### Backward Compatibility

Новая версия полностью совместима с оригинальным кодом:

1. **Сохранены все callback паттерны**
2. **Все i18n ключи работают**
3. **Legacy хендлеры не изменены**
4. **Старая БД поддерживается**

### Пошаговая миграция

**Шаг 1:** Замените файлы, но оставьте фича-флаги выключенными
```env
FEATURE_PARTNER_FSM=false
FEATURE_MODERATION=false
FEATURE_NEW_MENU=false
```

**Шаг 2:** Протестируйте основную функциональность

**Шаг 3:** Постепенно включайте новые функции

**Шаг 4:** Удалите старые файлы после полного перехода

## 🚨 Безопасность

### Критически важно

1. **Никогда не коммитьте .env файл**
2. **Ротируйте токены при компрометации**
3. **Используйте HTTPS для вебхуков**
4. **Ограничьте доступ к БД**

### Удаление секретов из истории Git

Если секреты попали в репозиторий:

```bash
# Установите git-filter-repo
pip install git-filter-repo

# Удалите файлы с секретами из истории
git filter-repo --path input --invert-paths
git filter-repo --path mythic-brook-414011-6b6b807faea2.json --invert-paths

# Форсированно обновите remote
git push origin --force --all
```

## 📊 Мониторинг

### Логирование

```python
# Настройка уровня логов
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Команды администратора

```
/moderate - начать модерацию карточек
/mod_stats - статистика модерации
/help - справка по командам
```

### Команды партнеров

```
/add_card - добавить новую карточку
/my_cards - просмотр своих карточек
/start - главное меню
```

## 🔧 Разработка

### Архитектурные принципы

1. **Non-Breaking Changes** - никаких breaking изменений
2. **Feature Flags** - новые функции за флагами
3. **Backward Compatibility** - поддержка legacy кода
4. **Database Migrations** - безопасные миграции БД

### Добавление новых функций

1. Создайте фича-флаг в `settings.py`
2. Добавьте новый код за условием флага
3. Напишите контракт-тесты
4. Обновите документацию

### Структура проекта

```
KARMABOT1-fixed/
├── core/
│   ├── database/          # БД и миграции
│   ├── handlers/          # Обработчики сообщений
│   ├── keyboards/         # Клавиатуры
│   ├── services/          # Бизнес-логика
│   └── utils/             # Утилиты
├── templates/             # Шаблоны сообщений
├── tests/                 # Тесты
├── main_v2.py            # Новая точка входа
├── main.py               # Legacy точка входа
└── .env.example          # Пример конфигурации
```

## 🆘 Устранение неполадок

### Частые проблемы

**Ошибка "BOT_TOKEN is required":**
```bash
# Проверьте .env файл
cat .env | grep BOT_TOKEN

# Убедитесь, что файл в корне проекта
ls -la .env
```

**База данных не инициализируется:**
```bash
# Проверьте права доступа
ls -la core/database/

# Удалите БД и пересоздайте
rm core/database/data.db
python main_v2.py
```

**Фича-флаги не работают:**
```bash
# Проверьте синтаксис в .env
# Используйте true/false, не True/False
FEATURE_PARTNER_FSM=true
```

### Логи и отладка

```python
# Включите подробные логи
LOG_LEVEL=DEBUG

# Проверьте логи запуска
python main_v2.py 2>&1 | grep "Feature flags"
```

## 📞 Поддержка

- **Issues:** Создавайте issue в репозитории
- **Документация:** Читайте комментарии в коде
- **Тесты:** Запускайте тесты перед изменениями

## 📄 Лицензия

Проект использует лицензию оригинального KARMABOT1.

---

**Версия:** 2.0.0  
**Дата:** 2025-08-21  
**Совместимость:** Python 3.8+, aiogram 3.3.0+
