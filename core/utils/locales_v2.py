"""
Enhanced localization with backward compatibility
Extends existing translations without breaking changes
"""
from typing import Dict, Any
import json
from pathlib import Path

# Extended translations (backward compatible)
translations_v2 = {
    'ru': {
        # Existing keys (preserved for compatibility)
        'back_to_main': 'Вернуться в главное меню🏘',
        'choose_category': '🗂️ Категории',
        'show_nearest': '📍 Показать ближайшие',
        'choose_language': '🌐 Язык',
        'choose_district': '🌆 По районам',
        
        # NEW: P1 additions (profile/help)
        'profile': '👤 Личный кабинет',
        'help': '❓ Помощь',
        
        # NEW: Partner FSM texts
        'add_card': '➕ Добавить карточку',
        'my_cards': '📋 Мои карточки',
        'card_status_draft': '📝 Черновик',
        'card_status_pending': '⏳ На модерации',
        'card_status_approved': '✅ Одобрено',
        'card_status_published': '🎉 Опубликовано',
        'card_status_rejected': '❌ Отклонено',
        'card_status_archived': '🗂️ Архив',
        
        # NEW: Moderation texts
        'moderation_title': '🔍 Модерация',
        'approve_card': '✅ Одобрить',
        'reject_card': '❌ Отклонить',
        'feature_card': '⭐ Рекомендуемое',
        'archive_card': '🗂️ Архив',
        
        # NEW: Common actions
        'cancel': '❌ Отменить',
        'skip': '⏭️ Пропустить',
        'back': '🔙 Назад',
        'next': '➡️ Далее',
        'edit': '✏️ Редактировать',
        'delete': '🗑️ Удалить',
        'save': '💾 Сохранить',
        
        # NEW: Card renderer texts
        'contact_info': '📞 Контакты',
        'address_info': '📍 Адрес',
        'discount_info': '🎫 Скидка',
        'show_on_map': '🗺️ Показать на карте',
        'create_qr': '📱 Создать QR',
        'call_business': '📞 Связаться',
        'book_service': '📅 Записаться',
        
        # NEW: Help texts
        'help_main': '''❓ **Справка по боту**

🗂️ **Категории** - просмотр заведений по типам
👤 **Личный кабинет** - управление карточками
📍 **Показать ближайшие** - поиск рядом с вами
🌆 **По районам** - выбор по местоположению
🌐 **Язык** - смена языка интерфейса

**Для партнеров:**
/add_card - добавить новую карточку
/my_cards - просмотр ваших карточек

**Поддержка:** @support_bot''',
        
        # NEW: Profile texts
        'profile_main': '👤 **Личный кабинет**',
        'profile_stats': '📊 Статистика',
        'profile_settings': '⚙️ Настройки',
        'cards_count': 'Карточек',
        'views_count': 'Просмотров',
        'qr_scans': 'QR сканирований',

        # NEW: Category Menu (v2)
        'category_restaurants': '🍽 Рестораны',
        'category_spa': '🧖‍♀️ SPA',
        'category_transport': '🚗 Транспорт',
        'category_hotels': '🏨 Отели',
        'category_tours': '🚶‍♂️ Экскурсии',
        'transport_bikes': '🛵 Байки',
        'transport_cars': '🚘 Машины',
        'transport_bicycles': '🚲 Велосипед',
        'tours_group': '👥 Групповые',
        'tours_private': '🧑‍🤝‍🧑 Индивидуальные',
        'back_to_categories': '◀️ Назад',
        'catalog_found': 'Найдено',
        'catalog_page': 'Стр.',
        'catalog_empty_sub': '📭 В этой подкатегории пока нет заведений.',
        'transport_choose': 'Выберите вид транспорта:',
        'tours_choose': 'Выберите тип экскурсии:',
    }
}

def get_text(key: str, lang: str = 'ru') -> str:
    """
    Get localized text with fallback
    Backward compatible with existing code
    """
    # Try new translations first
    if lang in translations_v2 and key in translations_v2[lang]:
        return translations_v2[lang][key]
    
    # Fallback to Russian if key not found in requested language
    if key in translations_v2['ru']:
        return translations_v2['ru'][key]
    
    # Ultimate fallback
    return f"[{key}]"

def get_all_texts(lang: str = 'ru') -> Dict[str, str]:
    """Get all texts for a language"""
    return translations_v2.get(lang, translations_v2['ru'])

def get_supported_languages() -> list:
    """Get list of supported language codes"""
    return list(translations_v2.keys())

# Backward compatibility: expose as 'translations' for existing code
translations = translations_v2

# Export for contract tests
REQUIRED_KEYS = set(translations_v2['ru'].keys())

def validate_translations() -> Dict[str, list]:
    """Validate that all languages have required keys"""
    missing_keys = {}
    
    for lang, texts in translations_v2.items():
        missing = REQUIRED_KEYS - set(texts.keys())
        if missing:
            missing_keys[lang] = list(missing)
    
    return missing_keys


def load_translations_from_dir(dirpath: str = "core/i18n"):
    """Load translations from all JSON files in a directory.
    Each file should be named like 'ru.json', 'en.json', etc., containing a flat {key: text} map.
    """
    global translations_v2, translations
    p = Path(dirpath)
    if not p.exists():
        return
    for file in p.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                lang_code = file.stem
                base = translations_v2.get(lang_code, {})
                base.update(data)
                translations_v2[lang_code] = base
        except Exception as e:
            print(f"Warning: Failed to load translations from {file}: {e}")
    translations = translations_v2

# Auto-load on import
load_translations_from_dir()
