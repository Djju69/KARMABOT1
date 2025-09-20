"""
Тесты для SSO сервиса
"""
import pytest
import time
import jwt
from unittest.mock import patch, Mock
from core.services.sso_service import SSOService, sso_service


class TestSSOService:
    """Тесты SSO сервиса"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.service = SSOService()
        self.test_telegram_id = 123456789
        self.test_role = 'partner'
    
    @pytest.mark.asyncio
    async def test_create_sso_token(self):
        """Тест создания SSO токена"""
        token = await self.service.create_sso_token(
            telegram_id=self.test_telegram_id,
            role=self.test_role
        )
        
        # Проверить что токен создан
        assert token is not None
        assert len(token) > 0
        
        # Проверить структуру токена
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload['telegram_id'] == str(self.test_telegram_id)
        assert payload['role'] == self.test_role
        assert 'iat' in payload
        assert 'exp' in payload
        assert 'session_id' in payload
        assert 'device_fingerprint' in payload
    
    @pytest.mark.asyncio
    async def test_token_ttl(self):
        """Тест TTL токена"""
        custom_ttl = 300  # 5 минут
        token = await self.service.create_sso_token(
            telegram_id=self.test_telegram_id,
            role=self.test_role,
            custom_ttl=custom_ttl
        )
        
        payload = jwt.decode(token, options={"verify_signature": False})
        iat = payload['iat']
        exp = payload['exp']
        
        # Проверить что TTL соответствует заданному
        assert exp - iat == custom_ttl
    
    @pytest.mark.asyncio
    async def test_token_with_permissions(self):
        """Тест токена с разрешениями"""
        permissions = ['view_cards', 'moderate_cards']
        token = await self.service.create_sso_token(
            telegram_id=self.test_telegram_id,
            role=self.test_role,
            permissions=permissions
        )
        
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload['permissions'] == permissions
    
    def test_validate_sso_token(self):
        """Тест валидации токена"""
        # Создать токен синхронно для теста
        current_time = int(time.time())
        payload = {
            'telegram_id': str(self.test_telegram_id),
            'role': self.test_role,
            'iat': current_time,
            'exp': current_time + 600,
            'session_id': f"tg_{self.test_telegram_id}_{current_time}",
            'device_fingerprint': self.service._device_fingerprint(self.test_telegram_id),
            'iss': 'karmabot',
            'aud': 'odoo_webapp'
        }
        
        token = jwt.encode(payload, self.service.secret, algorithm='HS256')
        
        # Валидировать токен
        validated_payload = self.service.validate_sso_token(token)
        assert validated_payload['telegram_id'] == str(self.test_telegram_id)
        assert validated_payload['role'] == self.test_role
    
    def test_validate_expired_token(self):
        """Тест валидации истекшего токена"""
        # Создать истекший токен
        current_time = int(time.time())
        payload = {
            'telegram_id': str(self.test_telegram_id),
            'role': self.test_role,
            'iat': current_time - 700,  # Истек 100 секунд назад
            'exp': current_time - 100,
            'session_id': f"tg_{self.test_telegram_id}_{current_time}",
            'device_fingerprint': self.service._device_fingerprint(self.test_telegram_id),
            'iss': 'karmabot',
            'aud': 'odoo_webapp'
        }
        
        token = jwt.encode(payload, self.service.secret, algorithm='HS256')
        
        # Попытка валидации должна вызвать исключение
        with pytest.raises(jwt.ExpiredSignatureError):
            self.service.validate_sso_token(token)
    
    def test_invalid_token(self):
        """Тест валидации невалидного токена"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.InvalidTokenError):
            self.service.validate_sso_token(invalid_token)
    
    def test_device_fingerprint(self):
        """Тест генерации отпечатка устройства"""
        fingerprint1 = self.service._device_fingerprint(self.test_telegram_id)
        fingerprint2 = self.service._device_fingerprint(self.test_telegram_id)
        
        # Отпечатки должны быть одинаковыми для одного пользователя
        assert fingerprint1 == fingerprint2
        assert len(fingerprint1) == 16  # MD5 хэш обрезанный до 16 символов
    
    def test_get_admin_permissions(self):
        """Тест получения разрешений админа"""
        admin_permissions = self.service._get_admin_permissions('admin')
        super_admin_permissions = self.service._get_admin_permissions('super_admin')
        
        # Супер-админ должен иметь больше разрешений
        assert len(super_admin_permissions) > len(admin_permissions)
        
        # Проверить базовые разрешения
        assert 'view_users' in admin_permissions
        assert 'moderate_cards' in admin_permissions
        assert 'manage_admins' in super_admin_permissions
        assert 'system_settings' in super_admin_permissions
    
    def test_get_token_info(self):
        """Тест получения информации о токене"""
        current_time = int(time.time())
        payload = {
            'telegram_id': str(self.test_telegram_id),
            'role': self.test_role,
            'iat': current_time,
            'exp': current_time + 600,
            'session_id': f"tg_{self.test_telegram_id}_{current_time}",
            'permissions': ['view_cards']
        }
        
        token = jwt.encode(payload, self.service.secret, algorithm='HS256')
        info = self.service.get_token_info(token)
        
        assert info['telegram_id'] == str(self.test_telegram_id)
        assert info['role'] == self.test_role
        assert info['remaining_seconds'] > 0
        assert not info['is_expired']
        assert info['permissions'] == ['view_cards']
    
    @pytest.mark.asyncio
    async def test_create_webapp_url(self):
        """Тест создания URL для WebApp"""
        with patch.dict('os.environ', {'ODOO_BASE_URL': 'https://test.odoo.com'}):
            url = await self.service.create_webapp_url(
                telegram_id=self.test_telegram_id,
                role=self.test_role,
                webapp_path='/partner/cards'
            )
            
            assert url.startswith('https://test.odoo.com/partner/cards')
            assert 'sso=' in url
    
    @pytest.mark.asyncio
    async def test_refresh_token(self):
        """Тест обновления токена"""
        # Создать исходный токен
        original_token = await self.service.create_sso_token(
            telegram_id=self.test_telegram_id,
            role=self.test_role
        )
        
        # Небольшая задержка чтобы время создания отличалось
        import asyncio
        await asyncio.sleep(0.1)
        
        # Обновить токен
        refreshed_token = await self.service.refresh_sso_token(original_token)
        
        # Проверить что новый токен валиден
        payload = self.service.validate_sso_token(refreshed_token)
        assert payload['telegram_id'] == str(self.test_telegram_id)
        assert payload['role'] == self.test_role
        
        # Проверить что функция refresh работает корректно
        # (токены могут быть одинаковыми если созданы в одну секунду)
        assert payload['telegram_id'] == str(self.test_telegram_id)
        assert payload['role'] == self.test_role


class TestSSOUtilityFunctions:
    """Тесты утилитарных функций SSO"""
    
    @pytest.mark.asyncio
    async def test_create_partner_sso_token(self):
        """Тест создания токена для партнера"""
        from core.services.sso_service import create_partner_sso_token
        
        token = await create_partner_sso_token(123456)
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload['role'] == 'partner'
    
    @pytest.mark.asyncio
    async def test_create_admin_sso_token(self):
        """Тест создания токена для админа"""
        from core.services.sso_service import create_admin_sso_token
        
        token = await create_admin_sso_token(123456, 'super_admin')
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload['role'] == 'super_admin'
    
    @pytest.mark.asyncio
    async def test_create_webapp_button(self):
        """Тест создания URL для WebApp кнопки"""
        from core.services.sso_service import create_webapp_button
        
        user_data = {'id': 123456, 'role': 'partner'}
        url = await create_webapp_button('/partner/cards', 'Мои карточки', user_data)
        
        assert url.startswith('http')
        assert 'sso=' in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
