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
        'back_to_main_menu': 'Вернуться в главное меню🏘',
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
        'create_qr': '📱 Создать QR-код',
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
        # NEW: Shops & Services main category and submenu
        'category_shops_services': '🛍️ Магазины и услуги',
        'shops_choose': 'Выберите раздел магазинов и услуг:',
        'shops_shops': '🛍 Магазины',
        'shops_services': '🧩 Услуги',
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
        # NEW: SPA and Hotels submenus
        'spa_choose': 'Выберите раздел SPA:',
        'spa_salon': '💆 Спа-салоны',
        'spa_massage': '🤲 Массаж',
        'spa_sauna': '🧖 Бани/сауны',
        'hotels_choose': 'Выберите тип размещения:',
        'hotels_hotels': '🏨 Отели',
        'hotels_apartments': '🏘 Апартаменты',

        # NEW: Restaurant filters
        'restaurants_choose_cuisine': 'Выберите тип кухни:',
        'filter_asia': 'Азиатская',
        'filter_europe': 'Европейская',
        'filter_street': 'Стритфуд',
        'filter_vege': 'Вегетарианская',
        'filter_all': 'Показать все',

        # NEW: Welcome flow
        'welcome_message': '''{user_name} 👋 Добро пожаловать в Karma System!

✨ Получай эксклюзивные скидки и предложения через QR-код в удобных категориях:
🍽️ Рестораны и кафе
🧖‍♀️ SPA и массаж
🏍️ Аренда байков
🏨 Отели
🚶‍♂️ Экскурсии

А если ты владелец бизнеса — присоединяйся к нам как партнёр и подключай свою систему лояльности! 🚀

Начни экономить прямо сейчас — выбирай категорию и получай свои скидки!

Продолжая пользоваться ботом вы соглашаетесь с политикой обработки персональных данных.''',
        'policy_accept': '✅ Согласен',
        'policy_view': '📄 Политика конфиденциальности',
        'policy_url': '/policy',  # Внутренняя страница политики на нашем веб-сервисе

        # NEW: Common UI texts required by handlers
        'main_menu_title': '🏘 Главное меню\n\n✨ Выберите категорию ниже и начните экономить уже сейчас!',
        'language_updated': '✅ Язык обновлён',
        'policy_accepted': '✅ Политика принята',
        'choose_city': '🌆 Выберите город:',
        'city_selected': '✅ Город выбран',
        'city_updated': '✅ Город обновлён',
        'unhandled_message': '🤖 Я вас не понял. Пожалуйста, используйте меню команд.',

        # NEW: WebApp security / errors
        'webapp_auth_invalid': '❌ Неверная авторизация WebApp. Повторите вход из Telegram.',
        'webapp_auth_expired': '⌛ Сессия истекла. Откройте WebApp заново из бота.',
        'webapp_origin_denied': '🚫 Источник запроса не разрешён.',

        # NEW: Reply Menu
        'menu_scan_qr': '🧾 Сканировать QR',
        'scan_qr_unavailable': 'Сканирование недоступно. Доступно только партнёрам с активными карточками.',
        'webapp_open': '🔗 Открыть WebApp',

        # NEW: Partner cabinet navigation
        'btn_more': '⋮ Ещё',
        'btn_goto_page': '➡️ К странице…',
        'btn_search_listing': '🔎 Поиск',
        'btn_add_offer': '➕ Добавить предложение',
        'btn_metrics_category': '📈 Показатели по категории',
        'search_placeholder': 'Введите название или часть адреса…',
        'search_no_results': 'Ничего не найдено по вашему запросу.',

        # NEW: Reports
        'report_building': '⏳ Формируем отчёт… Это может занять некоторое время.',
        'report_rate_limited': '⏱ Лимит запросов отчётов исчерпан. Повторите позже.',

        # NEW: Inline profile buttons (per spec)
        'btn.points': '🎁 Баллы',
        'btn.spend': '💳 Потратить',
        'btn.history': '📜 История операций',
        'btn.report': '📊 Получить отчёт',
        'btn.card.bind': '🪪 Зарегистрировать карту',
        'btn.notify.on': '🔔 Уведомления (вкл)',
        'btn.notify.off': '🔔 Уведомления (выкл)',
        'btn.lang': '🌐 Язык',
        'btn.partner.become': '🧑‍💼 Стать партнёром',

        # NEW: Wallet/card messages
        'wallet.spend.min_threshold': 'Минимальная сумма списания: %{min} pts',
        'wallet.spend.insufficient': 'Недостаточно баллов. Доступно: %{points} pts',
        'card.bind.prompt': 'Введите номер карты (12 цифр).',
        'card.bind.invalid': 'Неверный формат номера карты.',
        'card.bind.occupied': 'Карта уже привязана к другому аккаунту.',
        'card.bind.blocked': 'Карта заблокирована. Обратитесь в поддержку.',
        # NEW: Bind options
        'card.bind.options': 'Выберите способ привязки: сканировать QR, отправить фото QR-кода или ввести номер вручную.',
        'card.bind.send_photo': '📷 Отправить фото QR-кода',
        'card.bind.enter_manually': '⌨️ Ввести номер вручную',
        'card.bind.open_scanner': '🧾 Сканировать QR (в разработке)'
        ,
        # NEW: Admin cabinet
        'admin_menu_queue': '🗃 Очередь модерации',
        'admin_menu_search': '🔎 Поиск',
        'admin_menu_reports': '📊 Отчёты',
        'admin_cabinet_title': '🛠 Кабинет администратора',
        'admin_hint_queue': 'Используйте команду /moderate для запуска модерации или кнопки ниже.',
        'admin_hint_search': 'Поиск по карточкам появится в следующем релизе.',
        'admin_hint_reports': 'Отчёты и метрики появятся в следующем релизе.'
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


def load_translations_from_dir(dirpath: str = None):
    """Load translations from all JSON files in a directory.
    Each file should be named like 'ru.json', 'en.json', etc., containing a flat {key: text} map.
    """
    global translations_v2, translations
    
    # Use absolute path if dirpath is not provided
    if dirpath is None:
        import os
        dirpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'i18n')
    
    p = Path(dirpath)
    if not p.exists():
        print(f"Warning: Translations directory not found: {p.absolute()}")
        return
        
    for file in p.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                lang_code = file.stem
                base = translations_v2.get(lang_code, {})
                base.update(data)
                translations_v2[lang_code] = base
                print(f"Loaded translations for language: {lang_code}")
        except Exception as e:
            print(f"Warning: Failed to load translations from {file}: {e}")
    
    translations = translations_v2

# Auto-load on import
load_translations_from_dir()
