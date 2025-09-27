"""
Enhanced localization with backward compatibility
Extends existing translations without breaking changes
"""
from typing import Dict, Any
import json
from pathlib import Path

# Alias mapping for deprecated keys (backward compatibility)
ALIASES = {
    "back_to_main": "menu.back_to_main_menu",
    "back_to_main_menu": "menu.back_to_main_menu", 
    "back_simple": "common.back_simple",
    "back_to_partner_menu": "partner.back_to_partner_menu",
    "profile_settings": "keyboard.profile_settings"
}

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
        'back_admin': '◀️ 관리자 메뉴로',
        'back_partner': '◀️ 파트너 메뉴로',
        'invite.my_link': '내 링크',
        'invite.invited': '초대한 사용자',
        'invite.earnings': '수익',
        # Existing keys
        'back_to_main_menu': '◀️ 뒤로',
        'back_to_categories': '⬅️ 카테고리로',
        
        # Admin menu buttons
        'admin_menu_queue': '📋 검토 대기열',
        'admin_menu_search': '🔍 검색',
        'admin_menu_reports': '📊 보고서',
        
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
        'menu_scan_qr': '🧾 QR 스캔',
        'keyboard.statistics': '📈 통계',
        'keyboard.support': '🆘 지원',
        'keyboard.confirm': '✅ 확인',
        'keyboard.cancel': '❌ 취소',
        'keyboard.enter_amount': '💳 금액 입력',
        'keyboard.prev_page': '⬅️ 이전',
        'keyboard.next_page': '다음 ➡️',
        'keyboard.become_partner': '👨‍💼 파트너가되기',
        'choose_language': '🌐 언어',
        'choose_language_text': '언어를 선택하세요:',
        'request_location': '📍 가장 가까운 매장을 찾기 위해 위치를 공유해주세요:',
        'nearest_places_found': '📍 <b>가장 가까운 매장:</b>\n\n',
        'no_places_found': '❌ 근처에 매장이 없습니다. 다른 지역을 시도해보세요.',
        'location_error': '❌ 위치 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        'catalog_found': '발견된 매장',
        'catalog_page': '페이지',
        'catalog_empty_sub': '❌ 이 하위 카테고리에는 아직 매장이 없습니다.',
        'catalog_error': '❌ 카탈로그 로드 오류. 나중에 다시 시도해주세요.',
        'districts_found': '🌆 <b>지역별 매장:</b>\n\n',
        'no_districts_found': '❌ 지역별 매장을 찾을 수 없습니다.',
        'districts_error': '❌ 지역 로드 오류. 나중에 다시 시도해주세요.',
        'qr_codes': '📱 QR 코드',
        'no_qr_codes': '📱 아직 QR 코드가 없습니다.\n\n파트너 매장에서 할인을 받기 위해 QR 코드를 생성하세요.',
        'qr_codes_list': '📱 <b>귀하의 QR 코드:</b>\n\n',
        'create_qr_code': '📱 QR 코드 생성',
        'my_qr_codes': '📋 내 QR 코드',
        'qr_code_created': '📱 <b>QR 코드가 생성되었습니다!</b>\n\n🆔 코드: {qr_id}\n💎 할인: 10%\n📅 유효기간: 30일\n\n파트너 매장에서 이 QR 코드를 보여주시면 할인을 받으실 수 있습니다.',
        'qr_codes_error': '❌ QR 코드 로드 오류. 나중에 다시 시도해주세요.',
        'qr_create_error': '❌ QR 코드 생성 오류. 나중에 다시 시도해주세요.',
        'choose_district': '🌆 지역별',
        
        # Keyboard menu items
        'keyboard.categories': '🗂️ 카테고리',
        'keyboard.nearest': '📍 가까운 매장',
        'keyboard.help': '❓ 도움말',
        'keyboard.choose_language': '🌐 언어 변경',
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ 요리 종류를 선택하세요:',
        'restaurants_show_all': '📋 전체 보기',
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
        'transport_choose': '🚗 교통수단을 선택하세요',
        'transport_bikes': '🛵 바이크',
        'transport_cars': '🚘 자동차',
        'transport_bicycles': '🚲 자전거',
        
        # Categories
        'category_shops_services': '🛍️ 상점 및 서비스',
        
        # Tours
        'tours_choose': '🗺️ 투어를 선택하세요:',
        'tours_group': '👥 그룹 투어',
        'tours_private': '👤 개인 투어',
        
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
        'policy_text': '''🔒 <b>개인정보 처리방침</b>

<b>1. 일반 조항</b>
본 개인정보 처리방침은 Karma System 봇 사용자의 개인정보 처리 절차를 정의합니다.

<b>2. 수집하는 데이터</b>
• 텔레그램 사용자 ID
• 사용자명 및 이름
• 언어 설정
• 봇 상호작용 데이터
• 위치 정보 ("근처" 기능 사용 시)

<b>3. 처리 목적</b>
• 봇 서비스 제공
• 콘텐츠 개인화
• 사용 분석
• 서비스 품질 향상

<b>4. 데이터 전송</b>
귀하의 데이터는 법률에 의해 요구되는 경우를 제외하고 제3자에게 전송되지 않습니다.

<b>5. 보안</b>
귀하의 개인정보를 보호하기 위해 모든 필요한 조치를 취합니다.

<b>6. 귀하의 권리</b>
귀하는 귀하의 개인정보에 대한 접근, 수정 및 삭제 권리가 있습니다.

<b>7. 연락처</b>
개인정보 처리에 대한 문의사항은 봇 관리자에게 연락하세요.

<i>마지막 업데이트: 2025.09.07</i>''',
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
        
        # Tariff system
        'tariffs.title': '💰 사용 가능한 파트너십 요금제',
        'tariffs.for_partners': '비즈니스에 적합한 요금제를 선택하세요:',
        'tariffs.for_users': '파트너를 위한 요금제 정보:',
        'tariffs.become_partner': '🤝 파트너가 되고 싶으신가요?',
        'tariffs.become_partner_text': '파트너는 요금제 관리에 액세스할 수 있으며 비즈니스에 적합한 계획을 선택할 수 있습니다.',
        'tariffs.apply_instruction': '📝 파트너십 신청을 위해 메인 메뉴의 \'파트너십\' 섹션을 사용하세요.',
        'tariffs.free_starter': 'FREE STARTER',
        'tariffs.business': 'BUSINESS',
        'tariffs.enterprise': 'ENTERPRISE',
        'tariffs.price': '가격',
        'tariffs.free': '무료',
        'tariffs.month': '월',
        'tariffs.transactions_limit': '거래 한도',
        'tariffs.per_month': '월당',
        'tariffs.unlimited': '무제한',
        'tariffs.commission': '수수료',
        'tariffs.analytics': '분석',
        'tariffs.priority_support': '우선 지원',
        'tariffs.api_access': 'API 액세스',
        'tariffs.custom_integrations': '맞춤형 통합',
        'tariffs.dedicated_manager': '전담 관리자',
        'tariffs.enabled': '활성화됨',
        'tariffs.disabled': '비활성화됨',
        'tariffs.description': '설명',
        'tariffs.current_tariff': '현재 요금제',
        'tariffs.switch_tariff_button': '🔄 이 요금제로 전환',
        'tariffs.help_button': '❓ 요금제 도움말',
        'tariffs.become_partner_button': '🤝 파트너 되기',
        'tariffs.back_to_tariffs_list': '◀️ 요금제로 돌아가기',
        'tariffs.confirm_switch_text': '{tariff_name} 요금제로 전환하시겠습니까?',
        'tariffs.switch_success': '✅ {tariff_name} 요금제로 성공적으로 전환되었습니다!',
        'tariffs.switch_fail': '❌ 요금제 전환에 실패했습니다. 나중에 다시 시도해주세요.',
        'tariffs.help_text': '❓ 요금제 도움말\n\n💰 FREE STARTER - 시작하기 위한 무료 요금제\n• 월 15회 거래\n• 12% 수수료\n• 기본 기능\n\n💼 BUSINESS - 성장하는 비즈니스를 위한\n• 월 100회 거래\n• 6% 수수료\n• 분석 + 우선 지원\n\n🏢 ENTERPRISE - 대기업을 위한\n• 무제한 거래\n• 4% 수수료\n• 모든 기능: API, 통합, 관리자\n\n💡 요금제 변경 방법:\n1. 적합한 요금제 선택\n2. \'이 요금제로 전환\' 클릭\n3. 변경 확인\n\n❓ 도움이 필요하신가요? 지원팀에 문의하세요!',
        'tariffs.no_tariffs': '❌ 요금제가 일시적으로 사용할 수 없습니다. 나중에 다시 시도해주세요.',
        'tariffs.error_no_id': '❌ 오류: 요금제 ID가 지정되지 않음',
        'tariffs.not_found': '❌ 요금제를 찾을 수 없음',
        'tariffs.current_tariff_info': '현재 요금제입니다',
        'tariffs.only_partners': '❌ 파트너만 요금제를 관리할 수 있습니다',
        'tariffs.only_partners_change': '❌ 파트너만 요금제를 변경할 수 있습니다',
        
        # Language selection
        'language_ru': '🇷🇺 Русский',
        'language_en': '🇺🇸 English',
        'language_vi': '🇻🇳 Tiếng Việt',
        'language_ko': '🇰🇷 한국어',
        'choose_language': '🌐 언어 선택',
        'language_changed': '✅ 언어가 {language}로 변경되었습니다',
        
        # Errors
        'menu_error': '메인 메뉴로 돌아갈 수 없습니다. 나중에 다시 시도해주세요.',
        
        # Commands
        'commands.start': '재시작',
        'commands.add_card': '파트너 추가',
        'commands.webapp': 'WebApp 열기',
        'commands.city': '도시 변경',
        'commands.help': '도움말/FAQ',
        'commands.policy': '개인정보 보호정책',
        'commands.clear_cache': '캐시 지우기 (관리자만)',
        'commands.tariffs': '요금제 보기',
    },
    'vi': {
        # v4.2.4 minimal labels
        'menu.categories': '🗂️ Danh mục',
        'menu.invite_friends': '👥 Mời bạn bè',
        'menu.favorites': '⭐ Yêu thích',
        'menu.become_partner': '👨‍💼 Trở thành đối tác',
        'menu.help': '❓ Hỗ trợ',
        'menu.profile': '👤 Hồ sơ',
        'back_admin': '◀️ Về menu quản trị',
        'back_partner': '◀️ Về menu đối tác',
        'invite.my_link': 'Liên kết của tôi',
        'invite.invited': 'Đã mời',
        'invite.earnings': 'Thu nhập',
        # Existing keys
        'back_to_main_menu': '◀️ Quay lại',
        'back_to_categories': '⬅️ Về danh mục',
        'ai_assistant': '🤖 Trợ lý AI',
        'dashboard_admin': '📊 Bảng điều khiển: Duyệt(0) | Thông báo(0)',
        'dashboard_superadmin': '📊 Bảng điều khiển: Duyệt(0) | Thông báo(0) | Hệ thống(OK)',
        'partners': '🤝 Đối tác',
        'newsletter': '📧 Bản tin',
        'btn.partner.add_card': '➕ Thêm thẻ',
        
        # Admin menu buttons
        'admin_menu_queue': '📋 Hàng đợi kiểm duyệt',
        'admin_menu_search': '🔍 Tìm kiếm',
        'admin_menu_reports': '📊 Báo cáo',
        
        'choose_category': '🗂️ Danh mục',
        'show_nearest': '📍 Gần nhất',
        'choose_language': '🌐 Ngôn ngữ',
        'choose_language_text': 'Chọn ngôn ngữ:',
        'request_location': '📍 Chia sẻ vị trí của bạn để tìm các địa điểm gần nhất:',
        'nearest_places_found': '📍 <b>Các địa điểm gần nhất:</b>\n\n',
        'no_places_found': '❌ Không tìm thấy địa điểm nào gần đây. Hãy thử khu vực khác.',
        'location_error': '❌ Lỗi xử lý vị trí. Vui lòng thử lại.',
        'catalog_found': 'Tìm thấy địa điểm',
        'catalog_page': 'Trang',
        'catalog_empty_sub': '❌ Chưa có địa điểm nào trong danh mục con này.',
        'catalog_error': '❌ Lỗi tải danh mục. Vui lòng thử lại sau.',
        'districts_found': '🌆 <b>Địa điểm theo khu vực:</b>\n\n',
        'no_districts_found': '❌ Không tìm thấy địa điểm theo khu vực.',
        'districts_error': '❌ Lỗi tải khu vực. Vui lòng thử lại sau.',
        'qr_codes': '📱 Mã QR',
        'no_qr_codes': '📱 Bạn chưa có mã QR nào.\n\nTạo mã QR để nhận giảm giá tại các đối tác.',
        'qr_codes_list': '📱 <b>Mã QR của bạn:</b>\n\n',
        'create_qr_code': '📱 Tạo mã QR',
        'my_qr_codes': '📋 Mã QR của tôi',
        'qr_code_created': '📱 <b>Mã QR đã được tạo!</b>\n\n🆔 Mã: {qr_id}\n💎 Giảm giá: 10%\n📅 Có hiệu lực: 30 ngày\n\nHiển thị mã QR này tại các đối tác để nhận giảm giá.',
        'qr_codes_error': '❌ Lỗi tải mã QR. Vui lòng thử lại sau.',
        'qr_create_error': '❌ Lỗi tạo mã QR. Vui lòng thử lại sau.',
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
        'menu_scan_qr': '🧾 Quét QR',
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
        'back': '◀️ Назад в главное меню',
        'next': '➡️ Tiếp',
        'edit': '✏️ Chỉnh sửa',
        'delete': '🗑️ Xóa',
        'save': '💾 Lưu',
        
        # Policy
        'policy_text': '''🔒 <b>CHÍNH SÁCH BẢO MẬT</b>

<b>1. QUY ĐỊNH CHUNG</b>
Chính sách Bảo mật này xác định thủ tục xử lý dữ liệu cá nhân của người dùng bot Karma System.

<b>2. DỮ LIỆU CHÚNG TÔI THU THẬP</b>
• ID người dùng Telegram
• Tên người dùng và tên
• Cài đặt ngôn ngữ
• Dữ liệu tương tác với bot
• Thông tin vị trí (khi sử dụng tính năng "Gần đây")

<b>3. MỤC ĐÍCH XỬ LÝ</b>
• Cung cấp dịch vụ bot
• Cá nhân hóa nội dung
• Phân tích sử dụng
• Cải thiện chất lượng dịch vụ

<b>4. CHUYỂN GIAO DỮ LIỆU</b>
Dữ liệu của bạn không được chuyển giao cho bên thứ ba, trừ trường hợp pháp luật yêu cầu.

<b>5. BẢO MẬT</b>
Chúng tôi thực hiện mọi biện pháp cần thiết để bảo vệ dữ liệu cá nhân của bạn.

<b>6. QUYỀN CỦA BẠN</b>
Bạn có quyền truy cập, sửa đổi và xóa dữ liệu cá nhân của mình.

<b>7. LIÊN HỆ</b>
Đối với các câu hỏi về xử lý dữ liệu cá nhân, hãy liên hệ với quản trị viên bot.

<i>Cập nhật lần cuối: 07/09/2025</i>''',
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
        'transport_choose': '🚗 Chọn phương tiện giao thông',
        'transport_bikes': '🛵 Xe máy',
        'transport_cars': '🚘 Ô tô',
        'transport_bicycles': '🚲 Xe đạp',
        
        # Tours
        'tours_choose': '🗺️ Chọn tour:',
        'tours_group': '👥 Tour nhóm',
        'tours_private': '👤 Tour riêng',
        
        # Hotels
        'hotels_hotels': '🏨 Khách sạn',
        'hotels_apartments': '🏠 Căn hộ',
        'hotels_choose': '🏨 Chọn loại chỗ ở:',
        
        # Shops
        'shops_shops': '🛍️ Cửa hàng',
        'shops_services': '🔧 Dịch vụ',
        'shops_choose': '🛍️ Chọn loại cửa hàng:',
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ Chọn loại ẩm thực:',
        'restaurants_show_all': '📋 Xem tất cả',
        'filter_asia': '🌶️ Châu Á',
        'filter_europe': '🍝 Châu Âu',
        'filter_street': '🌭 Đồ ăn đường phố',
        'filter_vege': '🥗 Chay',
        'filter_all': '🔍 Tất cả',
        
        # Tariff system
        'tariffs.title': '💰 Gói đối tác có sẵn',
        'tariffs.for_partners': 'Chọn gói phù hợp cho doanh nghiệp của bạn:',
        'tariffs.for_users': 'Thông tin về gói cho đối tác:',
        'tariffs.become_partner': '🤝 Muốn trở thành đối tác?',
        'tariffs.become_partner_text': 'Đối tác có quyền truy cập quản lý gói và có thể chọn kế hoạch phù hợp cho doanh nghiệp của họ.',
        'tariffs.apply_instruction': '📝 Để đăng ký làm đối tác, sử dụng phần \'Đối tác\' trong menu chính.',
        'tariffs.free_starter': 'FREE STARTER',
        'tariffs.business': 'BUSINESS',
        'tariffs.enterprise': 'ENTERPRISE',
        'tariffs.price': 'Giá',
        'tariffs.free': 'Miễn phí',
        'tariffs.month': 'tháng',
        'tariffs.transactions_limit': 'Giới hạn giao dịch',
        'tariffs.per_month': 'mỗi tháng',
        'tariffs.unlimited': 'Không giới hạn',
        'tariffs.commission': 'Hoa hồng',
        'tariffs.analytics': 'Phân tích',
        'tariffs.priority_support': 'Hỗ trợ ưu tiên',
        'tariffs.api_access': 'Truy cập API',
        'tariffs.custom_integrations': 'Tích hợp tùy chỉnh',
        'tariffs.dedicated_manager': 'Quản lý chuyên dụng',
        'tariffs.enabled': 'Đã bật',
        'tariffs.disabled': 'Đã tắt',
        'tariffs.description': 'Mô tả',
        'tariffs.current_tariff': 'Gói hiện tại của bạn',
        'tariffs.switch_tariff_button': '🔄 Chuyển sang gói này',
        'tariffs.help_button': '❓ Trợ giúp gói',
        'tariffs.become_partner_button': '🤝 Trở thành đối tác',
        'tariffs.back_to_tariffs_list': '◀️ Quay lại gói',
        'tariffs.confirm_switch_text': 'Bạn có chắc chắn muốn chuyển sang gói {tariff_name}?',
        'tariffs.switch_success': '✅ Bạn đã chuyển thành công sang gói {tariff_name}!',
        'tariffs.switch_fail': '❌ Không thể chuyển gói. Vui lòng thử lại sau.',
        'tariffs.help_text': '❓ Trợ giúp gói\n\n💰 FREE STARTER - Gói miễn phí để bắt đầu\n• 15 giao dịch mỗi tháng\n• Hoa hồng 12%\n• Tính năng cơ bản\n\n💼 BUSINESS - Cho doanh nghiệp đang phát triển\n• 100 giao dịch mỗi tháng\n• Hoa hồng 6%\n• Phân tích + hỗ trợ ưu tiên\n\n🏢 ENTERPRISE - Cho doanh nghiệp lớn\n• Giao dịch không giới hạn\n• Hoa hồng 4%\n• Tất cả tính năng: API, tích hợp, quản lý\n\n💡 Cách thay đổi gói:\n1. Chọn gói phù hợp\n2. Nhấn \'Chuyển sang gói này\'\n3. Xác nhận thay đổi\n\n❓ Cần trợ giúp? Liên hệ hỗ trợ!',
        'tariffs.no_tariffs': '❌ Gói tạm thời không khả dụng. Vui lòng thử lại sau.',
        'tariffs.error_no_id': '❌ Lỗi: không chỉ định ID gói',
        'tariffs.not_found': '❌ Không tìm thấy gói',
        'tariffs.current_tariff_info': 'Đây là gói hiện tại của bạn',
        'tariffs.only_partners': '❌ Chỉ đối tác mới có thể quản lý gói',
        'tariffs.only_partners_change': '❌ Chỉ đối tác mới có thể thay đổi gói',
        
        # Language selection
        'language_ru': '🇷🇺 Русский',
        'language_en': '🇺🇸 English',
        'language_vi': '🇻🇳 Tiếng Việt',
        'language_ko': '🇰🇷 한국어',
        'choose_language': '🌐 Chọn ngôn ngữ',
        'language_changed': '✅ Đã thay đổi ngôn ngữ thành {language}',
        
        # Errors
        'menu_error': 'Không thể quay lại menu chính. Vui lòng thử lại sau.',
        
        # Commands
        'commands.start': 'Khởi động lại',
        'commands.add_card': 'Thêm đối tác',
        'commands.webapp': 'Mở WebApp',
        'commands.city': 'Đổi thành phố',
        'commands.help': 'Trợ giúp/FAQ',
        'commands.policy': 'Chính sách bảo mật',
        'commands.clear_cache': 'Xóa cache (chỉ admin)',
        'commands.tariffs': 'Xem gói cước',
    },
    'ru': {
        # v4.2.4 menu keys
        'menu.categories': '🗂️ Категории',
        'menu.invite_friends': '👥 Пригласить друзей',
        'menu.favorites': '⭐ Избранные',
        'menu.become_partner': '👨‍💼 Стать парнером',
        'menu.help': '❓ Помощь',
        'menu.profile': '👤 Личный кабинет',
        'help': '❓ Помощь',
        'back_admin': '◀️ Назад в админ‑меню',
        'back_partner': '◀️ Назад в меню партнёра',
        # Missing keys used by reply keyboards
        'choose_category': '🗂️ Категории',
        'favorites': '⭐ Избранные',
        'keyboard.referral_program': '👥 Пригласить друзей',
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
        'commands.tariffs': 'Просмотр тарифов',
        # v4.2.5 commands (новые описания)
        'commands.add_card': 'Добавить партнёра',
        
        # Voice functionality
        'voice.too_long': 'Сообщение длинновато. Запиши, пожалуйста, короче — до 60 секунд 🙏',
        'voice.too_large': 'Файл слишком большой. Отправь, пожалуйста, до 2 МБ 🤏',
        'voice.processing': 'Слушаю… секунду 🎧',
        'voice.couldnt_understand': 'Похоже, записалось неразборчиво. Давай ещё раз? Можно ближе к микрофону.',
        'voice.rate_limit': 'Слишком много запросов. Попробуй через минуту ⏳',
        'voice.btn_yes': 'Да',
        'voice.btn_retry': 'Повторить',
        
        # v4.2.4 categories labels
        'categories.restaurants': '🍽️ Рестораны и кафе',
        'categories.spa': '🧖‍♀️ SPA и массаж',
        'categories.transport': '🏍️ Аренда байков',
        'categories.hotels': '🏨 Отели',
        'categories.tours': '🚶‍♂️ Экскурсии',
        'categories.shops': '🛍️ Магазины и услуги',
        'menu_scan_qr': '🧾 Сканировать QR',
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ Выберите тип кухни:',
        'restaurants_show_all': '📋 Показать все',
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
        'transport_choose': '🚗 Выберите транспорт:',
        'transport_bikes': '🛵 Байки',
        'transport_cars': '🚘 Машины',
        'transport_bicycles': '🚲 Велосипеды',
        
        # Categories (full set for reply keyboard)
        'category_restaurants': '🍽️ Рестораны и кафе',
        'category_spa': '🧖‍♀️ SPA и массаж',
        'category_transport': '🏍️ Транспорт',
        'category_hotels': '🏨 Отели',
        'category_tours': '🚶‍♂️ Экскурсии',
        'category_shops_services': '🛍️ Магазины и услуги',
        
        # Tours
        'tours_choose': '🗺️ Выберите экскурсию:',
        'tours_group': '👥 Групповые',
        'tours_private': '👤 Индивидуальные',
        
        # Hotels
        'hotels_hotels': '🏨 Гостиницы',
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
        'choose_language_text': 'Выберите язык:',
        'request_location': '📍 Поделитесь своим местоположением, чтобы найти ближайшие заведения:',
        'nearest_places_found': '📍 <b>Ближайшие заведения:</b>\n\n',
        'no_places_found': '❌ Поблизости не найдено заведений. Попробуйте другой район.',
        'location_error': '❌ Ошибка обработки геолокации. Попробуйте еще раз.',
        'catalog_found': 'Найдено заведений',
        'catalog_page': 'Страница',
        'catalog_empty_sub': '❌ В этой подкатегории пока нет заведений.',
        'catalog_error': '❌ Ошибка загрузки каталога. Попробуйте позже.',
        'districts_found': '🌆 <b>Заведения по районам:</b>\n\n',
        'no_districts_found': '❌ Заведений по районам не найдено.',
        'districts_error': '❌ Ошибка загрузки районов. Попробуйте позже.',
        'qr_codes': '📱 QR-коды',
        'no_qr_codes': '📱 У вас пока нет QR-кодов.\n\nСоздайте QR-код для получения скидок в заведениях-партнерах.',
        'qr_codes_list': '📱 <b>Ваши QR-коды:</b>\n\n',
        'create_qr_code': '📱 Создать QR-код',
        'my_qr_codes': '📋 Мои QR-коды',
        'qr_code_created': '📱 <b>Ваш QR-код создан!</b>\n\n🆔 Код: {qr_id}\n💎 Скидка: 10%\n📅 Действует: 30 дней\n\nПокажите этот QR-код в заведениях-партнерах для получения скидки.',
        'qr_codes_error': '❌ Ошибка загрузки QR-кодов. Попробуйте позже.',
        'qr_create_error': '❌ Ошибка создания QR-кода. Попробуйте позже.',
        'detailed_profile': '👤 <b>Личный кабинет</b>\n\n🆔 <b>ID:</b> {user_id}\n👤 <b>Имя:</b> {name}\n📱 <b>Username:</b> @{username}\n🌐 <b>Язык:</b> {lang}\n\n📊 <b>Статистика:</b>\n💎 <b>QR-коды:</b> {qr_count} (активных: {active_qr})\n📍 <b>Посещено заведений:</b> 0\n🎯 <b>Любимая категория:</b> Рестораны\n⭐ <b>Рейтинг:</b> 4.5/5\n\n🏆 <b>Достижения:</b>\n• 🎉 Первый QR-код\n• 📱 Активный пользователь\n• 🎯 Исследователь\n\n💡 <b>Доступные функции:</b>\n• 📊 Просмотр статистики\n• 📋 Управление QR-кодами\n• 🔔 Настройки уведомлений\n• ⚙️ Настройки профиля',
        'statistics': '📊 Статистика',
        'settings': '⚙️ Настройки',
        'notifications': '🔔 Уведомления',
        'achievements': '🏆 Достижения',
        'cabinet.karma_and_achievements': '📈 Карма и достижения',
        'ai_assistant': '🤖 ИИ Помощник',
        'dashboard_admin': '📊 Дашборд: Модерация(0) | Уведомления(0)',
        'dashboard_superadmin': '📊 Дашборд: Модерация(0) | Уведомления(0) | Система(OK)',
        'partners': '🤝 Партнёры',
        'newsletter': '📧 Рассылка',
        'btn.partner.add_card': '➕ Добавить карточку',
        'detailed_statistics': '📊 <b>Детальная статистика</b>\n\n💎 <b>QR-коды:</b>\n• Всего создано: {total_qr}\n• Активных: {active_qr}\n• Использовано: {used_qr}\n\n📍 <b>Посещения:</b>\n• Всего заведений: 0\n• Любимая категория: {favorite_category}\n• Последнее посещение: Не было\n\n🎯 <b>Активность:</b>\n• Дней в системе: 1\n• Средний рейтинг: 4.5/5\n• Уровень: Новичок\n\n🏆 <b>Достижения:</b>\n• 🎉 Первый QR-код\n• 📱 Активный пользователь\n• 🎯 Исследователь',
        'settings_menu': '⚙️ <b>Настройки профиля</b>\n\n🌐 <b>Язык:</b> {lang}\n🔔 <b>Уведомления:</b> Включены\n📍 <b>Геолокация:</b> Разрешена\n📱 <b>QR-коды:</b> Автогенерация включена\n\n💡 <b>Доступные настройки:</b>\n• Смена языка\n• Настройки уведомлений\n• Приватность\n• Удаление аккаунта',
        'achievements_list': '🏆 <b>Достижения</b>\n\n✅ <b>Полученные:</b>\n• 🎉 Первый QR-код - Создайте свой первый QR-код\n• 📱 Активный пользователь - Используйте бота 7 дней подряд\n• 🎯 Исследователь - Посетите 5 разных заведений\n\n🔒 <b>Заблокированные:</b>\n• 💎 Мастер скидок - Получите скидку 10 раз\n• 🌟 VIP-клиент - Потратьте 100,000 VND\n• 🎖️ Легенда - Используйте бота 30 дней\n\n💡 <b>Прогресс:</b>\n• QR-коды: 1/1 ✅\n• Дни активности: 1/7\n• Заведения: 0/5',
        'back_to_cabinet': '◀️ К кабинету',
        'change_language': '🌐 Сменить язык',
        'notification_settings': '🔔 Уведомления',
        'privacy_settings': '🔒 Приватность',
        'cabinet_error': '❌ Ошибка загрузки личного кабинета. Попробуйте позже.',
        'statistics_error': '❌ Ошибка загрузки статистики. Попробуйте позже.',
        'settings_error': '❌ Ошибка загрузки настроек. Попробуйте позже.',
        'achievements_error': '❌ Ошибка загрузки достижений. Попробуйте позже.',
        
        # Policy
        'policy_text': '''🔒 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>

<b>1. ОБЩИЕ ПОЛОЖЕНИЯ</b>
Настоящая Политика конфиденциальности определяет порядок обработки персональных данных пользователей бота Karma System.

<b>2. КАКИЕ ДАННЫЕ МЫ СОБИРАЕМ</b>
• Идентификатор пользователя Telegram
• Имя пользователя и имя
• Языковые настройки
• Данные о взаимодействии с ботом
• Информация о местоположении (при использовании функции "Рядом")

<b>3. ЦЕЛИ ОБРАБОТКИ</b>
• Предоставление услуг бота
• Персонализация контента
• Аналитика использования
• Улучшение качества сервиса

<b>4. ПЕРЕДАЧА ДАННЫХ</b>
Ваши данные не передаются третьим лицам, за исключением случаев, предусмотренных законодательством.

<b>5. БЕЗОПАСНОСТЬ</b>
Мы принимаем все необходимые меры для защиты ваших персональных данных.

<b>6. ВАШИ ПРАВА</b>
Вы имеете право на доступ, исправление и удаление ваших персональных данных.

<b>7. КОНТАКТЫ</b>
По вопросам обработки персональных данных обращайтесь к администратору бота.

<i>Дата последнего обновления: 07.09.2025</i>''',
        'policy_message': '''🔒 Политика конфиденциальности\n\nПожалуйста, согласитесь с политикой конфиденциальности перед использованием сервиса.\n\nПродолжая пользоваться ботом вы соглашаетесь с политикой обработки персональных данных.''',
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
        
        # Tariff system
        'tariffs.title': '💰 Доступные тарифы партнерства',
        'tariffs.for_partners': 'Выберите подходящий тариф для вашего бизнеса:',
        'tariffs.for_users': 'Информация о тарифах для партнеров:',
        'tariffs.become_partner': '🤝 Хотите стать партнером?',
        'tariffs.become_partner_text': 'Партнеры получают доступ к управлению тарифами и могут выбирать подходящий план для своего бизнеса.',
        'tariffs.apply_instruction': '📝 Для подачи заявки на партнерство используйте раздел \'Партнерство\' в главном меню.',
        'tariffs.free_starter': 'FREE STARTER',
        'tariffs.business': 'BUSINESS',
        'tariffs.enterprise': 'ENTERPRISE',
        'tariffs.price': 'Цена',
        'tariffs.free': 'Бесплатно',
        'tariffs.month': 'месяц',
        'tariffs.transactions_limit': 'Лимит транзакций',
        'tariffs.per_month': 'в месяц',
        'tariffs.unlimited': 'Безлимит',
        'tariffs.commission': 'Комиссия',
        'tariffs.analytics': 'Аналитика',
        'tariffs.priority_support': 'Приоритетная поддержка',
        'tariffs.api_access': 'API доступ',
        'tariffs.custom_integrations': 'Кастомные интеграции',
        'tariffs.dedicated_manager': 'Выделенный менеджер',
        'tariffs.enabled': 'Включена',
        'tariffs.disabled': 'Отключена',
        'tariffs.description': 'Описание',
        'tariffs.current_tariff': 'Ваш текущий тариф',
        'tariffs.switch_tariff_button': '🔄 Переключиться на этот тариф',
        'tariffs.help_button': '❓ Помощь по тарифам',
        'tariffs.become_partner_button': '🤝 Стать партнером',
        'tariffs.back_to_tariffs_list': '◀️ Назад к тарифам',
        'tariffs.confirm_switch_text': 'Вы уверены, что хотите переключиться на тариф {tariff_name}?',
        'tariffs.switch_success': '✅ Вы успешно переключились на тариф {tariff_name}!',
        'tariffs.switch_fail': '❌ Не удалось переключить тариф. Попробуйте позже.',
        'tariffs.help_text': '❓ Помощь по тарифам\n\n💰 FREE STARTER - Бесплатный тариф для начала работы\n• 15 транзакций в месяц\n• Комиссия 12%\n• Базовые функции\n\n💼 BUSINESS - Для растущего бизнеса\n• 100 транзакций в месяц\n• Комиссия 6%\n• Аналитика + приоритетная поддержка\n\n🏢 ENTERPRISE - Для крупного бизнеса\n• Безлимит транзакций\n• Комиссия 4%\n• Все функции: API, интеграции, менеджер\n\n💡 Как сменить тариф:\n1. Выберите подходящий тариф\n2. Нажмите \'Переключиться на этот тариф\'\n3. Подтвердите смену\n\n❓ Нужна помощь? Обратитесь в поддержку!',
        'tariffs.no_tariffs': '❌ Тарифы временно недоступны. Попробуйте позже.',
        'tariffs.error_no_id': '❌ Ошибка: не указан ID тарифа',
        'tariffs.not_found': '❌ Тариф не найден',
        'tariffs.current_tariff_info': 'Это ваш текущий тариф',
        'tariffs.only_partners': '❌ Только партнеры могут управлять тарифами',
        'tariffs.only_partners_change': '❌ Только партнеры могут менять тарифы',
        
        # Language selection
        'language_ru': '🇷🇺 Русский',
        'language_en': '🇺🇸 English',
        'language_vi': '🇻🇳 Tiếng Việt',
        'language_ko': '🇰🇷 한국어',
        'choose_language': '🌐 Выберите язык',
        'language_changed': '✅ Язык изменен на {language}',
        
        # Gamification
        'gamification.achievements': '🏆 Достижения',
        'gamification.achievements_title': 'Ваши достижения',
        'gamification.stats_title': 'Статистика',
        'gamification.level': 'Уровень',
        'gamification.karma': 'Карма',
        'gamification.loyalty_points': 'Баллы лояльности',
        'gamification.achievements_count': 'Достижений',
        'gamification.referrals_count': 'Рефералов',
        'gamification.cards_count': 'Карт',
        'gamification.current_streak': 'Серия',
        'gamification.days': 'дней',
        'gamification.my_achievements': '📋 Мои достижения',
        'gamification.progress': '📈 Прогресс',
        'gamification.stats': '🎯 Статистика',
        'gamification.ranking': '🏅 Рейтинг',
        'gamification.no_achievements': 'У вас пока нет достижений',
        'gamification.achievements_tip': 'Выполняйте различные действия в системе, чтобы получить достижения!',
        'gamification.achievements_list_title': 'Ваши достижения:',
        'gamification.progress_title': 'Прогресс по достижениям:',
        'gamification.stats_title_detailed': 'Детальная статистика:',
        'gamification.next_level': 'До следующего уровня',
        'gamification.member_since': 'Участник с',
        'gamification.ranking_title': 'Рейтинг пользователей:',
        'gamification.karma_ranking': 'Рейтинг по карме:',
        'gamification.achievements_ranking': 'Рейтинг по достижениям:',
        'gamification.ranking_update': 'Рейтинг обновляется ежедневно!',
        'gamification.points_reward': 'баллов',
        'gamification.earned': 'получено',
        'gamification.progress_percentage': 'прогресс',
        
        # Navigation - Common
        'common.back_simple': '◀️ Назад',
        'back': '◀️ Назад в главное меню',
        
        # Navigation - Menu
        'menu.back_to_main_menu': '◀️ Назад в главное меню',
        
        # Navigation - Partner
        'partner.back_to_partner_menu': '◀️ Назад в меню партнёра',
        
        # Navigation - Keyboard
        'keyboard.profile_settings': '⚙️ Настройки',
        'back_to_categories': '◀️ К категориям',
        'contact_info': 'Контакт',
        'address_info': 'Адрес', 
        'discount_info': 'Скидка',
        'favorites': '⭐ Избранное',
        'ai_assistant': '🤖 AI Assistant',
        'dashboard_admin': '📊 Dashboard: Moderation(0) | Notifications(0)',
        'dashboard_superadmin': '📊 Dashboard: Moderation(0) | Notifications(0) | System(OK)',
        'partners': '🤝 Partners',
        'newsletter': '📧 Newsletter',
        'btn.partner.add_card': '➕ Add card',
        
        # Activity (loyalty) texts
        'actv_title': '🎯 Активности',
        'actv_checkin': 'Ежедневный чек‑ин',
        'actv_profile': 'Заполнить профиль',
        'actv_bindcard': 'Привязать карту',
        'actv_geocheckin': 'Чек‑ин по геолокации',
        'actv_rule_disabled': '🚧 Эта активность временно недоступна.',
        'actv_cooldown': '⏳ Активность уже выполнена. Попробуйте позже.',
        'actv_send_location_prompt': '📍 Отправьте геолокацию для чек‑ина поблизости.',
        'actv_claim_ok': '✅ Активность засчитана! Баллы начислены.',
        'actv_geo_required': '📍 Нужна геолокация. Отправьте местоположение и повторите.',
        'actv_out_of_coverage': 'ℹ️ Вы вне зоны действия для этой активности.',
    },
    'en': {
        # v4.2.4 minimal labels
        'menu.categories': '🗂️ Categories',
        'menu.invite_friends': '👥 Invite friends',
        'menu.favorites': '⭐ Favorites',
        'menu.become_partner': '👨‍💼 Become a partner',
        'menu.help': '❓ Help',
        'menu.profile': '👤 Profile',
        'back_admin': '◀️ Back to admin menu',
        'back_partner': '◀️ Back to partner menu',
        'invite.my_link': '🔗 My link',
        'invite.invited': '📋 Invited',
        'invite.earnings': '💵 Earnings',
        
        # Navigation - Common
        'common.back_simple': '◀️ Back',
        
        # Navigation - Menu
        'menu.back_to_main_menu': '◀️ Back to main menu',
        
        # Navigation - Partner
        'partner.back_to_partner_menu': '◀️ Back to partner menu',
        
        # Navigation - Keyboard
        'keyboard.profile_settings': '⚙️ Settings',
        
        # Voice functionality
        'voice.too_long': 'Message is too long. Please record shorter — up to 60 seconds 🙏',
        'voice.too_large': 'File is too large. Please send up to 2 MB 🤏',
        'voice.processing': 'Listening… one second 🎧',
        'voice.couldnt_understand': 'Seems like it recorded unclear. Let\'s try again? You can get closer to the microphone.',
        'voice.rate_limit': 'Too many requests. Try again in a minute ⏳',
        'voice.btn_yes': 'Yes',
        'voice.btn_retry': 'Retry',
        
        # Restaurant filters
        'restaurants_choose_cuisine': '🍽️ Choose cuisine type:',
        'restaurants_show_all': '📋 Show all',
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
        'transport_choose': '🚗 Choose transport:',
        'transport_bikes': '🛵 Bikes',
        'transport_cars': '🚘 Cars',
        'transport_bicycles': '🚲 Bicycles',
        
        # Categories
        'category_shops_services': '🛍️ Shops and services',
        
        # Tours
        'tours_choose': '🗺️ Choose tour:',
        'tours_group': '👥 Group tours',
        'tours_private': '👤 Private tours',
        
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
        'choose_language_text': 'Select language:',
        'request_location': '📍 Share your location to find the nearest places:',
        'nearest_places_found': '📍 <b>Nearest places:</b>\n\n',
        'no_places_found': '❌ No places found nearby. Try another area.',
        'location_error': '❌ Error processing location. Please try again.',
        'catalog_found': 'Found places',
        'catalog_page': 'Page',
        'catalog_empty_sub': '❌ No places in this subcategory yet.',
        'catalog_error': '❌ Catalog loading error. Please try again later.',
        'districts_found': '🌆 <b>Places by district:</b>\n\n',
        'no_districts_found': '❌ No places by district found.',
        'districts_error': '❌ District loading error. Please try again later.',
        'qr_codes': '📱 QR Codes',
        'no_qr_codes': '📱 You don\'t have any QR codes yet.\n\nCreate a QR code to get discounts at partner establishments.',
        'qr_codes_list': '📱 <b>Your QR codes:</b>\n\n',
        'create_qr_code': '📱 Create QR Code',
        'my_qr_codes': '📋 My QR Codes',
        'qr_code_created': '📱 <b>Your QR code has been created!</b>\n\n🆔 Code: {qr_id}\n💎 Discount: 10%\n📅 Valid for: 30 days\n\nShow this QR code at partner establishments to get discounts.',
        'qr_codes_error': '❌ QR codes loading error. Please try again later.',
        'qr_create_error': '❌ QR code creation error. Please try again later.',
        
        # Policy
        'policy_text': '''🔒 <b>PRIVACY POLICY</b>

<b>1. GENERAL PROVISIONS</b>
This Privacy Policy defines the procedure for processing personal data of Karma System bot users.

<b>2. DATA WE COLLECT</b>
• Telegram user ID
• Username and first name
• Language settings
• Bot interaction data
• Location information (when using "Nearby" feature)

<b>3. PROCESSING PURPOSES</b>
• Providing bot services
• Content personalization
• Usage analytics
• Service quality improvement

<b>4. DATA TRANSFER</b>
Your data is not transferred to third parties, except as required by law.

<b>5. SECURITY</b>
We take all necessary measures to protect your personal data.

<b>6. YOUR RIGHTS</b>
You have the right to access, correct and delete your personal data.

<b>7. CONTACTS</b>
For questions about personal data processing, contact the bot administrator.

<i>Last updated: 09/07/2025</i>''',
        'policy_message': '''🔒 Privacy Policy\n\nPlease agree to the privacy policy before using the service.\n\nContinuing means you agree to the privacy policy.''',
        'policy_accept': '✅ I agree',
        'policy_view': '📄 Privacy Policy',
        'policy_url': '/policy',
        
        # Errors
        'menu_error': 'Failed to return to main menu. Please try again later.',
        
        # Navigation
        'back_to_main_menu': '◀️ Назад в главное меню',
        'back_to_categories': '◀️ К категориям',
        'ai_assistant': '🤖 AI Assistant',
        'dashboard_admin': '📊 Dashboard: Moderation(0) | Notifications(0)',
        'dashboard_superadmin': '📊 Dashboard: Moderation(0) | Notifications(0) | System(OK)',
        'partners': '🤝 Partners',
        'newsletter': '📧 Newsletter',
        'btn.partner.add_card': '➕ Add card',
        
        # Tariff system
        'tariffs.title': '💰 Available Partnership Tariffs',
        'tariffs.for_partners': 'Choose the right tariff for your business:',
        'tariffs.for_users': 'Information about tariffs for partners:',
        'tariffs.become_partner': '🤝 Want to become a partner?',
        'tariffs.become_partner_text': 'Partners get access to tariff management and can choose the right plan for their business.',
        'tariffs.apply_instruction': '📝 To apply for partnership, use the \'Partnership\' section in the main menu.',
        'tariffs.free_starter': 'FREE STARTER',
        'tariffs.business': 'BUSINESS',
        'tariffs.enterprise': 'ENTERPRISE',
        'tariffs.price': 'Price',
        'tariffs.free': 'Free',
        'tariffs.month': 'month',
        'tariffs.transactions_limit': 'Transaction limit',
        'tariffs.per_month': 'per month',
        'tariffs.unlimited': 'Unlimited',
        'tariffs.commission': 'Commission',
        'tariffs.analytics': 'Analytics',
        'tariffs.priority_support': 'Priority support',
        'tariffs.api_access': 'API access',
        'tariffs.custom_integrations': 'Custom integrations',
        'tariffs.dedicated_manager': 'Dedicated manager',
        'tariffs.enabled': 'Enabled',
        'tariffs.disabled': 'Disabled',
        'tariffs.description': 'Description',
        'tariffs.current_tariff': 'Your current tariff',
        'tariffs.switch_tariff_button': '🔄 Switch to this tariff',
        'tariffs.help_button': '❓ Tariff help',
        'tariffs.become_partner_button': '🤝 Become partner',
        'tariffs.back_to_tariffs_list': '◀️ Back to tariffs',
        'tariffs.confirm_switch_text': 'Are you sure you want to switch to tariff {tariff_name}?',
        'tariffs.switch_success': '✅ You have successfully switched to tariff {tariff_name}!',
        'tariffs.switch_fail': '❌ Failed to switch tariff. Please try again later.',
        'tariffs.help_text': '❓ Tariff Help\n\n💰 FREE STARTER - Free tariff to get started\n• 15 transactions per month\n• 12% commission\n• Basic features\n\n💼 BUSINESS - For growing business\n• 100 transactions per month\n• 6% commission\n• Analytics + priority support\n\n🏢 ENTERPRISE - For large business\n• Unlimited transactions\n• 4% commission\n• All features: API, integrations, manager\n\n💡 How to change tariff:\n1. Choose the right tariff\n2. Click \'Switch to this tariff\'\n3. Confirm the change\n\n❓ Need help? Contact support!',
        'tariffs.no_tariffs': '❌ Tariffs are temporarily unavailable. Please try again later.',
        'tariffs.error_no_id': '❌ Error: tariff ID not specified',
        'tariffs.not_found': '❌ Tariff not found',
        'tariffs.current_tariff_info': 'This is your current tariff',
        'tariffs.only_partners': '❌ Only partners can manage tariffs',
        'tariffs.only_partners_change': '❌ Only partners can change tariffs',
        
        # Language selection
        'language_ru': '🇷🇺 Русский',
        'language_en': '🇺🇸 English',
        'language_vi': '🇻🇳 Tiếng Việt',
        'language_ko': '🇰🇷 한국어',
        'choose_language': '🌐 Choose language',
        'language_changed': '✅ Language changed to {language}',
        
        # Gamification
        'gamification.achievements': '🏆 Achievements',
        'gamification.achievements_title': 'Your achievements',
        'gamification.stats_title': 'Statistics',
        'gamification.level': 'Level',
        'gamification.karma': 'Karma',
        'gamification.loyalty_points': 'Loyalty points',
        'gamification.achievements_count': 'Achievements',
        'gamification.referrals_count': 'Referrals',
        'gamification.cards_count': 'Cards',
        'gamification.current_streak': 'Streak',
        'gamification.days': 'days',
        'gamification.my_achievements': '📋 My achievements',
        'gamification.progress': '📈 Progress',
        'gamification.stats': '🎯 Statistics',
        'gamification.ranking': '🏅 Ranking',
        'gamification.no_achievements': 'You don\'t have any achievements yet',
        'gamification.achievements_tip': 'Perform various actions in the system to get achievements!',
        'gamification.achievements_list_title': 'Your achievements:',
        'gamification.progress_title': 'Achievement progress:',
        'gamification.stats_title_detailed': 'Detailed statistics:',
        'gamification.next_level': 'To next level',
        'gamification.member_since': 'Member since',
        'gamification.ranking_title': 'User ranking:',
        'gamification.karma_ranking': 'Karma ranking:',
        'gamification.achievements_ranking': 'Achievements ranking:',
        'gamification.ranking_update': 'Ranking updates daily!',
        'gamification.points_reward': 'points',
        'gamification.earned': 'earned',
        'gamification.progress_percentage': 'progress',
        
        # Menu keys
        'menu.invite_friends': '👥 Invite friends',
        'menu.favorites': '⭐ Favorites',
        
        # Commands
        'commands.start': 'Restart',
        'commands.add_card': 'Add partner',
        'commands.webapp': 'Open WebApp',
        'commands.city': 'Change city',
        'commands.help': 'Help/FAQ',
        'commands.policy': 'Privacy policy',
        'commands.clear_cache': 'Clear cache (admin only)',
        'commands.tariffs': 'View tariffs',
    }
}

def get_text(key: str, lang: str = 'ru') -> str:
    """
    Get localized text with fallback and alias support
    Backward compatible with existing code
    """
    # Check aliases first
    if key in ALIASES:
        canonical_key = ALIASES[key]
        return get_text(canonical_key, lang)
    
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
