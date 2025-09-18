# Тестирование KarmaBot

Этот каталог содержит модульные и интеграционные тесты для KarmaBot.

## Структура тестов

```
tests/
├── conftest.py          # Общие фикстуры и настройки
├── unit/                # Модульные тесты
│   └── handlers/        # Тесты обработчиков
└── integration/         # Интеграционные тесты
```

## Запуск тестов

### Установка зависимостей

```bash
pip install -r requirements-dev.txt
```

### Запуск всех тестов

```bash
pytest
```

### Запуск с покрытием кода

```bash
pytest --cov=core --cov-report=term-missing
```

### Запуск конкретного теста

```bash
pytest tests/unit/handlers/test_admin_queue_delete_isolated.py -v
```

## Настройка pre-commit

Для автоматической проверки кода перед коммитом:

```bash
pre-commit install
```

## Рекомендации по написанию тестов

1. **Именование тестов**:
   - Файлы: `test_<module>_<feature>.py`
   - Классы: `Test<FeatureName>`
   - Методы: `test_<scenario>_<expected_behavior>`

2. **Фикстуры**:
   - Используйте фикстуры из `conftest.py`
   - Создавайте локальные фикстуры для специфичных тестов

3. Асинхронные тесты:
   - Используйте `@pytest.mark.asyncio` для асинхронных тестов
   - Используйте `AsyncMock` для моков асинхронных функций

4. Моки:
   - Изолируйте тесты с помощью моков
   - Проверяйте вызовы моков с помощью `assert_called_with()`

## Отладка тестов

Для отладки тестов можно использовать:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Или запустить тест с флагом `-s` для вывода print'ов:

```bash
pytest tests/unit/handlers/test_example.py -v -s
```
