# 🏷️ Неймспейсы i18n

## 📋 Обзор неймспейсов

Система i18n организована по неймспейсам для лучшей структуризации и избежания конфликтов.

## 🗂️ Структура неймспейсов

### `common.*` - Общие элементы
Элементы, используемые во всех частях приложения.

```json
{
  "common.back_simple": "◀️ Назад",
  "common.cancel": "❌ Отменить", 
  "common.save": "💾 Сохранить",
  "common.edit": "✏️ Редактировать",
  "common.delete": "🗑️ Удалить",
  "common.next": "➡️ Далее",
  "common.skip": "⏭️ Пропустить"
}
```

### `keyboard.*` - Кнопки клавиатур
Тексты для кнопок Reply и Inline клавиатур.

```json
{
  "keyboard.profile_settings": "⚙️ Настройки",
  "keyboard.referral_program": "👥 Реферальная программа",
  "keyboard.my_referral_link": "🔗 Моя реферальная ссылка",
  "keyboard.points": "💰 Мои баллы",
  "keyboard.history": "📜 История"
}
```

### `menu.*` - Навигация по меню
Элементы навигации между разделами.

```json
{
  "menu.back_to_main_menu": "◀️ Назад в главное меню",
  "menu.categories": "🗂️ Категории",
  "menu.favorites": "⭐ Избранные",
  "menu.invite_friends": "👥 Пригласить друзей",
  "menu.profile": "👤 Личный кабинет"
}
```

### `partner.*` - Партнёрские функции
Функциональность для партнёров.

```json
{
  "partner.back_to_partner_menu": "◀️ Назад в меню партнёра",
  "partner.add_card": "➕ Добавить карточку",
  "partner.my_cards": "📋 Мои карточки",
  "partner.statistics": "📊 Статистика",
  "partner.scan_qr": "🧾 Сканировать QR"
}
```

### `admin.*` - Админские функции
Функциональность для администраторов.

```json
{
  "admin.moderation": "🔍 Модерация",
  "admin.approve_card": "✅ Одобрить",
  "admin.reject_card": "❌ Отклонить",
  "admin.statistics": "📊 Статистика",
  "admin.dashboard": "📊 Дашборд"
}
```

### `user.*` - Пользовательские функции
Функциональность для обычных пользователей.

```json
{
  "user.profile_title": "👤 Личный кабинет",
  "user.points": "💰 Мои баллы",
  "user.history": "📜 История",
  "user.achievements": "🏆 Достижения",
  "user.qr_codes": "📱 QR-коды"
}
```

### `errors.*` - Сообщения об ошибках
Ошибки и предупреждения.

```json
{
  "errors.not_found": "❌ Не найдено",
  "errors.access_denied": "🚫 Доступ запрещён",
  "errors.invalid_input": "⚠️ Неверный ввод",
  "errors.server_error": "🔥 Ошибка сервера",
  "errors.network_error": "🌐 Ошибка сети"
}
```

### `messages.*` - Информационные сообщения
Информационные сообщения и уведомления.

```json
{
  "messages.success": "✅ Успешно",
  "messages.saved": "💾 Сохранено",
  "messages.loading": "⏳ Загрузка...",
  "messages.welcome": "👋 Добро пожаловать!",
  "messages.goodbye": "👋 До свидания!"
}
```

## 🔄 Миграция ключей

### Старые ключи → Новые неймспейсы

| Старый ключ | Новый неймспейс | Причина |
|-------------|-----------------|---------|
| `back_to_main` | `menu.back_to_main_menu` | Навигация по меню |
| `back_simple` | `common.back_simple` | Общий элемент |
| `profile_settings` | `keyboard.profile_settings` | Кнопка клавиатуры |
| `back_to_partner_menu` | `partner.back_to_partner_menu` | Партнёрская функция |

### Алиасы для обратной совместимости

```python
ALIASES = {
    "back_to_main": "menu.back_to_main_menu",
    "back_to_main_menu": "menu.back_to_main_menu", 
    "back_simple": "common.back_simple",
    "back_to_partner_menu": "partner.back_to_partner_menu",
    "profile_settings": "keyboard.profile_settings"
}
```

## 📝 Правила именования

### 1. Структура ключа:
```
{namespace}.{action}_{object}
```

### 2. Примеры:
```python
# ✅ Хорошо
'common.back_simple'
'keyboard.profile_settings'
'menu.back_to_main_menu'
'partner.add_card'
'admin.approve_card'
'user.view_profile'
'errors.not_found'
'messages.success'

# ❌ Плохо
'back'
'prof_set'
'menu_back'
'addcard'
'approve'
'viewprofile'
'notfound'
'success'
```

### 3. Соглашения:
- Используйте `snake_case`
- Группируйте по функциональности
- Избегайте сокращений
- Будьте последовательными

## 🧪 Тестирование неймспейсов

### Проверка структуры:
```python
def test_namespace_structure():
    """Проверяет правильность неймспейсов"""
    namespaces = ['common', 'keyboard', 'menu', 'partner', 'admin', 'user', 'errors', 'messages']
    
    for lang in ['ru', 'en']:
        texts = get_all_texts(lang)
        for key in texts.keys():
            if '.' in key:
                namespace = key.split('.')[0]
                assert namespace in namespaces, f"Unknown namespace: {namespace} in key {key}"
```

### Проверка алиасов:
```python
def test_aliases_valid():
    """Проверяет валидность всех алиасов"""
    for old_key, new_key in ALIASES.items():
        # Проверяем, что новый ключ существует
        assert get_text(new_key, 'ru') != f"[{new_key}]", f"Alias target {new_key} not found"
        
        # Проверяем, что алиас работает
        old_value = get_text(old_key, 'ru')
        new_value = get_text(new_key, 'ru')
        assert old_value == new_value, f"Alias {old_key} -> {new_key} values don't match"
```

## 🚀 Будущие неймспейсы

### Планируемые добавления:
- `qr.*` - QR-коды и сканирование
- `payment.*` - Платежи и транзакции
- `notification.*` - Уведомления
- `settings.*` - Настройки приложения
- `help.*` - Справка и поддержка

### Процесс добавления:
1. Создать RFC с обоснованием
2. Добавить неймспейс в документацию
3. Мигрировать существующие ключи
4. Обновить тесты
5. Обновить алиасы

