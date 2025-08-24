# KARMABOT1 WebApp — состояние на заморозку

Дата: 2025-08-24

## 1. Что сделано
- UI-страница кабинета партнёра отдается роутом `GET /cabinet/partner/cards/page` в `web/main.py` (константа `INDEX_HTML`).
- Фикс авторизации на фронтенде:
  - `asciiToken()` фильтрует токен до печатаемых ASCII (32..126), чтобы заголовок `Authorization: Bearer` не ломался.
  - Глобальная обертка `fetch` автоматически подставляет `Authorization` для same-origin запросов.
  - `devTokenFlow()` сразу грузит профиль (`loadProfile()`), параллельно ставит куки и делает мягкий редирект на `?token=...`.
  - Добавлен UX: статус «Применяю токен… / Загружаю профиль…» и обработчик клавиши Enter в поле токена.
- Фикс UI: в HTML есть элементы, с которыми работает JS (`#cabinet`, `#status`, `#authStatus`, `#cardsList`, `#cardsEmpty`).
- Бэкенд `/cabinet` (файл `web/routes_cabinet.py`):
  - Зависимости: `get_current_claims()` принимает токен из Header/Cookie/Query и валидирует через `check_jwt`, `verify_partner`, `verify_admin`. Есть безопасный fallback на payload JWT для ролей `admin/superadmin/partner`.
  - Эндпоинты: `/cabinet/profile`, `/cabinet/partner/cards` (+ CRUD, изображения, запросы на удаление, справочники).
  - Автобутстрап SQLite (`core/database/data.db`): при первом запуске создаются минимальные таблицы `partners_v2`, `categories_v2`, `cards_v2` — исключает 500 на пустой БД.
- CSP и middleware для токенов включены в `web/main.py`.
- Добавлен диагностический вывод на странице (`#status`, `#error`, `#diag`).

## 2. Как воспроизвести локально
1) Запуск (Windows PowerShell):
```
$env:SHOW_DEBUG_UI="1"; uvicorn web.main:app --host 0.0.0.0 --port 8021 --reload
```
2) Открыть: `http://localhost:8021/cabinet/partner/cards/page`
3) Авторизация:
- Вставить JWT в поле и нажать Enter или «Применить токен», либо открыть URL c `?token=...`.
- Должно показать «Авторизация успешна» и профиль; затем загрузить «Мои карточки» (список или «Карточек пока нет»).

## 3. Известные проблемы (root causes / гипотезы)
- В отдельных окружениях страница может грузиться со старого кеша/Service Worker, из-за чего новые обработчики (Enter/статусы) незаметны. На странице выполняется `clearCachesAndSW()`, но настоятельно рекомендуем Ctrl+F5 и инкогнито.
- Если токен некорректный/просроченый, `/cabinet/profile` и `/cabinet/partner/cards` дадут 401. В консоли будут логи `[auth]` и `[cards]`.
- Telegram WebApp: иногда `initData` отсутствует в браузере, авторизация идёт через ручной токен.
- UI списка карточек пока минималистичный (отображение в `ul#cardsList` без таблицы/фильтров версии V2).

## 4. Что осталось / TODO (при разморозке)
- Полная UI-страница карточек V2: фильтры, пагинация, модалки редактирования, загрузка изображений, статусы модерации (есть в бэке — допилить фронт).
- Строгий поток авторизации WebApp: двойная проверка `initData` + refresh токена; унификация куки `SameSite=None; Secure` для iOS/Android WebApp.
- Улучшить empty state: кнопка «Создать карточку» (вызов `POST /cabinet/partner/cards`).
- Тесты: unit/интеграционные для `get_current_claims()`, профиля, карточек.
- Логи: structured logging + кореляция запросов.
- Документация для развёртывания (prod) и ключей JWT/Telegram.

## 5. API-справка (MVP)
- `GET /cabinet/profile` — профиль из JWT (роль auto или из токена).
- `GET /cabinet/partner/cards?limit=20&status=&q=&after_id=` — список карточек текущего партнёра или всех (для admin).
- `POST /cabinet/partner/cards` — создать «draft/pending» карточку.
- `PATCH /cabinet/partner/cards/{id}` — частичное обновление, чувствительные поля → `pending`.
- `POST /cabinet/partner/cards/{id}/hide` — в архив.
- Галерея: `GET/POST/DELETE /cabinet/partner/cards/{id}/images`.
- Справочники: `/cabinet/partner/categories`, `/cabinet/partner/subcategories`, `/cabinet/partner/cities`, `/cabinet/partner/areas`.

## 6. Навигация по коду
- Фронтенд (single HTML): `web/main.py` → `_INDEX_HTML_RAW` + `INDEX_HTML`.
- Кабинет-API: `web/routes_cabinet.py`.
- Аутентификация: `core/services/webapp_auth.py`, `core/security/jwt_service.py`.
- Настройки: `core/settings.py`.

## 7. Как понять, «в чём проблема», если UI «не реагирует»
- Проверьте версию HTML (страница должна показывать статусы «Применяю токен… / Загружаю профиль…» при вводе токена). Если нет — это кеш.
- В DevTools → Network: ответы `/cabinet/profile`, `/cabinet/partner/cards` (код 200/401/403/500 и тела ответов).
- В DevTools → Console: логи `"[auth] ..."`, `"[cards] ..."` показывают, каким способом авторизация проходила (header vs `?token`).

## 8. Статус: проект заморожен
- Код стабилизирован до отображения пустого списка карточек и загрузки профиля при корректном токене.
- TODO и дальнейшие шаги описаны выше.
