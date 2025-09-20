"""
Тесты для функциональности QR-кодов
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from core.services.qr_code_service import QRCodeService
from core.settings_new import settings

@pytest.fixture
def qr_service():
    """Фикстура для сервиса QR-кодов"""
    return QRCodeService()

@pytest.mark.asyncio
async def test_generate_qr_code(qr_service):
    """Тест генерации QR-кода"""
    # Подготовка
    user_id = 12345
    points = 100
    
    # Действие
    qr_data = await qr_service.generate_qr_code(user_id, points)
    
    # Проверка
    assert qr_data is not None
    assert "code" in qr_data
    assert "image_url" in qr_data
    assert str(user_id) in qr_data["code"]
    assert str(points) in qr_data["code"]

@pytest.mark.asyncio
async def test_validate_qr_code(qr_service):
    """Тест валидации QR-кода"""
    # Подготовка
    user_id = 12345
    points = 100
    qr_data = await qr_service.generate_qr_code(user_id, points)
    
    # Действие
    is_valid = await qr_service.validate_qr_code(qr_data["code"], user_id, points)
    
    # Проверка
    assert is_valid is True

@pytest.mark.asyncio
async def test_get_user_qr_codes(qr_service):
    """Тест получения списка QR-кодов пользователя"""
    # Подготовка
    user_id = 12345
    
    # Действие
    qr_codes = await qr_service.get_user_qr_codes(user_id)
    
    # Проверка
    assert isinstance(qr_codes, list)

@pytest.mark.asyncio
async def test_mark_qr_used(qr_service):
    """Тест отметки QR-кода как использованного"""
    # Подготовка
    qr_id = "test_qr_123"
    used_by = 12345
    
    # Действие
    result = await qr_service.mark_qr_used(qr_id, used_by)
    
    # Проверка
    assert result is True

# Тесты для проверки настроек
def test_settings_loaded():
    """Проверка загрузки настроек"""
    assert settings is not None
    assert hasattr(settings, 'BOT_TOKEN')
    assert hasattr(settings, 'ADMIN_ID')
    assert hasattr(settings, 'FEATURE_QR_WEBAPP')

def test_feature_flags():
    """Проверка работы фича-флагов"""
    assert isinstance(settings.FEATURE_QR_WEBAPP, bool)
    assert isinstance(settings.FEATURE_PARTNER_FSM, bool)
    assert isinstance(settings.FEATURE_MODERATION, bool)
    assert isinstance(settings.FEATURE_NEW_MENU, bool)
    assert isinstance(settings.FEATURE_LISTEN_NOTIFY, bool)
