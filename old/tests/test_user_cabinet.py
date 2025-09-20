"""
Тесты для кабинета пользователя
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext
from core.handlers.cabinet_router import (
    view_cards_handler,
    view_karma_handler,
    view_history_handler,
    language_handler,
    add_card_qr_callback,
    add_card_manual_callback,
    add_card_virtual_callback,
    spend_points_callback,
    cancel_spend_callback
)


class TestUserCabinet:
    """Тесты кабинета пользователя"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.user_id = 123456789
        self.user = User(
            id=self.user_id,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        self.message = Mock(spec=Message)
        self.message.from_user = self.user
        self.message.answer = AsyncMock()
        self.message.edit_text = AsyncMock()
        
        self.callback = Mock(spec=CallbackQuery)
        self.callback.from_user = self.user
        self.callback.message = self.message
        self.callback.answer = AsyncMock()
        
        self.state = Mock(spec=FSMContext)
        self.state.set_state = AsyncMock()
        self.state.clear = AsyncMock()
        self.state.get_data = AsyncMock(return_value={'lang': 'ru'})
    
    @pytest.mark.asyncio
    async def test_view_cards_handler_no_cards(self):
        """Тест просмотра карт когда карт нет"""
        with patch('core.handlers.cabinet_router.user_cabinet_service') as mock_service:
            mock_service.get_user_cards = AsyncMock(return_value=[])
            
            await view_cards_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Мои карты" in call_args[0][0]
            assert "нет привязанных карт" in call_args[0][0]
            assert "Способы добавления карт" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_view_cards_handler_with_cards(self):
        """Тест просмотра карт когда карты есть"""
        mock_cards = [
            {
                'card_id_printable': '1234-5678-90',
                'bound_at': Mock(strftime=Mock(return_value='01.01.2024')),
                'is_blocked': False
            }
        ]
        
        with patch('core.handlers.cabinet_router.user_cabinet_service') as mock_service:
            mock_service.get_user_cards = AsyncMock(return_value=mock_cards)
            
            await view_cards_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Мои карты" in call_args[0][0]
            assert "1234-5678-90" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_view_karma_handler_with_points(self):
        """Тест просмотра баллов когда баллы есть"""
        mock_profile = {
            'karma_points': 500,
            'loyalty_points': 250
        }
        
        with patch('core.handlers.cabinet_router.user_cabinet_service') as mock_service:
            mock_service.get_user_profile = AsyncMock(return_value=mock_profile)
            
            await view_karma_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Мои баллы" in call_args[0][0]
            assert "500" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_view_karma_handler_no_points(self):
        """Тест просмотра баллов когда баллов нет"""
        mock_profile = {
            'karma_points': 0,
            'loyalty_points': 0
        }
        
        with patch('core.handlers.cabinet_router.user_cabinet_service') as mock_service:
            mock_service.get_user_profile = AsyncMock(return_value=mock_profile)
            
            await view_karma_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "недостаточно кармы" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_view_history_handler_with_transactions(self):
        """Тест просмотра истории когда есть транзакции"""
        mock_history = {
            'transactions': [
                {
                    'description': 'QR scan reward',
                    'amount': 50,
                    'created_at': '2024-01-01',
                    'status': 'completed'
                }
            ],
            'total': 1
        }
        
        with patch('core.handlers.cabinet_router.user_cabinet_service') as mock_service:
            mock_service.get_transaction_history = AsyncMock(return_value=mock_history)
            
            await view_history_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Последние операции" in call_args[0][0]
            assert "QR scan reward" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_view_history_handler_no_transactions(self):
        """Тест просмотра истории когда транзакций нет"""
        mock_history = {'transactions': [], 'total': 0}
        
        with patch('core.handlers.cabinet_router.user_cabinet_service') as mock_service:
            mock_service.get_transaction_history = AsyncMock(return_value=mock_history)
            
            await view_history_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "нет истории операций" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_language_handler(self):
        """Тест обработчика языка"""
        with patch('core.handlers.cabinet_router.build_language_inline_kb') as mock_kb:
            mock_keyboard = Mock()
            mock_kb.return_value = mock_keyboard
            
            await language_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Выбор языка" in call_args[0][0]


class TestUserCabinetCallbacks:
    """Тесты callback'ов кабинета пользователя"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.user_id = 123456789
        self.user = User(
            id=self.user_id,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        self.message = Mock(spec=Message)
        self.message.from_user = self.user
        self.message.edit_text = AsyncMock()
        
        self.callback = Mock(spec=CallbackQuery)
        self.callback.from_user = self.user
        self.callback.message = self.message
        self.callback.answer = AsyncMock()
        self.callback.data = "add_card_qr"
        
        self.state = Mock(spec=FSMContext)
        self.state.set_state = AsyncMock()
        self.state.clear = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_add_card_qr_callback(self):
        """Тест callback'а добавления карты через QR"""
        self.callback.data = "add_card_qr"
        
        await add_card_qr_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Сканирование QR-кода" in call_args[0][0]
        assert "KARMA_QR:" in call_args[0][0]
        
        # Проверить что состояние установлено
        self.state.set_state.assert_called_once()
        self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_card_manual_callback(self):
        """Тест callback'а добавления карты вручную"""
        self.callback.data = "add_card_manual"
        
        await add_card_manual_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Ввод номера карты" in call_args[0][0]
        assert "только цифры" in call_args[0][0]
        
        # Проверить что состояние установлено
        self.state.set_state.assert_called_once()
        self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_card_virtual_callback(self):
        """Тест callback'а создания виртуальной карты"""
        self.callback.data = "add_card_virtual"
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "1234567890abcdef"
            
            await add_card_virtual_callback(self.callback, self.state)
            
            # Проверить что сообщение отредактировано
            self.message.edit_text.assert_called_once()
            call_args = self.message.edit_text.call_args
            assert "Виртуальная карта создана" in call_args[0][0]
            assert "V12345678" in call_args[0][0]
            
            self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_spend_points_callback(self):
        """Тест callback'а списания баллов"""
        self.callback.data = "spend_points_200"
        
        await spend_points_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Баллы успешно списаны" in call_args[0][0]
        assert "200 баллов" in call_args[0][0]
        assert "10%" in call_args[0][0]
        
        self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_spend_callback(self):
        """Тест callback'а отмены списания баллов"""
        self.callback.data = "cancel_spend"
        
        await cancel_spend_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Списание баллов отменено" in call_args[0][0]
        
        # Проверить что состояние очищено
        self.state.clear.assert_called_once()
        self.callback.answer.assert_called_once()


class TestUserCabinetStates:
    """Тесты состояний кабинета пользователя"""
    
    def test_cabinet_states_defined(self):
        """Тест что все состояния кабинета определены"""
        from core.handlers.cabinet_router import CabinetStates
        
        # Проверить что все состояния определены
        assert hasattr(CabinetStates, 'viewing_profile')
        assert hasattr(CabinetStates, 'viewing_balance')
        assert hasattr(CabinetStates, 'viewing_history')
        assert hasattr(CabinetStates, 'viewing_cards')
        assert hasattr(CabinetStates, 'viewing_notifications')
        assert hasattr(CabinetStates, 'viewing_achievements')
        assert hasattr(CabinetStates, 'spending_points')
        assert hasattr(CabinetStates, 'viewing_settings')
        
        # Проверить новые состояния для добавления карт
        assert hasattr(CabinetStates, 'adding_card_qr')
        assert hasattr(CabinetStates, 'adding_card_manual')
        assert hasattr(CabinetStates, 'adding_card_virtual')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
