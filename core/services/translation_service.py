"""
Сервис для управления переводами и мультиязычностью
"""
import logging
from typing import Dict, Any, Optional, List
import json
import os

logger = logging.getLogger(__name__)

class TranslationService:
    """Сервис для управления переводами"""
    
    def __init__(self):
        self.supported_languages = {
            'ru': {'name': 'Русский', 'flag': '🇷🇺', 'code': 'ru'},
            'en': {'name': 'English', 'flag': '🇺🇸', 'code': 'en'},
            'vi': {'name': 'Tiếng Việt', 'flag': '🇻🇳', 'code': 'vi'},
            'ko': {'name': '한국어', 'flag': '🇰🇷', 'code': 'ko'}
        }
        self.default_language = 'ru'
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Загрузить переводы из файлов"""
        try:
            # Загружаем переводы из папки core/i18n/
            i18n_dir = os.path.join(os.path.dirname(__file__), '..', 'i18n')
            
            for lang_code in self.supported_languages.keys():
                file_path = os.path.join(i18n_dir, f'{lang_code}.json')
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                        logger.info(f"Loaded translations for {lang_code}: {len(self.translations[lang_code])} keys")
                else:
                    logger.warning(f"Translation file not found: {file_path}")
                    self.translations[lang_code] = {}
                    
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
            # Fallback к базовым переводам
            self.translations = {
                'ru': self._get_fallback_translations('ru'),
                'en': self._get_fallback_translations('en'),
                'vi': self._get_fallback_translations('vi'),
                'ko': self._get_fallback_translations('ko')
            }
    
    def _get_fallback_translations(self, lang_code: str) -> Dict[str, str]:
        """Получить базовые переводы как fallback"""
        fallbacks = {
            'ru': {
                'main_menu': '🏠 Главное меню',
                'profile': '👤 Профиль',
                'catalog': '📋 Каталог',
                'language': '🌐 Язык',
                'help': '❓ Помощь',
                'settings': '⚙️ Настройки',
                'back': '⬅️ Назад',
                'cancel': '❌ Отмена',
                'confirm': '✅ Подтвердить',
                'error': '❌ Ошибка',
                'success': '✅ Успешно',
                'loading': '⏳ Загрузка...',
                'not_found': '❌ Не найдено',
                'access_denied': '🚫 Доступ запрещен',
                'invalid_data': '❌ Неверные данные',
                'try_again': '🔄 Попробуйте снова'
            },
            'en': {
                'main_menu': '🏠 Main Menu',
                'profile': '👤 Profile',
                'catalog': '📋 Catalog',
                'language': '🌐 Language',
                'help': '❓ Help',
                'settings': '⚙️ Settings',
                'back': '⬅️ Back',
                'cancel': '❌ Cancel',
                'confirm': '✅ Confirm',
                'error': '❌ Error',
                'success': '✅ Success',
                'loading': '⏳ Loading...',
                'not_found': '❌ Not Found',
                'access_denied': '🚫 Access Denied',
                'invalid_data': '❌ Invalid Data',
                'try_again': '🔄 Try Again'
            },
            'vi': {
                'main_menu': '🏠 Menu Chính',
                'profile': '👤 Hồ Sơ',
                'catalog': '📋 Danh Mục',
                'language': '🌐 Ngôn Ngữ',
                'help': '❓ Trợ Giúp',
                'settings': '⚙️ Cài Đặt',
                'back': '⬅️ Quay Lại',
                'cancel': '❌ Hủy',
                'confirm': '✅ Xác Nhận',
                'error': '❌ Lỗi',
                'success': '✅ Thành Công',
                'loading': '⏳ Đang Tải...',
                'not_found': '❌ Không Tìm Thấy',
                'access_denied': '🚫 Từ Chối Truy Cập',
                'invalid_data': '❌ Dữ Liệu Không Hợp Lệ',
                'try_again': '🔄 Thử Lại'
            },
            'ko': {
                'main_menu': '🏠 메인 메뉴',
                'profile': '👤 프로필',
                'catalog': '📋 카탈로그',
                'language': '🌐 언어',
                'help': '❓ 도움말',
                'settings': '⚙️ 설정',
                'back': '⬅️ 뒤로',
                'cancel': '❌ 취소',
                'confirm': '✅ 확인',
                'error': '❌ 오류',
                'success': '✅ 성공',
                'loading': '⏳ 로딩 중...',
                'not_found': '❌ 찾을 수 없음',
                'access_denied': '🚫 접근 거부',
                'invalid_data': '❌ 잘못된 데이터',
                'try_again': '🔄 다시 시도'
            }
        }
        return fallbacks.get(lang_code, fallbacks['ru'])
    
    def get_text(self, key: str, lang_code: str = None, **kwargs) -> str:
        """Получить переведенный текст"""
        if lang_code is None:
            lang_code = self.default_language
        
        if lang_code not in self.supported_languages:
            lang_code = self.default_language
        
        # Получаем перевод
        translation = self.translations.get(lang_code, {}).get(key, '')
        
        # Если перевод не найден, пробуем fallback
        if not translation:
            translation = self._get_fallback_translations(lang_code).get(key, '')
        
        # Если и fallback не найден, возвращаем ключ
        if not translation:
            translation = key
        
        # Заменяем параметры в тексте
        try:
            if kwargs:
                translation = translation.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"Error formatting translation for key '{key}': {e}")
        
        return translation
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """Получить список поддерживаемых языков"""
        return self.supported_languages
    
    def get_language_name(self, lang_code: str) -> str:
        """Получить название языка"""
        lang_info = self.supported_languages.get(lang_code)
        if lang_info:
            return f"{lang_info['flag']} {lang_info['name']}"
        return lang_code
    
    def is_language_supported(self, lang_code: str) -> bool:
        """Проверить, поддерживается ли язык"""
        return lang_code in self.supported_languages
    
    def get_user_language(self, user_id: int) -> str:
        """Получить язык пользователя из БД"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT language FROM users WHERE telegram_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    lang_code = result[0]
                    if self.is_language_supported(lang_code):
                        return lang_code
                
                return self.default_language
                
        except Exception as e:
            logger.error(f"Error getting user language: {e}")
            return self.default_language
    
    def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """Установить язык пользователя"""
        try:
            if not self.is_language_supported(lang_code):
                return False
            
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                conn.execute("""
                    UPDATE users SET language = ? WHERE telegram_id = ?
                """, (lang_code, user_id))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
            return False
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """Получить статистику переводов"""
        stats = {}
        for lang_code, translations in self.translations.items():
            stats[lang_code] = {
                'total_keys': len(translations),
                'translated_keys': len([k for k, v in translations.items() if v]),
                'missing_keys': len([k for k, v in translations.items() if not v]),
                'coverage_percent': (len([k for k, v in translations.items() if v]) / len(translations) * 100) if translations else 0
            }
        return stats
    
    def get_missing_translations(self, lang_code: str) -> List[str]:
        """Получить список отсутствующих переводов"""
        if lang_code not in self.translations:
            return []
        
        missing = []
        for key, value in self.translations[lang_code].items():
            if not value or value.strip() == '':
                missing.append(key)
        
        return missing
    
    def add_translation(self, key: str, translations: Dict[str, str]) -> bool:
        """Добавить новый перевод"""
        try:
            for lang_code, text in translations.items():
                if lang_code in self.supported_languages:
                    if lang_code not in self.translations:
                        self.translations[lang_code] = {}
                    self.translations[lang_code][key] = text
            
            # Сохраняем в файлы
            self._save_translations()
            return True
            
        except Exception as e:
            logger.error(f"Error adding translation: {e}")
            return False
    
    def _save_translations(self):
        """Сохранить переводы в файлы"""
        try:
            i18n_dir = os.path.join(os.path.dirname(__file__), '..', 'i18n')
            os.makedirs(i18n_dir, exist_ok=True)
            
            for lang_code, translations in self.translations.items():
                file_path = os.path.join(i18n_dir, f'{lang_code}.json')
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"Error saving translations: {e}")

# Создаем экземпляр сервиса
translation_service = TranslationService()
