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
        # v4.2.4 minimal labels
        'menu.categories': '🗂️ 카테고리',
        'menu.invite_friends': '👥 친구 초대',
        'menu.favorites': '⭐ 즐겨찾기',
        'menu.become_partner': '👨‍💼 파트너 되기',
        'menu.help': '❓ 도움말',
        'menu.profile': '👤 프로필',
        'invite.my_link': '내 링크',
        'invite.invited': '초대한 사용자',
        'invite.earnings': '수익',
        # Existing keys
        'back_to_main_menu': '메인 메뉴로 돌아가기🏘',
        'back_to_categories': '⬅️ 카테고리로',
        'choose_category': '🗂️ 카테고리',
        'show_nearest': '📍 가까운 매장',
        
        # Menu keys
        'menu.invite_friends': '👥 친구 초대',
        'menu.favorites': '⭐ 즐겨찾기',
        
        # User profile
        'cabinet.user_profile': '👤 내 정보\n\n💎 포인트: {points}\n🏆 레벨: {level}\n\n아래 메뉴를 사용하여 프로필을 관리하세요',
        'cabinet.user_points': '💰 내 포인트: {points}\n\n파트너사에서 사용할 수 있습니다',
        'cabinet.history_header': '📜 거래 내역:',
        'cabinet.partner_profile': '👤 파트너 프로필\n\n✅ 승인된 카드: {approved_cards}\n👀 총 조회수: {total_views}\n📊 총 스캔 수: {total_sc캉}',
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
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ 요리 종류를 선택하세요:',
        'filter_asia': '🌶️ 아시아',
        'filter_europe': '🍝 유럽',
        'filter_street': '🌭 길거리 음식',
        'filter_vege': '🥗 채식',
        'filter_all': '🔍 전체',
        
        # SPA services
        'spa_choose': '🧖‍♀️ SPA 서비스를 선택하세요:',
        'spa_salon': '💅 미용실',
        'spa_massage': '💆‍♀️ 마사지',
        'spa_sauna': '🧖‍♂️ 사우나',
        
        # Transport
        'transport_bikes': '🛵 바이크',
        'transport_cars': '🚘 자동차',
        'transport_bicycles': '🚲 자전거',
        
        # Categories
        'category_shops_services': '🛍️ 상점 및 서비스',
        
        # Hotels
        'hotels_hotels': '🏨 호텔',
        'hotels_apartments': '🏠 아파트',
        'hotels_choose': '🏨 숙박 유형을 선택하세요:',
        
        # Shops
        'shops_shops': '🛍️ 상점',
        'shops_services': '🔧 서비스',
        'shops_choose': '🛍️ 상점 유형을 선택하세요:',
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
        'policy_message': '''🔒 개인정보 처리방침\n\n서비스를 이용하기 전에 개인정보 처리방침에 동의해 주세요.\n\n계속하시면 개인정보 처리방침에 동의하는 것으로 간주됩니다.''',
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
        'failed': '실패했습니다.',
        
        # Errors
        'menu_error': '메인 메뉴로 돌아갈 수 없습니다. 나중에 다시 시도해주세요.'
    },
    'vi': {
        # v4.2.4 minimal labels
        'menu.categories': '🗂️ Danh mục',
        'menu.invite_friends': '👥 Mời bạn bè',
        'menu.favorites': '⭐ Yêu thích',
        'menu.become_partner': '👨‍💼 Trở thành đối tác',
        'menu.help': '❓ Hỗ trợ',
        'menu.profile': '👤 Hồ sơ',
        'invite.my_link': 'Liên kết của tôi',
        'invite.invited': 'Đã mời',
        'invite.earnings': 'Thu nhập',
        # Existing keys
        'back_to_main_menu': 'Về menu chính🏘',
        'back_to_categories': '⬅️ Về danh mục',
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
        
        # Policy
        'policy_text': '''Vui lòng đồng ý với chính sách bảo mật.\n\nTiếp tục có nghĩa là bạn đồng ý với chính sách bảo mật.''',
        'policy_message': '''🔒 Chính sách bảo mật\n\nVui lòng đồng ý với chính sách bảo mật trước khi sử dụng dịch vụ.\n\nTiếp tục có nghĩa là bạn đồng ý với chính sách bảo mật.''',
        'policy_accept': '✅ Đồng ý',
        'policy_view': '📄 Chính sách bảo mật',
        'policy_url': '/policy',
        
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
        'failed': 'Thất bại!',
        
        # SPA services
        'spa_choose': '🧖‍♀️ Chọn dịch vụ SPA:',
        'spa_salon': '💅 Salon làm đẹp',
        'spa_massage': '💆‍♀️ Massage',
        'spa_sauna': '🧖‍♂️ Xông hơi',
        
        # Transport
        'transport_bikes': '🛵 Xe máy',
        'transport_cars': '🚘 Ô tô',
        'transport_bicycles': '🚲 Xe đạp',
        
        # Hotels
        'hotels_hotels': '🏨 Khách sạn',
        'hotels_apartments': '🏠 Căn hộ',
        'hotels_choose': '🏨 Chọn loại chỗ ở:',
        
        # Shops
        'shops_shops': '🛍️ Cửa hàng',
        'shops_services': '🔧 Dịch vụ',
        'shops_choose': '🛍️ Chọn loại cửa hàng:',
        
        # Errors
        'menu_error': 'Không thể quay lại menu chính. Vui lòng thử lại sau.'
    },
    'ru': {
        # v4.2.4 menu keys
        'menu.categories': '🗂️ Категории',
        'menu.invite_friends': '👥 Пригласить друзей',
        'menu.favorites': '⭐ Избранные',
        'menu.become_partner': '👨‍💼 Стать парнером',
        'menu.help': '❓ Помощь',
        'menu.profile': '👤 Личный кабинет',
        # v4.2.4 invite submenu
        'invite.my_link': '🔗 Моя ссылка',
        'invite.invited': '📋 Приглашённые',
        'invite.earnings': '💵 Доходы',
        'invite.copied': 'Ссылка скопирована',
        'invite.empty': 'У вас пока нет приглашённых',
        # v4.2.4 commands
        'commands.start': 'Перезапуск',
        'commands.add_partner': 'Добавить парнер',
        'commands.webapp': 'Открыть WebApp',
        'commands.city': 'Сменить город',
        'commands.help': 'Помощь/FAQ',
        'commands.policy': 'Политика конфиденциальности',
        'commands.clear_cache': 'Очистить кэш (только админ)',
        # v4.2.4 categories labels
        'categories.restaurants': '🍽️ Рестораны и кафе',
        'categories.spa': '🧖‍♀️ SPA и массаж',
        'categories.transport': '🏍️ Аренда байков',
        'categories.hotels': '🏨 Отели',
        'categories.tours': '🚶‍♂️ Экскурсии',
        'categories.shops': '🛍️ Магазины и услуги',
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ Выберите тип кухни:',
        'filter_asia': '🌶️ Азиатская',
        'filter_europe': '🍝 Европейская',
        'filter_street': '🌭 Уличная еда',
        'filter_vege': '🥗 Вегетарианская',
        'filter_all': '🔍 Все',
        
        # SPA services
        'spa_choose': '🧖‍♀️ Выберите SPA услугу:',
        'spa_salon': '💅 Салон красоты',
        'spa_massage': '💆‍♀️ Массаж',
        'spa_sauna': '🧖‍♂️ Сауна',
        
        # Transport
        'transport_bikes': '🛵 Байки',
        'transport_cars': '🚘 Машины',
        'transport_bicycles': '🚲 Велосипеды',
        
        # Categories
        'category_shops_services': '🛍️ Магазины и услуги',
        
        # Hotels
        'hotels_hotels': '🏨 Отели',
        'hotels_apartments': '🏠 Апартаменты',
        'hotels_choose': '🏨 Выберите тип размещения:',
        
        # Shops
        'shops_shops': '🛍️ Магазины',
        'shops_services': '🔧 Услуги',
        'shops_choose': '🛍️ Выберите тип магазина:',
        
        # Keyboard buttons
        'keyboard.categories': '🗂️ Категории',
        'keyboard.nearest': '📍 Ближайшие',
        'keyboard.help': '❓ Помощь',
        'keyboard.choose_language': '🌐 Сменить язык',
        
        # Policy
        'policy_text': '''Пожалуйста, согласитесь с политикой конфиденциальности.\n\nПродолжение означает согласие с политикой конфиденциальности.''',
        'policy_message': '''🔒 Политика конфиденциальности\n\nПожалуйста, согласитесь с политикой конфиденциальности перед использованием сервиса.\n\nПродолжение означает согласие с политикой конфиденциальности.''',
        'policy_accept': '✅ Согласен',
        'policy_decline': '❌ Отклонить',
        'policy_view': '📄 Политика обработки персональных данных',
        'policy_url': '/policy',
        
        # Errors
        'menu_error': 'Не удалось вернуться в главное меню. Пожалуйста, попробуйте позже.',
        
        # Welcome message
        'welcome_message': '''{name} 👋 Добро пожаловать в Karma System! 

✨ Получай эксклюзивные скидки и предложения через QR-код в удобных категориях:
🍽️ Рестораны и кафе
🧖‍♀️ SPA и массаж
🏍️ Аренда байков
🏨 Отели
🚶‍♂️ Экскурсии
🛍️ Магазины и услуги  

А если ты владелец бизнеса — присоединяйся к нам как партнёр и подключай свою систему лояльности! 🚀

Начни экономить прямо сейчас — выбирай категорию и получай свои скидки!

Продолжая пользоваться ботом вы соглашаетесь с политикой обработки персональных данных.''',
        
        # Navigation
        'back_to_main': '🏠 Главное меню',
        'back_to_main_menu': '◀️ Назад',
        'back_to_categories': '⬅️ К категориям',
    },
    'en': {
        # v4.2.4 minimal labels
        'menu.categories': '🗂️ Categories',
        'menu.invite_friends': '👥 Invite friends',
        'menu.favorites': '⭐ Favorites',
        'menu.become_partner': '👨‍💼 Become a partner',
        'menu.help': '❓ Help',
        'menu.profile': '👤 Profile',
        'invite.my_link': '🔗 My link',
        'invite.invited': '📋 Invited',
        'invite.earnings': '💵 Earnings',
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ Choose cuisine type:',
        'filter_asia': '🌶️ Asian',
        'filter_europe': '🍝 European',
        'filter_street': '🌭 Street food',
        'filter_vege': '🥗 Vegetarian',
        'filter_all': '🔍 All',
        
        # SPA services
        'spa_choose': '🧖‍♀️ Choose SPA service:',
        'spa_salon': '💅 Beauty salon',
        'spa_massage': '💆‍♀️ Massage',
        'spa_sauna': '🧖‍♂️ Sauna',
        
        # Transport
        'transport_bikes': '🛵 Bikes',
        'transport_cars': '🚘 Cars',
        'transport_bicycles': '🚲 Bicycles',
        
        # Categories
        'category_shops_services': '🛍️ Shops and services',
        
        # Hotels
        'hotels_hotels': '🏨 Hotels',
        'hotels_apartments': '🏠 Apartments',
        'hotels_choose': '🏨 Choose accommodation type:',
        
        # Shops
        'shops_shops': '🛍️ Shops',
        'shops_services': '🔧 Services',
        'shops_choose': '🛍️ Choose shop type:',
        'shops_choose': '🛍️ Choose shop type:',
        
        # Keyboard buttons
        'keyboard.categories': '🗂️ Categories',
        'keyboard.nearest': '📍 Nearest',
        'keyboard.help': '❓ Help',
        'keyboard.choose_language': '🌐 Change language',
        
        # Policy
        'policy_text': '''Please agree to the privacy policy.\n\nContinuing means you agree to the privacy policy.''',
        'policy_message': '''🔒 Privacy Policy\n\nPlease agree to the privacy policy before using the service.\n\nContinuing means you agree to the privacy policy.''',
        'policy_accept': '✅ I agree',
        'policy_view': '📄 Privacy Policy',
        'policy_url': '/policy',
        
        # Errors
        'menu_error': 'Failed to return to main menu. Please try again later.',
        
        # Navigation
        'back_to_main_menu': '◀️ Back',
        'back_to_categories': '⬅️ To categories',
        
        # Menu keys
        'menu.invite_friends': '👥 Invite friends',
        'menu.favorites': '⭐ Favorites',
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
