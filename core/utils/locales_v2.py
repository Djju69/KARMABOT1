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
    },
    
    'en': {
        # Existing keys (preserved)
        'back_to_main': 'Back to main menu🏘',
        'choose_category': '🗂️ Categories',
        'show_nearest': '📍 Show nearest',
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
        'help_main': '''❓ **Bot Help**

🗂️ **Categories** - browse businesses by type
👤 **Profile** - manage your cards
📍 **Show nearest** - find nearby places
🌆 **By districts** - choose by location
🌐 **Language** - change interface language

**For partners:**
/add_card - add new business card
/my_cards - view your cards

**Support:** @support_bot''',
        
        # NEW: Profile
        'profile_main': '👤 **Profile**',
        'profile_stats': '📊 Statistics',
        'profile_settings': '⚙️ Settings',
        'cards_count': 'Cards',
        'views_count': 'Views',
        'qr_scans': 'QR scans',
    },
    
    'vi': {
        # Existing keys (preserved)
        'back_to_main': 'Về menu chính🏘',
        'choose_category': '🗂️ Danh mục',
        'show_nearest': '📍 Hiển thị gần nhất',
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
        'help_main': '''❓ **Trợ giúp Bot**

🗂️ **Danh mục** - duyệt doanh nghiệp theo loại
👤 **Hồ sơ** - quản lý thẻ của bạn
📍 **Hiển thị gần nhất** - tìm địa điểm gần
🌆 **Theo quận** - chọn theo vị trí
🌐 **Ngôn ngữ** - thay đổi ngôn ngữ

**Cho đối tác:**
/add_card - thêm thẻ doanh nghiệp mới
/my_cards - xem thẻ của bạn

**Hỗ trợ:** @support_bot''',
        
        # NEW: Profile
        'profile_main': '👤 **Hồ sơ**',
        'profile_stats': '📊 Thống kê',
        'profile_settings': '⚙️ Cài đặt',
        'cards_count': 'Thẻ',
        'views_count': 'Lượt xem',
        'qr_scans': 'Quét QR',
    },
    
    'ko': {
        # Existing keys (preserved)
        'back_to_main': '메인 메뉴로🏘',
        'choose_category': '🗂️ 카테고리',
        'show_nearest': '📍 가까운 곳 보기',
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
        'help_main': '''❓ **봇 도움말**

🗂️ **카테고리** - 유형별 업체 보기
👤 **프로필** - 카드 관리
📍 **가까운 곳 보기** - 근처 장소 찾기
🌆 **지역별** - 위치별 선택
🌐 **언어** - 인터페이스 언어 변경

**파트너용:**
/add_card - 새 비즈니스 카드 추가
/my_cards - 내 카드 보기

**지원:** @support_bot''',
        
        # NEW: Profile
        'profile_main': '👤 **프로필**',
        'profile_stats': '📊 통계',
        'profile_settings': '⚙️ 설정',
        'cards_count': '카드',
        'views_count': '조회수',
        'qr_scans': 'QR 스캔',
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

# Save extended translations to file for persistence
def save_translations_to_file(filepath: str = "core/utils/translations_v2.json"):
    """Save translations to JSON file"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(translations_v2, f, ensure_ascii=False, indent=2)

# Load from file if exists (for runtime updates)
def load_translations_from_file(filepath: str = "core/utils/translations_v2.json"):
    """Load translations from JSON file if exists"""
    global translations_v2, translations
    
    if Path(filepath).exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                translations_v2.update(loaded)
                translations = translations_v2
        except Exception as e:
            print(f"Warning: Failed to load translations from {filepath}: {e}")

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

# Auto-load on import (JSON dir has precedence, then single file)
load_translations_from_dir()
load_translations_from_file()
