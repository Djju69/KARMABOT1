"""
Тесты для WebApp интеграции
"""
import pytest
import time
import os
from unittest.mock import patch, Mock
from core.services.webapp_integration import WebAppIntegration, webapp_integration


class TestWebAppIntegration:
    """Тесты WebApp интеграции"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.integration = WebAppIntegration()
        self.test_telegram_id = 123456789
        self.test_role = 'partner'
    
    def test_create_webapp_url(self):
        """Тест создания URL для WebApp"""
        url = self.integration.create_webapp_url(
            telegram_id=self.test_telegram_id,
            role=self.test_role,
            webapp_path='/webapp'
        )
        
        # Проверить что URL создан
        assert url is not None
        assert url != "#"
        assert 'tg_user_id=' in url
        assert 'tg_role=' in url
        assert 'tg_timestamp=' in url
        assert 'tg_signature=' in url
        assert '/webapp' in url
    
    def test_url_contains_correct_params(self):
        """Тест что URL содержит правильные параметры"""
        url = self.integration.create_webapp_url(
            telegram_id=self.test_telegram_id,
            role=self.test_role,
            webapp_path='/webapp'
        )
        
        # Проверить параметры в URL
        assert f'tg_user_id={self.test_telegram_id}' in url
        assert f'tg_role={self.test_role}' in url
        assert 'tg_timestamp=' in url
        assert 'tg_expires=' in url
        assert 'tg_signature=' in url
    
    def test_signature_creation(self):
        """Тест создания подписи"""
        params = {
            'tg_user_id': self.test_telegram_id,
            'tg_role': self.test_role,
            'tg_timestamp': int(time.time())
        }
        
        signature = self.integration._create_signature(params)
        
        # Проверить что подпись создана
        assert signature is not None
        assert len(signature) == 16  # Первые 16 символов SHA256
        assert isinstance(signature, str)
    
    def test_signature_validation(self):
        """Тест валидации подписи"""
        params = {
            'tg_user_id': self.test_telegram_id,
            'tg_role': self.test_role,
            'tg_timestamp': int(time.time()),
            'tg_expires': int(time.time()) + 600
        }
        
        # Создать подпись
        signature = self.integration._create_signature(params)
        params['tg_signature'] = signature
        
        # Валидировать
        is_valid = self.integration.validate_webapp_params(params)
        assert is_valid is True
    
    def test_signature_validation_invalid(self):
        """Тест валидации неверной подписи"""
        params = {
            'tg_user_id': self.test_telegram_id,
            'tg_role': self.test_role,
            'tg_timestamp': int(time.time()),
            'tg_expires': int(time.time()) + 600,
            'tg_signature': 'invalid_signature'
        }
        
        # Валидировать
        is_valid = self.integration.validate_webapp_params(params)
        assert is_valid is False
    
    def test_expired_token_validation(self):
        """Тест валидации истекшего токена"""
        params = {
            'tg_user_id': self.test_telegram_id,
            'tg_role': self.test_role,
            'tg_timestamp': int(time.time()) - 700,  # Истек 100 секунд назад
            'tg_expires': int(time.time()) - 100,
            'tg_signature': 'some_signature'
        }
        
        # Валидировать
        is_valid = self.integration.validate_webapp_params(params)
        assert is_valid is False
    
    def test_missing_params_validation(self):
        """Тест валидации с отсутствующими параметрами"""
        params = {
            'tg_user_id': self.test_telegram_id,
            'tg_role': self.test_role,
            # Отсутствует tg_timestamp и tg_signature
        }
        
        # Валидировать
        is_valid = self.integration.validate_webapp_params(params)
        assert is_valid is False
    
    def test_create_partner_webapp_url(self):
        """Тест создания URL для партнерского WebApp"""
        url = self.integration.create_partner_webapp_url(
            telegram_id=self.test_telegram_id,
            partner_id=123
        )
        
        assert url is not None
        assert '/web/partner/cards' in url
        assert 'partner_id=123' in url
        assert f'tg_user_id={self.test_telegram_id}' in url
        assert 'tg_role=partner' in url
    
    def test_create_admin_webapp_url(self):
        """Тест создания URL для админского WebApp"""
        url = self.integration.create_admin_webapp_url(
            telegram_id=self.test_telegram_id,
            admin_level='super_admin'
        )
        
        assert url is not None
        assert '/web/admin/dashboard' in url
        assert 'admin_level=super_admin' in url
        assert f'tg_user_id={self.test_telegram_id}' in url
        assert 'tg_role=super_admin' in url
    
    def test_create_user_webapp_url(self):
        """Тест создания URL для пользовательского WebApp"""
        url = self.integration.create_user_webapp_url(
            telegram_id=self.test_telegram_id
        )
        
        assert url is not None
        assert '/web/user/profile' in url
        assert f'tg_user_id={self.test_telegram_id}' in url
        assert 'tg_role=user' in url
    
    def test_additional_params(self):
        """Тест добавления дополнительных параметров"""
        additional_params = {
            'custom_param': 'test_value',
            'another_param': 123
        }
        
        url = self.integration.create_webapp_url(
            telegram_id=self.test_telegram_id,
            role=self.test_role,
            webapp_path='/webapp',
            additional_params=additional_params
        )
        
        assert 'custom_param=test_value' in url
        assert 'another_param=123' in url
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        # Тест с неверными параметрами
        url = self.integration.create_webapp_url(
            telegram_id=None,  # Неверный параметр
            role=self.test_role,
            webapp_path='/webapp'
        )
        
        # Проверить что URL создан (None обрабатывается как строка)
        assert url is not None
        assert 'tg_user_id=None' in url


class TestWebAppUtilityFunctions:
    """Тесты утилитарных функций WebApp"""
    
    def test_create_partner_webapp_button(self):
        """Тест создания кнопки для партнера"""
        from core.services.webapp_integration import create_partner_webapp_button
        
        url = create_partner_webapp_button(123456, 789)
        
        assert url is not None
        assert '/web/partner/cards' in url
        assert 'partner_id=789' in url
    
    def test_create_admin_webapp_button(self):
        """Тест создания кнопки для админа"""
        from core.services.webapp_integration import create_admin_webapp_button
        
        url = create_admin_webapp_button(123456, 'super_admin')
        
        assert url is not None
        assert '/web/admin/dashboard' in url
        assert 'admin_level=super_admin' in url
    
    def test_create_user_webapp_button(self):
        """Тест создания кнопки для пользователя"""
        from core.services.webapp_integration import create_user_webapp_button
        
        url = create_user_webapp_button(123456)
        
        assert url is not None
        assert '/web/user/profile' in url


class TestWebAppIntegrationEnvironment:
    """Тесты WebApp интеграции с переменными окружения"""
    
    def test_secret_key_required(self):
        """Тест что SECRET_KEY обязателен"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SECRET_KEY environment variable is required"):
                WebAppIntegration()
    
    def test_odoo_base_url_default(self):
        """Тест дефолтного URL Odoo"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret'}):
            integration = WebAppIntegration()
            
            # Создать URL без ODOO_BASE_URL
            url = integration.create_webapp_url(
                telegram_id=123456,
                role='user',
                webapp_path='/webapp'
            )
            
            assert 'https://odoo.example.com' in url
    
    def test_odoo_base_url_custom(self):
        """Тест кастомного URL Odoo"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret',
            'ODOO_BASE_URL': 'https://my-odoo.com'
        }):
            integration = WebAppIntegration()
            
            url = integration.create_webapp_url(
                telegram_id=123456,
                role='user',
                webapp_path='/webapp'
            )
            
            assert 'https://my-odoo.com' in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
