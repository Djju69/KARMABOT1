# 🌐 Руководство по i18n (многоязычности)

## 📋 Обзор

Проект поддерживает многоязычность через систему i18n с обратной совместимостью. Основные языки: RU, EN, VI, KO.

## 🏗️ Архитектура

### Файлы локализации:
- `locales/ru.json` - русский (эталонный)
- `locales/en.json` - английский
- `locales/deprecated.json` - устаревшие ключи
- `core/utils/locales_v2.py` - расширенные переводы

### Неймспейсы:
- `common.*` - общие элементы (кнопки назад, действия)
- `keyboard.*` - кнопки клавиатур
- `menu.*` - навигация по меню
- `partner.*` - партнёрские функции
- `admin.*` - админские функции
- `user.*` - пользовательские функции
- `errors.*` - сообщения об ошибках
- `messages.*` - информационные сообщения

## ➕ Добавление новых ключей

### 1. Добавить в JSON файлы:
```json
// locales/ru.json
{
  "new_key": "Новый текст"
}

// locales/en.json  
{
  "new_key": "New text"
}
```

### 2. Добавить в locales_v2.py (опционально):
```python
translations_v2 = {
    'ru': {
        'new_key': 'Новый текст'
    },
    'en': {
        'new_key': 'New text'
    }
}
```

### 3. Использовать в коде:
```python
from core.utils.locales_v2 import get_text

text = get_text('new_key', lang='ru')
```

## 🔄 Система алиасов

Для обратной совместимости используется система алиасов:

```python
ALIASES = {
    "back_to_main": "menu.back_to_main_menu",
    "back_to_main_menu": "menu.back_to_main_menu", 
    "back_simple": "common.back_simple",
    "back_to_partner_menu": "partner.back_to_partner_menu",
    "profile_settings": "keyboard.profile_settings"
}
```

### Как работает:
1. При вызове `get_text('back_to_main', 'ru')`
2. Система проверяет алиасы
3. Находит `back_to_main` → `menu.back_to_main_menu`
4. Возвращает значение для `menu.back_to_main_menu`

## 🗑️ Помечание ключей как deprecated

### 1. Добавить в deprecated.json:
```json
{
  "_comment": "Deprecated i18n keys - kept for backward compatibility",
  "_deprecated_keys": {
    "old_key": "Use 'new_key' instead"
  },
  "old_key": "Старое значение"
}
```

### 2. Добавить алиас:
```python
ALIASES = {
    "old_key": "new_key"
}
```

### 3. Обновить документацию

## ⏰ Сроки удаления deprecated ключей

- **Минимум 2 релиза** - алиасы должны работать
- **После 2 релизов** - можно удалить через RFC
- **Критично:** не удалять без согласования!

## 🧪 Тестирование

### Автотест консистентности:
```bash
python tests/test_i18n_consistency.py
```

### Проверки:
- ✅ Одинаковый набор ключей во всех языках
- ✅ Отсутствие дубликатов
- ✅ Корректность JSON синтаксиса
- ✅ Валидность алиасов

## 📝 Соглашения

### Именование ключей:
- Используйте `snake_case`
- Группируйте по неймспейсам
- Избегайте сокращений

### Примеры:
```python
# ✅ Хорошо
'common.back_simple'
'keyboard.profile_settings'
'menu.back_to_main_menu'
'partner.add_card'

# ❌ Плохо
'back'
'prof_set'
'menu_back'
```

### Значения:
- Сохраняйте эмодзи
- Используйте форматирование Markdown при необходимости
- Избегайте слишком длинных строк

## 🚨 Важные правила

1. **НЕ удаляйте** старые ключи сразу
2. **НЕ меняйте** тексты UI без согласования
3. **ВСЕГДА добавляйте** переводы для всех языков
4. **ИСПОЛЬЗУЙТЕ** алиасы для миграции
5. **ТЕСТИРУЙТЕ** изменения

## 🔧 Утилиты

### Получить все тексты:
```python
from core.utils.locales_v2 import get_all_texts
texts = get_all_texts('ru')
```

### Поддерживаемые языки:
```python
from core.utils.locales_v2 import get_supported_languages
langs = get_supported_languages()  # ['ru', 'en', 'ko', 'vi']
```

### Проверить существование ключа:
```python
from core.utils.locales_v2 import get_text
try:
    text = get_text('key', 'ru')
    if text.startswith('[') and text.endswith(']'):
        print(f"Key 'key' not found")
except:
    print("Error getting text")
```
