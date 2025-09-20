"""
Тесты для многоуровневой реферальной системы
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from datetime import datetime

from core.services.multilevel_referral_service import MultilevelReferralService
from core.models.referral_tree import ReferralTree, ReferralBonus, ReferralStats
from core.common.exceptions import BusinessLogicError, ValidationError


class TestMultilevelReferralService:
    """Тесты для многоуровневой реферальной системы"""
    
    @pytest.fixture
    def service(self):
        """Фикстура сервиса"""
        return MultilevelReferralService()
    
    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_add_referral_success(self, service, mock_db):
        """Тест успешного добавления реферала"""
        # Настройка моков
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # Пользователь не найден
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [None, 1]  # Уровень реферера = 1
        
        # Выполнение
        result = await service.add_referral(user_id=123, referrer_id=456)
        
        # Проверки
        assert result["user_id"] == 123
        assert result["referrer_id"] == 456
        assert result["level"] == 2  # Уровень реферера + 1
        assert "created_at" in result
    
    @pytest.mark.asyncio
    async def test_add_referral_user_already_exists(self, service, mock_db):
        """Тест добавления уже существующего пользователя"""
        # Настройка моков
        mock_db.execute.return_value.scalar_one_or_none.return_value = ReferralTree()  # Пользователь уже существует
        
        # Выполнение и проверка исключения
        with pytest.raises(BusinessLogicError, match="уже в реферальной системе"):
            await service.add_referral(user_id=123, referrer_id=456)
    
    @pytest.mark.asyncio
    async def test_add_referral_max_level(self, service, mock_db):
        """Тест добавления реферала на максимальном уровне"""
        # Настройка моков
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [None, 3]  # Реферер на 3-м уровне
        
        # Выполнение
        result = await service.add_referral(user_id=123, referrer_id=456)
        
        # Проверки
        assert result["level"] == 3  # Максимальный уровень
    
    @pytest.mark.asyncio
    async def test_process_referral_bonus_no_referrals(self, service, mock_db):
        """Тест обработки бонусов без рефералов"""
        # Настройка моков
        service._get_referral_chain = AsyncMock(return_value={})  # Нет рефералов
        
        # Выполнение
        result = await service.process_referral_bonus(
            transaction_id=1,
            user_id=123,
            amount=Decimal('100.00')
        )
        
        # Проверки
        assert result["bonuses_processed"] == 0
        assert result["total_amount"] == Decimal('0')
    
    @pytest.mark.asyncio
    async def test_process_referral_bonus_with_referrals(self, service, mock_db):
        """Тест обработки бонусов с рефералами"""
        # Настройка моков
        service._get_referral_chain = AsyncMock(return_value={
            1: 456,  # Реферер 1-го уровня
            2: 789   # Реферер 2-го уровня
        })
        service._add_loyalty_bonus = AsyncMock()
        
        # Выполнение
        result = await service.process_referral_bonus(
            transaction_id=1,
            user_id=123,
            amount=Decimal('100.00')
        )
        
        # Проверки
        assert result["bonuses_processed"] == 2
        assert result["total_amount"] == Decimal('80.00')  # 50% + 30%
        assert result["transaction_id"] == 1
    
    @pytest.mark.asyncio
    async def test_process_referral_bonus_minimum_amounts(self, service, mock_db):
        """Тест обработки бонусов с минимальными суммами"""
        # Настройка моков
        service._get_referral_chain = AsyncMock(return_value={
            1: 456,  # Реферер 1-го уровня
            2: 789,  # Реферер 2-го уровня
            3: 101   # Реферер 3-го уровня
        })
        service._add_loyalty_bonus = AsyncMock()
        
        # Выполнение с малой суммой
        result = await service.process_referral_bonus(
            transaction_id=1,
            user_id=123,
            amount=Decimal('5.00')  # Малая сумма
        )
        
        # Проверки - только 1-й уровень должен получить бонус (2.50 > 2.00 минимум)
        assert result["bonuses_processed"] == 1
        assert result["total_amount"] == Decimal('2.50')
    
    @pytest.mark.asyncio
    async def test_get_referral_tree(self, service, mock_db):
        """Тест получения дерева рефералов"""
        # Настройка моков
        mock_referrals = [
            ReferralTree(user_id=111, level=1, total_earnings=Decimal('50.00'), total_referrals=2),
            ReferralTree(user_id=222, level=1, total_earnings=Decimal('30.00'), total_referrals=1),
            ReferralTree(user_id=333, level=2, total_earnings=Decimal('20.00'), total_referrals=0)
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_referrals
        
        # Выполнение
        result = await service.get_referral_tree(user_id=123)
        
        # Проверки
        assert result["user_id"] == 123
        assert result["total_referrals"] == 3
        assert result["total_earnings"] == Decimal('100.00')
        assert 1 in result["levels"]
        assert 2 in result["levels"]
        assert result["levels"][1]["count"] == 2
        assert result["levels"][2]["count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_referral_stats_existing(self, service, mock_db):
        """Тест получения существующей статистики"""
        # Настройка моков
        mock_stats = ReferralStats(
            user_id=123,
            level_1_count=5,
            level_2_count=3,
            level_3_count=1,
            level_1_earnings=Decimal('100.00'),
            level_2_earnings=Decimal('60.00'),
            level_3_earnings=Decimal('20.00'),
            total_referrals=9,
            total_earnings=Decimal('180.00'),
            last_updated=datetime.utcnow()
        )
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_stats
        
        # Выполнение
        result = await service.get_referral_stats(user_id=123)
        
        # Проверки
        assert result["user_id"] == 123
        assert result["level_1"]["count"] == 5
        assert result["level_1"]["earnings"] == 100.0
        assert result["level_2"]["count"] == 3
        assert result["level_2"]["earnings"] == 60.0
        assert result["level_3"]["count"] == 1
        assert result["level_3"]["earnings"] == 20.0
        assert result["total_referrals"] == 9
        assert result["total_earnings"] == 180.0
    
    @pytest.mark.asyncio
    async def test_get_referral_stats_not_existing(self, service, mock_db):
        """Тест получения статистики для нового пользователя"""
        # Настройка моков
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # Статистика не найдена
        
        # Выполнение
        result = await service.get_referral_stats(user_id=123)
        
        # Проверки
        assert result["user_id"] == 123
        assert result["level_1"]["count"] == 0
        assert result["level_1"]["earnings"] == 0
        assert result["level_2"]["count"] == 0
        assert result["level_2"]["earnings"] == 0
        assert result["level_3"]["count"] == 0
        assert result["level_3"]["earnings"] == 0
        assert result["total_referrals"] == 0
        assert result["total_earnings"] == 0
        assert result["last_updated"] is None
    
    def test_level_percentages(self, service):
        """Тест процентов бонусов по уровням"""
        assert service.level_percentages[1] == 0.50  # 50%
        assert service.level_percentages[2] == 0.30  # 30%
        assert service.level_percentages[3] == 0.20  # 20%
    
    def test_minimum_bonus_amounts(self, service):
        """Тест минимальных сумм бонусов"""
        assert service.min_bonus_amounts[1] == Decimal('10.00')
        assert service.min_bonus_amounts[2] == Decimal('5.00')
        assert service.min_bonus_amounts[3] == Decimal('2.00')


class TestReferralTreeModel:
    """Тесты модели ReferralTree"""
    
    def test_referral_tree_creation(self):
        """Тест создания записи ReferralTree"""
        referral = ReferralTree(
            user_id=123,
            referrer_id=456,
            level=1,
            total_earnings=Decimal('100.00'),
            total_referrals=5
        )
        
        assert referral.user_id == 123
        assert referral.referrer_id == 456
        assert referral.level == 1
        assert referral.total_earnings == Decimal('100.00')
        assert referral.total_referrals == 5
        assert referral.created_at is not None


class TestReferralBonusModel:
    """Тесты модели ReferralBonus"""
    
    def test_referral_bonus_creation(self):
        """Тест создания записи ReferralBonus"""
        bonus = ReferralBonus(
            referrer_id=456,
            referred_id=123,
            level=1,
            bonus_amount=Decimal('50.00'),
            source_transaction_id=789
        )
        
        assert bonus.referrer_id == 456
        assert bonus.referred_id == 123
        assert bonus.level == 1
        assert bonus.bonus_amount == Decimal('50.00')
        assert bonus.source_transaction_id == 789
        assert bonus.created_at is not None


class TestReferralStatsModel:
    """Тесты модели ReferralStats"""
    
    def test_referral_stats_creation(self):
        """Тест создания записи ReferralStats"""
        stats = ReferralStats(
            user_id=123,
            level_1_count=5,
            level_2_count=3,
            level_3_count=1,
            level_1_earnings=Decimal('100.00'),
            level_2_earnings=Decimal('60.00'),
            level_3_earnings=Decimal('20.00'),
            total_referrals=9,
            total_earnings=Decimal('180.00')
        )
        
        assert stats.user_id == 123
        assert stats.level_1_count == 5
        assert stats.level_2_count == 3
        assert stats.level_3_count == 1
        assert stats.level_1_earnings == Decimal('100.00')
        assert stats.level_2_earnings == Decimal('60.00')
        assert stats.level_3_earnings == Decimal('20.00')
        assert stats.total_referrals == 9
        assert stats.total_earnings == Decimal('180.00')
        assert stats.created_at is not None
