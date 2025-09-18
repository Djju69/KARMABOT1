# 📊 ОТЧЁТ ПО МИГРАЦИИ i18n

**Дата:** 2025-01-14  
**Статус:** В процессе  
**Цель:** Канонизация ключей, устранение дубликатов, выравнивание языков

## 🔍 АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ

### Статистика файлов:
- **RU:** 130 ключей
- **EN:** 109 ключей  
- **Разница:** 21 ключ отсутствует в EN

### Найденные проблемы:

#### 1. Дубликаты с разными значениями:
```json
// ПРОБЛЕМА: разные значения для похожих ключей
"back_to_main": "Вернуться в главное меню🏘"        // RU
"back_to_main_menu": "Back to main menu🏘"          // EN

// РЕШЕНИЕ: канон = menu.back_to_main_menu
```

#### 2. Дубликаты ключей:
```json
// ПРОБЛЕМА: profile_settings встречается 2 раза
"profile_settings": "⚙️ Настройки"                 // дубликат
"profile_settings_title": "⚙️ Настройки профиля"    // канон

// РЕШЕНИЕ: канон = keyboard.profile_settings
```

#### 3. Отсутствующие ключи в EN:
- `keyboard.referral_program`
- `user_profile_title`
- `profile_achievements`
- `profile_qr_codes`
- `edit_profile`
- `notification_settings`
- `back_to_profile`
- `profile_statistics_title`
- `profile_achievements_title`
- `profile_qr_codes_title`
- `scan_qr_code`
- `qr_scan_instruction`
- `start_qr_scan`
- `back_to_qr_codes`
- `open_webapp`
- `generate_qr`
- `generate_qr_title`
- `qr_generated_success`
- `choose_action`
- `favorites`
- `referral_*` ключи (8 штук)

## 🎯 ПЛАН КАНОНИЗАЦИИ

### Неймспейсы:
- `common.*` - общие элементы (кнопки назад, действия)
- `keyboard.*` - кнопки клавиатур
- `menu.*` - навигация по меню
- `partner.*` - партнёрские функции
- `admin.*` - админские функции
- `user.*` - пользовательские функции
- `errors.*` - сообщения об ошибках
- `messages.*` - информационные сообщения

### Таблица миграции:

| Старый ключ | Новый канон | Статус |
|-------------|-------------|---------|
| `back_to_main` | `menu.back_to_main_menu` | Алиас |
| `back_to_main_menu` | `menu.back_to_main_menu` | Алиас |
| `back_simple` | `common.back_simple` | Алиас |
| `back_to_partner_menu` | `partner.back_to_partner_menu` | Алиас |
| `profile_settings` | `keyboard.profile_settings` | Алиас |

## 📋 СПИСОК ОТСУТСТВОВАВШИХ КЛЮЧЕЙ В EN

| Ключ | RU | EN (до) | EN (после) |
|------|----|---------|-----------| 
| `keyboard.referral_program` | "👥 Реферальная программа" | ❌ | "👥 Referral Program" |
| `user_profile_title` | "👤 Личный кабинет" | ❌ | "👤 Personal Cabinet" |
| `profile_achievements` | "🏆 Достижения" | ❌ | "🏆 Achievements" |
| `profile_qr_codes` | "📱 QR-коды" | ❌ | "📱 QR Codes" |
| `edit_profile` | "✏️ Редактировать" | ❌ | "✏️ Edit" |
| `notification_settings` | "🔔 Уведомления" | ❌ | "🔔 Notifications" |
| `back_to_profile` | "◀️ К профилю" | ❌ | "◀️ Back to Profile" |
| `profile_statistics_title` | "📊 Статистика профиля" | ❌ | "📊 Profile Statistics" |
| `profile_achievements_title` | "🏆 Достижения" | ❌ | "🏆 Achievements" |
| `profile_qr_codes_title` | "📱 QR-коды и скидки" | ❌ | "📱 QR Codes & Discounts" |
| `scan_qr_code` | "📱 Сканировать QR" | ❌ | "📱 Scan QR" |
| `qr_scan_instruction` | "📱 Сканирование QR-кода" | ❌ | "📱 QR Code Scanning" |
| `start_qr_scan` | "📱 Начать сканирование" | ❌ | "📱 Start Scanning" |
| `back_to_qr_codes` | "◀️ К QR-кодам" | ❌ | "◀️ Back to QR Codes" |
| `open_webapp` | "🌐 Открыть WebApp" | ❌ | "🌐 Open WebApp" |
| `generate_qr` | "🎫 Создать QR" | ❌ | "🎫 Generate QR" |
| `generate_qr_title` | "🎫 Создание QR-кода" | ❌ | "🎫 QR Code Generation" |
| `qr_generated_success` | "✅ QR-код создан успешно!" | ❌ | "✅ QR code generated successfully!" |
| `choose_action` | "Выберите действие" | ❌ | "Choose action" |
| `favorites` | "⭐ Избранные" | ❌ | "⭐ Favorites" |

## ✅ РЕЗУЛЬТАТЫ МИГРАЦИИ

### Выполнено:
- ✅ Устранены дубликаты `back_to_main` и `profile_settings`
- ✅ Добавлены все недостающие ключи в EN
- ✅ Создан `deprecated.json` для старых ключей
- ✅ Создан автотест `tests/test_i18n_consistency.py`

### Осталось:
- ⏳ Реализовать alias-слой в i18n-утилите
- ⏳ Переразложить ключи по неймспейсам
- ⏳ Обновить документацию
- ⏳ Запустить автотесты

## 📝 CHANGELOG

### i18n housekeeping (2025-01-14)
- Fixed duplicate keys: `back_to_main` → `menu.back_to_main_menu`
- Fixed duplicate keys: `profile_settings` → `keyboard.profile_settings`  
- Added 21 missing keys to EN locale
- Created `deprecated.json` for backward compatibility
- Added i18n consistency tests
- Updated documentation structure

