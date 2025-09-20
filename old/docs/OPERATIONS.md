# Операции: одиночный режим поллинга, очистка Redis-лока и миграция на вебхуки

## 1) Одиночный режим (рекомендуется сейчас)
Используйте один инстанс бота, отключите лидер-лок и включите поллинг:

- ENABLE_POLLING_LEADER_LOCK=0
- DISABLE_POLLING=0
- PREEMPT_LEADER=0

Перезапустите процесс бота после изменения переменных.

Дополнительно (разово): очистите старый ключ лока в Redis, см. раздел 2.

## 2) Разовая очистка ключа в Redis
Ключ: `production:bot:polling:leader`

Выберите удобный способ:

- Через redis-cli:
```bash
redis-cli -u redis://<host>:<port> -n <db> AUTH <password>
DEL production:bot:polling:leader
```
Примеры без AUTH/DB:
```bash
redis-cli -h 127.0.0.1 -p 6379 DEL production:bot:polling:leader
```

- Через docker (если Redis в контейнере):
```bash
docker exec -it <redis-container> redis-cli DEL production:bot:polling:leader
```

- Через Python (redis-py):
```python
import asyncio
from redis.asyncio import Redis

async def main():
    r = Redis.from_url("redis://<host>:<port>/<db>", password=None)
    await r.delete("production:bot:polling:leader")
    await r.aclose()

asyncio.run(main())
```

После удаления ключа перезапустите единственный инстанс бота.

## 3) Переключение на вебхуки (позже, когда будет домен/HTTPS)
Вебхуки убирают необходимость в поллинге: Telegram сам шлёт апдейты на ваш HTTPS URL.

### Требования
- Валидный домен с HTTPS (TLS).
- Публичный доступ к вашему FastAPI.

### Шаги
1. Убедитесь, что в веб-приложении есть обработчик вебхука. Рекомендуемый путь: `/bot/webhook`.
   - Если нет — добавить FastAPI-роут:
   ```python
   from fastapi import APIRouter, Request
   webhook_router = APIRouter()

   @webhook_router.post("/bot/webhook")
   async def telegram_webhook(req: Request):
       update = await req.json()
       # передать update в диспетчер aiogram
       # await dp.feed_webhook_update(update)
       return {"ok": True}
   ```
   Примечание: конкретная интеграция зависит от вашей версии aiogram и структуры `main_v2.py`.

2. Настроить переменные окружения:
   - DISABLE_POLLING=1
   - WEBHOOK_URL=https://<your-domain>/bot/webhook

3. Зарегистрировать вебхук у Telegram (один из вариантов):
   - Через curl:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -d url="https://<your-domain>/bot/webhook"
   ```
   - Или скриптом на Python (requests):
   ```python
   import requests
   BOT_TOKEN = "<YOUR_BOT_TOKEN>"
   WEBHOOK_URL = "https://<your-domain>/bot/webhook"
   r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", data={"url": WEBHOOK_URL})
   print(r.status_code, r.text)
   ```

4. Проверить доставку: логи FastAPI должны получать апдейты, бот отвечает.

### Откат на поллинг
- Удалить/отключить вебхук:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```
- Вернуть поллинг:
  - DISABLE_POLLING=0
  - ENABLE_POLLING_LEADER_LOCK=0 (одиночный режим) или 1 (если планируете много инстансов)

## 4) FAQ
- Почему бот иногда уходит в idle? — Когда включён лидер-лок и ключ в Redis уже занят другим инстансом.
- Что делать, если случайно запущены 2 копии? — Остановить лишнюю. В одиночном режиме держите 1 процесс и держите `ENABLE_POLLING_LEADER_LOCK=0`.
- Нужно ли чистить ключ в Redis каждый раз? — Нет. Только если ключ остался от старого лидера и мешает.

## 5) Регрессия: партнёрский кабинет (i18n-кнопки и карточки после модерации)

Краткий чек-лист для проверки кнопок партнёра и отображения карточек после модерации.

1. Общие условия
   - Убедиться, что включён флаг `FEATURE_PARTNER_FSM` (`settings.features.partner_fsm = True`).
   - Политика принята (иначе сначала принять в приветствии).

2. Кнопки партнёра (Reply)
   - Открыть «👤 Личный кабинет» из главного меню.
   - Нажать «➕ Добавить карточку» — должен стартовать мастер создания карточки (шаг выбора города).
   - Нажать «📋 Мои карточки» — должен открыться список карточек с пагинацией.
   - Повторить для локалей ru/en/vi/ko (кнопочные тексты берутся из translations, обработчики не зависят от эмодзи).

3. Отправка и модерация
   - Создать карточку и «Отправить на модерацию».
   - В админке (/moderate) одобрить карточку — статус изменяется на `published`.

4. Отображение карточек у партнёра
   - Открыть «Мои карточки»: должна отображаться карточка со статусом `published`.
   - Пагинация: кнопки «⬅️ Назад / Вперёд ➡️ / 🔄 Обновить» работают, список обновляется.
   - Просмотр карточки («🔎 …»): доступны действия «👁️ Показать/Скрыть» (`published` ↔ `archived`) и «🗑 Удалить».

5. Диагностика
   - Если «Мои карточки» ничего не показывает: проверить, что статус карточки `approved` или `published` (фильтр отображения именно по этим статусам).
   - Если нажатия по кнопкам не обрабатываются: убедиться, что базовый fallback не перехватывает текст (в `core/handlers/basic.py` исключения по ключам переводов `add_card`, `my_cards`, `btn.partner.become`).
