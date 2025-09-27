"""
Тесты для тарифной системы партнеров
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from core.models.tariff_models import Tariff, TariffType, TariffFeatures, DEFAULT_TARIFFS
from core.services.tariff_service import TariffService

class TestTariffModels:
    """Тесты для моделей тарифов"""
    
    def test_tariff_type_enum(self):
        """Тест перечисления типов тарифов"""
        assert TariffType.FREE_STARTER.value == "free_starter"
        assert TariffType.BUSINESS.value == "business"
        assert TariffType.ENTERPRISE.value == "enterprise"
    
    def test_tariff_features_dataclass(self):
        """Тест dataclass функций тарифа"""
        features = TariffFeatures(
            max_transactions_per_month=100,
            commission_rate=0.06,
            analytics_enabled=True,
            priority_support=True,
            api_access=False,
            custom_integrations=False,
            dedicated_manager=False
        )
        
        assert features.max_transactions_per_month == 100
        assert features.commission_rate == 0.06
        assert features.analytics_enabled is True
        assert features.priority_support is True
        assert features.api_access is False
    
    def test_tariff_dataclass(self):
        """Тест dataclass тарифа"""
        features = TariffFeatures(
            max_transactions_per_month=100,
            commission_rate=0.06,
            analytics_enabled=True,
            priority_support=True,
            api_access=False,
            custom_integrations=False,
            dedicated_manager=False
        )
        
        tariff = Tariff(
            id=1,
            name="BUSINESS",
            tariff_type=TariffType.BUSINESS,
            price_vnd=490000,
            features=features,
            description="Тестовый тариф"
        )
        
        assert tariff.id == 1
        assert tariff.name == "BUSINESS"
        assert tariff.tariff_type == TariffType.BUSINESS
        assert tariff.price_vnd == 490000
        assert tariff.features.commission_rate == 0.06
    
    def test_default_tariffs(self):
        """Тест предустановленных тарифов"""
        assert TariffType.FREE_STARTER in DEFAULT_TARIFFS
        assert TariffType.BUSINESS in DEFAULT_TARIFFS
        assert TariffType.ENTERPRISE in DEFAULT_TARIFFS
        
        # Проверяем FREE STARTER
        free_tariff = DEFAULT_TARIFFS[TariffType.FREE_STARTER]
        assert free_tariff.price_vnd == 0
        assert free_tariff.features.max_transactions_per_month == 15
        assert free_tariff.features.commission_rate == 0.12
        assert free_tariff.features.analytics_enabled is False
        
        # Проверяем BUSINESS
        business_tariff = DEFAULT_TARIFFS[TariffType.BUSINESS]
        assert business_tariff.price_vnd == 490000
        assert business_tariff.features.max_transactions_per_month == 100
        assert business_tariff.features.commission_rate == 0.06
        assert business_tariff.features.analytics_enabled is True
        
        # Проверяем ENTERPRISE
        enterprise_tariff = DEFAULT_TARIFFS[TariffType.ENTERPRISE]
        assert enterprise_tariff.price_vnd == 960000
        assert enterprise_tariff.features.max_transactions_per_month == -1  # Безлимит
        assert enterprise_tariff.features.commission_rate == 0.04
        assert enterprise_tariff.features.api_access is True
        assert enterprise_tariff.features.dedicated_manager is True

class TestTariffService:
    """Тесты для сервиса тарифов"""
    
    @pytest.fixture
    def tariff_service(self):
        """Фикстура сервиса тарифов"""
        return TariffService()
    
    @pytest.fixture
    def mock_db_v2(self):
        """Фикстура мока базы данных"""
        mock_db = Mock()
        mock_db.fetch_all = Mock()
        mock_db.fetch_one = Mock()
        mock_db.execute = Mock()
        return mock_db
    
    @pytest.mark.asyncio
    async def test_get_all_tariffs_success(self, tariff_service, mock_db_v2):
        """Тест успешного получения всех тарифов"""
        # Мокаем данные из БД
        mock_rows = [
            (1, "FREE STARTER", "free_starter", 0, 15, 0.12, False, False, False, False, False, "Бесплатный тариф", True, datetime.now(), datetime.now()),
            (2, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now()),
            (3, "ENTERPRISE", "enterprise", 960000, -1, 0.04, True, True, True, True, True, "Корпоративный тариф", True, datetime.now(), datetime.now())
        ]
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_all.return_value = mock_rows
            
            tariffs = await tariff_service.get_all_tariffs()
            
            assert len(tariffs) == 3
            assert tariffs[0].name == "FREE STARTER"
            assert tariffs[1].name == "BUSINESS"
            assert tariffs[2].name == "ENTERPRISE"
            
            # Проверяем что запрос был выполнен
            mock_db_v2.fetch_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_tariffs_empty(self, tariff_service, mock_db_v2):
        """Тест получения пустого списка тарифов"""
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_all.return_value = []
            
            tariffs = await tariff_service.get_all_tariffs()
            
            assert len(tariffs) == 0
    
    @pytest.mark.asyncio
    async def test_get_all_tariffs_error(self, tariff_service, mock_db_v2):
        """Тест обработки ошибки при получении тарифов"""
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_all.side_effect = Exception("Database error")
            
            tariffs = await tariff_service.get_all_tariffs()
            
            assert len(tariffs) == 0
    
    @pytest.mark.asyncio
    async def test_get_tariff_by_type_success(self, tariff_service, mock_db_v2):
        """Тест успешного получения тарифа по типу"""
        mock_row = (1, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = mock_row
            
            tariff = await tariff_service.get_tariff_by_type(TariffType.BUSINESS)
            
            assert tariff is not None
            assert tariff.name == "BUSINESS"
            assert tariff.tariff_type == TariffType.BUSINESS
            assert tariff.price_vnd == 490000
            assert tariff.features.commission_rate == 0.06
    
    @pytest.mark.asyncio
    async def test_get_tariff_by_type_not_found(self, tariff_service, mock_db_v2):
        """Тест получения несуществующего тарифа"""
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = None
            
            tariff = await tariff_service.get_tariff_by_type(TariffType.BUSINESS)
            
            assert tariff is None
    
    @pytest.mark.asyncio
    async def test_get_partner_current_tariff_with_subscription(self, tariff_service, mock_db_v2):
        """Тест получения текущего тарифа партнера с подпиской"""
        mock_row = (1, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = mock_row
            
            tariff = await tariff_service.get_partner_current_tariff(123)
            
            assert tariff is not None
            assert tariff.name == "BUSINESS"
    
    @pytest.mark.asyncio
    async def test_get_partner_current_tariff_default(self, tariff_service, mock_db_v2):
        """Тест получения дефолтного тарифа для партнера без подписки"""
        # Первый вызов возвращает None (нет подписки)
        # Второй вызов возвращает FREE STARTER
        mock_free_row = (1, "FREE STARTER", "free_starter", 0, 15, 0.12, False, False, False, False, False, "Бесплатный тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.side_effect = [None, mock_free_row]
            
            tariff = await tariff_service.get_partner_current_tariff(123)
            
            assert tariff is not None
            assert tariff.name == "FREE STARTER"
            assert tariff.tariff_type == TariffType.FREE_STARTER
    
    @pytest.mark.asyncio
    async def test_subscribe_partner_to_tariff_success(self, tariff_service, mock_db_v2):
        """Тест успешной подписки партнера на тариф"""
        mock_tariff_row = (1, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = mock_tariff_row
            
            result = await tariff_service.subscribe_partner_to_tariff(123, TariffType.BUSINESS)
            
            assert result is True
            # Проверяем что были выполнены запросы на деактивацию и создание подписки
            assert mock_db_v2.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_subscribe_partner_to_tariff_not_found(self, tariff_service, mock_db_v2):
        """Тест подписки на несуществующий тариф"""
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = None
            
            result = await tariff_service.subscribe_partner_to_tariff(123, TariffType.BUSINESS)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_transaction_limit_unlimited(self, tariff_service, mock_db_v2):
        """Тест проверки лимита для безлимитного тарифа"""
        mock_tariff_row = (1, "ENTERPRISE", "enterprise", 960000, -1, 0.04, True, True, True, True, True, "Корпоративный тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = mock_tariff_row
            
            result = await tariff_service.check_transaction_limit(123)
            
            assert result["allowed"] is True
            assert result["remaining"] == -1
            assert result["tariff"] == "ENTERPRISE"
    
    @pytest.mark.asyncio
    async def test_check_transaction_limit_with_limit(self, tariff_service, mock_db_v2):
        """Тест проверки лимита для тарифа с ограничениями"""
        mock_tariff_row = (1, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.side_effect = [mock_tariff_row, (25,)]  # Тариф и количество использованных транзакций
            
            result = await tariff_service.check_transaction_limit(123)
            
            assert result["allowed"] is True
            assert result["remaining"] == 75  # 100 - 25
            assert result["used"] == 25
            assert result["limit"] == 100
    
    @pytest.mark.asyncio
    async def test_get_tariff_commission_rate(self, tariff_service, mock_db_v2):
        """Тест получения процента комиссии"""
        mock_tariff_row = (1, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = mock_tariff_row
            
            commission_rate = await tariff_service.get_tariff_commission_rate(123)
            
            assert commission_rate == 0.06
    
    @pytest.mark.asyncio
    async def test_get_tariff_commission_rate_default(self, tariff_service, mock_db_v2):
        """Тест получения дефолтного процента комиссии"""
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = None
            
            commission_rate = await tariff_service.get_tariff_commission_rate(123)
            
            assert commission_rate == 0.12  # Дефолтная комиссия
    
    @pytest.mark.asyncio
    async def test_get_partner_tariff_features(self, tariff_service, mock_db_v2):
        """Тест получения функций тарифа партнера"""
        mock_tariff_row = (1, "BUSINESS", "business", 490000, 100, 0.06, True, True, False, False, False, "Бизнес тариф", True, datetime.now(), datetime.now())
        
        with patch('core.services.tariff_service.db_v2', mock_db_v2):
            mock_db_v2.fetch_one.return_value = mock_tariff_row
            
            features = await tariff_service.get_partner_tariff_features(123)
            
            assert features["analytics_enabled"] is True
            assert features["priority_support"] is True
            assert features["api_access"] is False
            assert features["tariff_name"] == "BUSINESS"
            assert features["commission_rate"] == 0.06

class TestTariffIntegration:
    """Интеграционные тесты тарифной системы"""
    
    @pytest.mark.asyncio
    async def test_tariff_service_initialization(self):
        """Тест инициализации сервиса тарифов"""
        service = TariffService()
        assert service.default_tariffs is not None
        assert len(service.default_tariffs) == 3
    
    def test_tariff_types_coverage(self):
        """Тест покрытия всех типов тарифов"""
        service = TariffService()
        
        for tariff_type in TariffType:
            assert tariff_type in service.default_tariffs
            tariff = service.default_tariffs[tariff_type]
            assert tariff.tariff_type == tariff_type
            assert tariff.name is not None
            assert tariff.price_vnd >= 0
            assert tariff.features.commission_rate > 0

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
