"""
Enhanced localization with backward compatibility
Extends existing translations without breaking changes
"""
from typing import Dict, Any
import json
from pathlib import Path

# Extended translations (backward compatible)
translations_v2 = {
    'ko': {
        # Existing keys
        'back_to_main_menu': '메인 메뉴로 돌아가기🏘',
        'choose_category': '🗂️ 카테고리',
        'show_nearest': '📍 가까운 매장',
        
        # User profile
        'cabinet.user_profile': '👤 내 정보\n\n💎 포인트: {points}\n🏆 레벨: {level}\n\n아래 메뉴를 사용하여 프로필을 관리하세요',
        'cabinet.user_points': '💰 내 포인트: {points}\n\n파트너사에서 사용할 수 있습니다',
        'cabinet.history_header': '📜 거래 내역:',
        'cabinet.partner_profile': '👤 파트너 프로필\n\n✅ 승인된 카드: {approved_cards}\n👀 총 조회수: {total_views}\n📊 총 스캔 수: {total_scans}',
        'cabinet.partner_statistics': '📊 통계\n\n📋 총 카드 수: {total_cards}\n✅ 활성화된 카드: {active_cards}\n👀 조회수: {total_views}\n📊 스캔 수: {total_scans}\n📈 전환률: {conversion_rate}%',
        'partner.no_cards': '아직 승인된 카드가 없습니다.\n카드를 추가하여 시작하세요.',
        
        # Keyboard buttons
        'keyboard.points': '💰 내 포인트',
        'keyboard.history': '📜 거래 내역',
        'keyboard.spend': '💳 사용',
        'keyboard.report': '📊 보고서',
        'keyboard.card': '🎫 내 카드',
        'keyboard.settings': '⚙️ 설정',
        'keyboard.back': '◀️ 뒤로',
        'keyboard.my_cards': '📋 내 카드',
        'keyboard.scan_qr': '📱 QR 스캔',
        'keyboard.statistics': '📈 통계',
        'keyboard.support': '🆘 지원',
        'keyboard.confirm': '✅ 확인',
        'keyboard.cancel': '❌ 취소',
        'keyboard.enter_amount': '💳 금액 입력',
        'keyboard.prev_page': '⬅️ 이전',
        'keyboard.next_page': '다음 ➡️',
        'keyboard.become_partner': '👨‍💼 파트너가되기',
        'choose_language': '🌐 언어',
        'choose_district': '🌆 지역별',
        
        # Keyboard menu items
        'keyboard.categories': '🗂️ 카테고리',
        'keyboard.nearest': '📍 가까운 매장',
        'keyboard.help': '❓ 도움말',
        'keyboard.choose_language': '🌐 언어 변경',
        'keyboard.back_to_main': '🏠 메인 메뉴',
        
        # Profile/help
        'profile': '👤 내 정보',
        'help': '❓ 도움말',
        
        # Partner FSM texts
        'add_card': '➕ 카드 추가',
        'my_cards': '📋 내 카드',
        'card_status_draft': '📝 초안',
        'card_status_pending': '⏳ 검토 중',
        'card_status_approved': '✅ 승인됨',
        'card_status_published': '🎉 게시됨',
        'card_status_rejected': '❌ 거부됨',
        'card_status_archived': '🗂️ 보관됨',
        
        # Moderation texts
        'moderation_title': '🔍 검토',
        'approve_card': '✅ 승인',
        'reject_card': '❌ 거부',
        'feature_card': '⭐ 추천',
        'archive_card': '🗂️ 보관',
        
        # Common actions
        'cancel': '❌ 취소',
        'skip': '⏭️ 건너뛰기',
        'back': '🔙 뒤로',
        
        # Help text
        'help_text': '''안녕하세요! KarmaBot을 이용해 주셔서 감사합니다.\n\n사용 가능한 명령어:\n/start - 봇 시작\n/help - 도움말\n/menu - 메인 메뉴\n/language - 언어 변경\n\n도움이 필요하시면 @support_bot으로 문의해 주세요.''',
        
        # Profile texts
        'profile_main': '👤 **내 정보**',
        'profile_stats': '📊 통계',
        'profile_settings': '⚙️ 설정',
        'profile_help': '❓ 도움말',
        
        # Policy
        'policy_text': '''개인정보 처리방침에 동의해 주세요.\n\n계속하시면 개인정보 처리방침에 동의하는 것으로 간주됩니다.''',
        'policy_accept': '✅ 동의합니다',
        'policy_view': '📄 개인정보 처리방침',
        'policy_url': '/policy',
        
        # Common UI
        'error_occurred': '⚠️ 오류가 발생했습니다. 나중에 다시 시도해 주세요.',
        'not_available': '🚧 현재 사용할 수 없는 기능입니다.',
        'thanks': '🙏 감사합니다!',
        'loading': '로드 중...',
        'saved': '저장되었습니다!',
        'select_option': '옵션을 선택하세요:',
        'no_results': '결과가 없습니다.',
        'try_again': '다시 시도하세요.',
        'success': '성공!',
        'failed': '실패했습니다.'
    },
    'vi': {
        # Existing keys
        'back_to_main_menu': 'Về menu chính🏘',
        'choose_category': '🗂️ Danh mục',
        'show_nearest': '📍 Gần nhất',
        'choose_language': '🌐 Ngôn ngữ',
        'choose_district': '🌆 Khu vực',
        
        # User profile
        'cabinet.user_profile': '👤 Hồ sơ của bạn\n\n💎 Điểm: {points}\n🏆 Cấp độ: {level}\n\nSử dụng menu bên dưới để quản lý hồ sơ',
        'cabinet.user_points': '💰 Điểm của bạn: {points}\n\nBạn có thể sử dụng chúng tại các đối tác của chúng tôi',
        'cabinet.history_header': '📜 Lịch sử giao dịch:',
        'cabinet.partner_profile': '👤 Tài khoản đối tác\n\n✅ Thẻ đã duyệt: {approved_cards}\n👀 Lượt xem: {total_views}\n📊 Lượt quét: {total_scans}',
        'cabinet.partner_statistics': '📊 Thống kê\n\n📋 Tổng thẻ: {total_cards}\n✅ Đang hoạt động: {active_cards}\n👀 Lượt xem: {total_views}\n📊 Lượt quét: {total_scans}\n📈 Tỷ lệ chuyển đổi: {conversion_rate}%',
        'partner.no_cards': 'Bạn chưa có thẻ nào được duyệt.\nThêm thẻ để bắt đầu.',
        
        # Keyboard buttons
        'keyboard.points': '💰 Điểm của tôi',
        'keyboard.history': '📜 Lịch sử',
        'keyboard.spend': '💳 Tiêu điểm',
        'keyboard.report': '📊 Báo cáo',
        'keyboard.card': '🎫 Thẻ của tôi',
        'keyboard.settings': '⚙️ Cài đặt',
        'keyboard.back': '◀️ Quay lại',
        'keyboard.my_cards': '📋 Thẻ của tôi',
        'keyboard.scan_qr': '📱 Quét QR',
        'keyboard.statistics': '📈 Thống kê',
        'keyboard.support': '🆘 Hỗ trợ',
        'keyboard.confirm': '✅ Xác nhận',
        'keyboard.cancel': '❌ Hủy',
        'keyboard.enter_amount': '💳 Nhập số tiền',
        'keyboard.prev_page': '⬅️ Trước',
        'keyboard.next_page': 'Sau ➡️',
        'keyboard.become_partner': '👨‍💼 Trở thành đối tác',
        
        # Keyboard menu items
        'keyboard.categories': '🗂️ Danh mục',
        'keyboard.nearest': '📍 Gần nhất',
        'keyboard.help': '❓ Trợ giúp',
        'keyboard.choose_language': '🌐 Đổi ngôn ngữ',
        'keyboard.back_to_main': '🏠 Về menu chính',
        
        # Profile/help
        'profile': '👤 Hồ sơ',
        'help': '❓ Trợ giúp',
        
        # Common actions
        'cancel': '❌ Hủy',
        'skip': '⏭️ Bỏ qua',
        'back': '🔙 Quay lại',
        'next': '➡️ Tiếp',
        'edit': '✏️ Chỉnh sửa',
        'delete': '🗑️ Xóa',
        'save': '💾 Lưu',
        
        # Common UI
        'error_occurred': '⚠️ Đã xảy ra lỗi. Vui lòng thử lại sau.',
        'not_available': '🚧 Tính năng hiện không khả dụng.',
        'thanks': '🙏 Cảm ơn!',
        'loading': 'Đang tải...',
        'saved': 'Đã lưu!',
        'select_option': 'Chọn một tùy chọn:',
        'no_results': 'Không có kết quả.',
        'try_again': 'Thử lại.',
        'success': 'Thành công!',
        'failed': 'Thất bại!'
    },
    'ru': {
        # Existing keys (preserved for compatibility)
        'back_to_main_menu': 'Вернуться в главное меню🏘',
        'choose_category': '🗂️ Категории',
        'show_nearest': '📍 Показать ближайшие',
        
        # User profile
        'cabinet.user_profile': '👤 Ваш профиль\n\n💎 Баллы: {points}\n🏆 Уровень: {level}\n\nИспользуйте меню ниже для управления профилем',
        'cabinet.user_points': '💰 Ваши баллы: {points}\n\nВы можете потратить их у наших партнеров',
        'cabinet.history_header': '📜 История операций:',
        'cabinet.partner_profile': '👤 Кабинет партнера\n\n✅ Одобрено карточек: {approved_cards}\n👀 Всего просмотров: {total_views}\n📊 Всего сканирований: {total_scans}',
        'cabinet.partner_statistics': '📊 Статистика\n\n📋 Всего карточек: {total_cards}\n✅ Активных: {active_cards}\n👀 Просмотров: {total_views}\n📊 Сканирований: {total_scans}\n📈 Конверсия: {conversion_rate}%',
        'partner.no_cards': 'У вас пока нет одобренных карточек.\nДобавьте карточку, чтобы начать работу.',
        
        # Keyboard buttons
        'keyboard.points': '💰 Мои баллы',
        'keyboard.history': '📜 История',
        'keyboard.spend': '💳 Потратить',
        'keyboard.report': '📊 Отчет',
        'keyboard.card': '🎫 Моя карта',
        'keyboard.settings': '⚙️ Настройки',
        'keyboard.back': '◀️ Назад',
        'keyboard.my_cards': '📋 Мои карточки',
        'keyboard.scan_qr': '📱 Сканировать QR',
        'keyboard.statistics': '📈 Статистика',
        'keyboard.support': '🆘 Поддержка',
        'keyboard.confirm': '✅ Подтвердить',
        'keyboard.cancel': '❌ Отмена',
        'keyboard.enter_amount': '💳 Ввести сумму',
        'keyboard.prev_page': '⬅️ Назад',
        'keyboard.next_page': 'Вперед ➡️',
        'keyboard.become_partner': '👨‍💼 Стать партнером',
        
        # User profile
        'cabinet.user_profile': '👤 Ваш профиль\n\n💎 Баллы: {points}\n🏆 Уровень: {level}\n\nИспользуйте меню ниже для управления профилем',
        'cabinet.user_points': '💰 Ваши баллы: {points}\n\nВы можете потратить их у наших партнеров',
        'cabinet.history_header': '📜 История операций:',
        'cabinet.partner_profile': '👤 Кабинет партнера\n\n✅ Одобрено карточек: {approved_cards}\n👀 Всего просмотров: {total_views}\n📊 Всего сканирований: {total_scans}',
        'cabinet.partner_statistics': '📊 Статистика\n\n📋 Всего карточек: {total_cards}\n✅ Активных: {active_cards}\n👀 Просмотров: {total_views}\n📊 Сканирований: {total_scans}\n📈 Конверсия: {conversion_rate}%',
        'partner.no_cards': 'У вас пока нет одобренных карточек.\nДобавьте карточку, чтобы начать работу.',
        
        # Keyboard buttons
        'keyboard.points': '💰 Мои баллы',
        'keyboard.history': '📜 История',
        'keyboard.spend': '💳 Потратить',
        'keyboard.report': '📊 Отчет',
        'keyboard.card': '🎫 Моя карта',
        'keyboard.settings': '⚙️ Настройки',
        'keyboard.back': '◀️ Назад',
        'keyboard.my_cards': '📋 Мои карточки',
        'keyboard.scan_qr': '📱 Сканировать QR',
        'keyboard.statistics': '📈 Статистика',
        'keyboard.support': '🆘 Поддержка',
        'keyboard.confirm': '✅ Подтвердить',
        'keyboard.cancel': '❌ Отмена',
        'keyboard.enter_amount': '💳 Ввести сумму',
        'keyboard.prev_page': '⬅️ Назад',
        'keyboard.next_page': 'Вперед ➡️',
        'keyboard.become_partner': '👨‍💼 Стать партнером',
        'choose_language': '🌐 Язык',
        'choose_district': '🌆 По районам',
        
        # Keyboard menu items
        'keyboard.categories': '🗂️ Категории',
        'keyboard.nearest': '📍 Ближайшие',
        'keyboard.help': '❓ Помощь',
        'keyboard.choose_language': '🌐 Сменить язык',
        'keyboard.back_to_main': '🏠 В главное меню',
        
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
