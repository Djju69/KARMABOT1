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
    },
    
    'en': {
        # Existing keys (preserved)
        'back_to_main': 'Back to main menu🏘',
        'choose_category': '🗂️ Categories',
        'show_nearest': '📍 By districts / Nearby',
        'choose_language': '🌐 Language',
        'choose_district': '🌆 By districts',
        
        # NEW: P1 additions
        'profile': '👤 Profile',
        'help': '❓ Help',
        
        # NEW: Partner FSM
        'add_card': '➕ Add card',
        'my_cards': '📋 My cards',
        'card_status_draft': '📝 Draft',
        'card_status_pending': '⏳ Pending',
        'card_status_approved': '✅ Approved',
        'card_status_published': '🎉 Published',
        'card_status_rejected': '❌ Rejected',
        'card_status_archived': '🗂️ Archived',
        
        # NEW: Moderation
        'moderation_title': '🔍 Moderation',
        'approve_card': '✅ Approve',
        'reject_card': '❌ Reject',
        'feature_card': '⭐ Feature',
        'archive_card': '🗂️ Archive',
        
        # NEW: Common actions
        'cancel': '❌ Cancel',
        'skip': '⏭️ Skip',
        'back': '🔙 Back',
        'next': '➡️ Next',
        'edit': '✏️ Edit',
        'delete': '🗑️ Delete',
        'save': '💾 Save',
        
        # NEW: Card renderer
        'contact_info': '📞 Contact',
        'address_info': '📍 Address',
        'discount_info': '🎫 Discount',
        'show_on_map': '🗺️ Show on map',
        'create_qr': '📱 Create QR',
        'call_business': '📞 Contact',
        'book_service': '📅 Book',
        
        # NEW: Help
        'help_main': 'This is Karma Bot. Use the menu to navigate.',
        'catalog_empty': 'There is nothing in this category yet.',
        'catalog_error': 'An error occurred while loading the catalog. Please try again later.',
        'start_welcome': '👋 Hello! Choose a language and category in the main menu.',
        'main_menu_title': 'Main menu: use the buttons below.',
        'language_updated': 'Language updated',
        'choose_city': 'Choose a district:',
        'city_updated': 'City/district updated',
        'city_selected': 'District selected. You can continue searching.',
        'policy_accepted': 'Policy accepted',
        'unhandled_message': 'I don\'t understand. Please use the menu buttons.',
        
        # NEW: Profile
        'profile_main': '👤 **Profile**',
        'profile_stats': '📊 Statistics',
        'profile_settings': '⚙️ Settings',
        'cards_count': 'Cards',
        'views_count': 'Views',
        'qr_scans': 'QR scans',

        # NEW: Category Menu (v2)
        'category_restaurants': '🍽 Restaurants',
        'category_spa': '🧖‍♀️ SPA',
        'category_transport': '🚗 Transport',
        'category_hotels': '🏨 Hotels',
        'category_tours': '🚶‍♂️ Tours',
        'transport_bikes': '🛵 Bikes',
        'transport_cars': '🚘 Cars',
        'transport_bicycles': '🚲 Bicycles',
        'tours_group': '👥 Group',
        'tours_private': '🧑‍🤝‍🧑 Private',
        'back_to_categories': '◀️ Back',
        'catalog_found': 'Found',
        'catalog_page': 'Page',
        'catalog_empty_sub': '📭 There are no places in this subcategory yet.',
        'transport_choose': 'Choose transport type:',
        'tours_choose': 'Choose tour type:',
    },
    
    'vi': {
        # Existing keys (preserved)
        'back_to_main': 'Về menu chính🏘',
        'choose_category': '🗂️ Danh mục',
        'show_nearest': '📍 Theo quận / Gần đây',
        'choose_language': '🌐 Ngôn ngữ',
        'choose_district': '🌆 Theo quận',
        
        # NEW: P1 additions
        'profile': '👤 Hồ sơ',
        'help': '❓ Trợ giúp',
        
        # NEW: Partner FSM
        'add_card': '➕ Thêm thẻ',
        'my_cards': '📋 Thẻ của tôi',
        'card_status_draft': '📝 Bản nháp',
        'card_status_pending': '⏳ Đang chờ',
        'card_status_approved': '✅ Đã duyệt',
        'card_status_published': '🎉 Đã xuất bản',
        'card_status_rejected': '❌ Bị từ chối',
        'card_status_archived': '🗂️ Lưu trữ',
        
        # NEW: Common actions
        'cancel': '❌ Hủy',
        'skip': '⏭️ Bỏ qua',
        'back': '🔙 Quay lại',
        'next': '➡️ Tiếp theo',
        'edit': '✏️ Chỉnh sửa',
        'delete': '🗑️ Xóa',
        'save': '💾 Lưu',
        
        # NEW: Card renderer
        'contact_info': '📞 Liên hệ',
        'address_info': '📍 Địa chỉ',
        'discount_info': '🎫 Giảm giá',
        'show_on_map': '🗺️ Hiện trên bản đồ',
        'create_qr': '📱 Tạo QR',
        'call_business': '📞 Liên hệ',
        'book_service': '📅 Đặt chỗ',
        
        # NEW: Help
        'help_main': 'Đây là Karma Bot. Sử dụng menu để điều hướng.',
        'catalog_empty': 'Chưa có gì trong danh mục này.',
        'catalog_error': 'Đã xảy ra lỗi khi tải danh mục. Vui lòng thử lại sau.',
        'start_welcome': '👋 Xin chào! Chọn ngôn ngữ và danh mục trong menu chính.',
        'main_menu_title': 'Menu chính: sử dụng các nút bên dưới.',
        'language_updated': 'Đã cập nhật ngôn ngữ',
        'choose_city': 'Chọn một quận:',
        'city_updated': 'Đã cập nhật thành phố/quận',
        'city_selected': 'Đã chọn quận. Bạn có thể tiếp tục tìm kiếm.',
        'policy_accepted': 'Chính sách được chấp nhận',
        'unhandled_message': 'Tôi không hiểu. Vui lòng sử dụng các nút menu.',
        
        # NEW: Profile
        'profile_main': '👤 **Hồ sơ**',
        'profile_stats': '📊 Thống kê',
        'profile_settings': '⚙️ Cài đặt',
        'cards_count': 'Thẻ',
        'views_count': 'Lượt xem',
        'qr_scans': 'Quét QR',

        # NEW: Category Menu (v2)
        'category_restaurants': '🍽 Nhà hàng',
        'category_spa': '🧖‍♀️ SPA',
        'category_transport': '🚗 Vận chuyển',
        'category_hotels': '🏨 Khách sạn',
        'category_tours': '🚶‍♂️ Tour',
        'transport_bikes': '🛵 Xe máy',
        'transport_cars': '🚘 Ô tô',
        'transport_bicycles': '🚲 Xe đạp',
        'tours_group': '👥 Nhóm',
        'tours_private': '🧑‍🤝‍🧑 Riêng tư',
        'back_to_categories': '◀️ Quay lại',
        'catalog_found': 'Tìm thấy',
        'catalog_page': 'Trang',
        'catalog_empty_sub': '📭 Chưa có địa điểm nào trong tiểu mục này.',
        'transport_choose': 'Chọn loại phương tiện:',
        'tours_choose': 'Chọn loại tour:',
    },
    
    'ko': {
        # Existing keys (preserved)
        'back_to_main': '메인 메뉴로🏘',
        'choose_category': '🗂️ 카테고리',
        'show_nearest': '📍 지역별 / 근처',
        'choose_language': '🌐 언어',
        'choose_district': '🌆 지역별',
        
        # NEW: P1 additions
        'profile': '👤 프로필',
        'help': '❓ 도움말',
        
        # NEW: Partner FSM
        'add_card': '➕ 카드 추가',
        'my_cards': '📋 내 카드',
        'card_status_draft': '📝 초안',
        'card_status_pending': '⏳ 대기중',
        'card_status_approved': '✅ 승인됨',
        'card_status_published': '🎉 게시됨',
        'card_status_rejected': '❌ 거부됨',
        'card_status_archived': '🗂️ 보관됨',
        
        # NEW: Common actions
        'cancel': '❌ 취소',
        'skip': '⏭️ 건너뛰기',
        'back': '🔙 뒤로',
        'next': '➡️ 다음',
        'edit': '✏️ 편집',
        'delete': '🗑️ 삭제',
        'save': '💾 저장',
        
        # NEW: Card renderer
        'contact_info': '📞 연락처',
        'address_info': '📍 주소',
        'discount_info': '🎫 할인',
        'show_on_map': '🗺️ 지도에서 보기',
        'create_qr': '📱 QR 생성',
        'call_business': '📞 연락하기',
        'book_service': '📅 예약하기',
        
        # NEW: Help
        'help_main': '카르마 봇입니다. 메뉴를 사용하여 탐색하세요.',
        'catalog_empty': '이 카테고리에는 아직 아무것도 없습니다.',
        'catalog_error': '카탈로그를 로드하는 중 오류가 발생했습니다. 나중에 다시 시도하십시오.',
        'start_welcome': '👋 안녕하세요! 메인 메뉴에서 언어와 카테고리를 선택하세요.',
        'main_menu_title': '메인 메뉴: 아래 버튼을 사용하세요.',
        'language_updated': '언어 업데이트됨',
        'choose_city': '지역을 선택하세요:',
        'city_updated': '도시/지역 업데이트됨',
        'city_selected': '지역이 선택되었습니다. 계속 검색할 수 있습니다.',
        'policy_accepted': '정책 동의함',
        'unhandled_message': '이해할 수 없습니다. 메뉴 버튼을 사용해 주세요.',
        
        # NEW: Profile
        'profile_main': '👤 **프로필**',
        'profile_stats': '📊 통계',
        'profile_settings': '⚙️ 설정',
        'cards_count': '카드',
        'views_count': '조회수',
        'qr_scans': 'QR 스캔',

        # NEW: Category Menu (v2)
        'category_restaurants': '🍽 레스토랑',
        'category_spa': '🧖‍♀️ 스파',
        'category_transport': '🚗 교통',
        'category_hotels': '🏨 호텔',
        'category_tours': '🚶‍♂️ 투어',
        'transport_bikes': '🛵 오토바이',
        'transport_cars': '🚘 자동차',
        'transport_bicycles': '🚲 자전거',
        'tours_group': '👥 그룹',
        'tours_private': '🧑‍🤝‍🧑 개인',
        'back_to_categories': '◀️ 뒤로',
        'catalog_found': '찾음',
        'catalog_page': '페이지',
        'catalog_empty_sub': '📭 이 하위 카테고리에는 아직 장소가 없습니다.',
        'transport_choose': '교통 수단을 선택하십시오:',
        'tours_choose': '투어 유형을 선택하십시오:',
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
