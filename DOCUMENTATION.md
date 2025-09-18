# KarmaSystemBot - Документация

## 🧪 Тестирование

### Запуск тестов локально

1. Установите зависимости:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

2. Настройте тестовую базу данных PostgreSQL

3. Запустите тесты:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/test_db TESTING=1 pytest tests/ -v
```

### Структура тестов

- `tests/integration/` - интеграционные тесты
  - `test_admin_*.py` - тесты админ-панели
  - `test_handlers.py` - тесты обработчиков
- `tests/unit/` - юнит-тесты

### Добавление новых тестов

1. Создайте тестовый класс, унаследованный от `BaseBotTest`
2. Используйте `AsyncMock` для мокирования асинхронных вызовов
3. Проверяйте как успешные сценарии, так и обработку ошибок

## 🚀 Деплой

### Переменные окружения

Создайте файл `.env` со следующими переменными:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=12345,67890
```

### Staging

1. Настройте подключение к базе данных
2. Запустите миграции:
```bash
python -m alembic upgrade head
```
3. Запустите бота:
```bash
python main_v2.py
```

### Production

1. Создайте тег релиза:
```bash
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

2. Запустите деплой (пример для Railway):
```bash
railway up --service bot
```

## 🔧 Troubleshooting

### Частые проблемы

1. **Ошибки подключения к БД**
   - Проверьте строку подключения
   - Убедитесь, что БД доступна

2. **Проблемы с правами доступа**
   - Проверьте `ADMIN_IDS`
   - Убедитесь, что пользователь добавлен в админы

### Логи

Логи хранятся в `logs/bot.log`

### Откат

1. Откатитесь к предыдущему тегу:
```bash
git checkout v0.9.0
```
2. Перезапустите сервис

## 📊 Мониторинг

### Метрики

- Доступность сервиса
- Время ответа
- Количество ошибок
- Использование ресурсов

### Alerting

- Ошибки 5xx
- Response time > 1000ms
- Memory usage > 80%

## 📚 Пользовательские сценарии и фильтрация (v4.2.5)

### Первый запуск
- `/start` → inline‑выбор языка (RU/EN/VI/KO)
- Сохранение языка в профиле
- Показ политики: inline‑кнопки «✅ Принять» / «❌ Отклонить» / «📜 Политика»
- После «Принять» показывается главное меню

### Главное меню (ReplyKeyboard)
- Ряд 1: `🗂️ Категории` · `👥 Пригласить друзей`
- Ряд 2: `⭐ Избранные` · `❓ Помощь`
- Ряд 3: `👤 Личный кабинет`

### Категории (ReplyKeyboard, 6 кнопок)
- `🍽 restaurants` · `🧖‍♀ spa` · `🚗 transport` · `🏨 hotels` · `🚶‍♂ tours` · `🛍️ shops`
- Обработчики: `core/handlers/main_menu_router.py` и `core/handlers/category_handlers_v2.py`

### Рестораны — фильтрация (Inline)
- После выбора `🍽 restaurants` показывается сообщение «Выберите кухню:» и inline‑клавиатура:
  - `🥢 Азиатская` → `filt:restaurants:asia`
  - `🍝 Европейская` → `filt:restaurants:europe`
  - `🌭 Стрит‑фуд` → `filt:restaurants:street`
  - `🥗 Вегетарианская` → `filt:restaurants:vege`
  - `🔎 Показать все` → `filt:restaurants:all`
- По фильтру запускается единый рендер карточек `show_catalog_page(...)`

### Подкатегории (Reply)
- Транспорт: `🏍️ Байки` · `🚘 Машины` · `🚲 Велосипеды` · `◀️ Назад`
- Экскурсии: `👥 Групповые` · `🧑‍🤝‍🧑 Индивидуальные` · `◀️ Назад`
- SPA: `Салоны` · `Массаж` · `Сауна` · `◀️ Назад`
- Отели: `Отели` · `Апартаменты` · `◀️ Назад`

### Пагинация
- Формат callback: `pg:<slug>:<sub_slug>:<page>`
- Обработчик: `on_catalog_pagination` в `category_handlers_v2.py`
- Состояние FSM сохраняет: `{ category, sub_slug, page }`

### Единый рендер карточек
- Вызов: `show_cards(user_id, category, sub_slug=None, page=1)` → внутри вызывает `show_catalog_page`
- Источник данных: `db_v2.get_cards_by_category(...)`

### Логи и аудит
- Все ключевые действия логируются (открытие категорий, фильтры, пагинация)
- Принятие политики и выбор языка фиксируются
