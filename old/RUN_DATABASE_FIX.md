# Инструкция по исправлению базы данных

## Для выполнения исправлений базы данных:

### Вариант 1: Через psql (PostgreSQL)
```bash
psql -U your_username -d your_database_name -f fix_database.sql
```

### Вариант 2: Через pgAdmin
1. Откройте pgAdmin
2. Подключитесь к вашей базе данных
3. Откройте Query Tool
4. Скопируйте содержимое `fix_database.sql`
5. Выполните запрос

### Вариант 3: Через DBeaver или другой SQL клиент
1. Подключитесь к базе данных
2. Откройте SQL редактор
3. Скопируйте содержимое `fix_database.sql`
4. Выполните скрипт

### Вариант 4: Через Python скрипт
```python
import asyncpg
import asyncio

async def run_fix():
    conn = await asyncpg.connect('postgresql://user:password@localhost/dbname')
    
    with open('fix_database.sql', 'r') as f:
        sql = f.read()
    
    await conn.execute(sql)
    await conn.close()
    print("Database fixes applied successfully!")

asyncio.run(run_fix())
```

## Что делает скрипт:
1. Исправляет дублирование колонки `karma_points`
2. Создает таблицу `cards_generated` для хранения сгенерированных карт
3. Создает необходимые индексы для производительности
4. Добавляет недостающие колонки в таблицу `users`
5. Создает таблицы `favorites` и `karma_log`

После выполнения скрипта перезапустите бота.
