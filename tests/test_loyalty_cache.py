import pytest
from unittest.mock import patch, MagicMock, ANY
from core.services.loyalty import LoyaltyService, loyalty_service
from core.services.cache import cache_service
from core.database.db_v2 import db_v2

# Импортируем настройки для тестовой БД
from core.settings import settings as app_settings

# Переопределяем настройки БД для тестов
app_settings.database.url = "sqlite:///:memory:"

@pytest.fixture(autouse=True)
def init_test_db():
    """Инициализируем тестовую БД и создаем таблицы"""
    # Создаем тестовые таблицы
    with db_v2.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loyalty_wallets (
                user_id INTEGER PRIMARY KEY,
                balance_pts INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS loyalty_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                delta_pts INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                ref INTEGER,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    yield  # Тесты выполняются здесь
    
    # Очищаем таблицы после тестов
    with db_v2.get_connection() as conn:
        conn.execute("DELETE FROM loyalty_wallets")
        conn.execute("DELETE FROM loyalty_transactions")

@pytest.mark.asyncio
@patch('core.services.cache.cache_service')
async def test_get_balance_caching(mock_cache, init_test_db):
    # Настраиваем мок для кэша
    mock_cache.get.return_value = None
    
    # Тестируем кэширование
    user_id = 1
    
    # Создаем тестовый кошелек
    with db_v2.get_connection() as conn:
        conn.execute("INSERT INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)", (user_id, 0))
    
    # Первый вызов - должен пойти в БД
    balance = await loyalty_service.get_balance(user_id)
    assert balance == 0
    
    # Проверяем, что значение закэшировалось
    mock_cache.set.assert_called_once_with(f"loyalty:balance:{user_id}", '0', ex=300)
    
    # Настраиваем мок для возврата закэшированного значения
    mock_cache.get.return_value = "100"
    mock_cache.reset_mock()
    
    # Второй вызов - должно быть закэшировано
    balance = await loyalty_service.get_balance(user_id)
    assert balance == 100
    assert not mock_cache.set.called  # Не должно быть вызова set

@pytest.mark.asyncio
@patch('core.services.cache.cache_service')
async def test_adjust_balance_cache_invalidation(mock_cache, init_test_db):
    user_id = 2
    
    # Создаем тестовый кошелек
    with db_v2.get_connection() as conn:
        conn.execute("INSERT INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)", (user_id, 0))
    
    # Добавляем баллы
    await loyalty_service.adjust_balance(user_id, 50, "Test")
    
    # Проверяем, что кэш был обновлен с новым значением
    mock_cache.set.assert_called_with(f"loyalty:balance:{user_id}", '50', ex=1)

@pytest.mark.asyncio
@patch('core.services.cache.cache_service')
async def test_get_recent_transactions_caching(mock_cache, init_test_db):
    user_id = 3
    
    # Настраиваем мок для кэша
    mock_cache.get.return_value = None
    
    # Создаем тестовые транзакции
    with db_v2.get_connection() as conn:
        conn.execute("""
            INSERT INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)
        """, (user_id, 100))
        
        conn.execute("""
            INSERT INTO loyalty_transactions 
            (user_id, kind, delta_pts, balance_after, note)
            VALUES (?, 'accrual', 100, 100, 'Test')
        """, (user_id,))
    
    # Первый вызов - должен пойти в БД
    txs = await loyalty_service.get_recent_transactions(user_id)
    assert len(txs) == 1
    assert txs[0]['kind'] == 'accrual'
    
    # Проверяем, что данные закэшировались
    import json
    mock_cache.set.assert_called_once()
    args, kwargs = mock_cache.set.call_args
    assert args[0] == f"loyalty:tx_history:{user_id}:10"
    assert json.loads(args[1])[0]['kind'] == 'accrual'
    assert kwargs['ex'] == 60
    
    # Настраиваем мок для возврата закэшированного значения
    test_data = json.dumps([{'id': 1, 'kind': 'accrual', 'delta_pts': 50}])
    mock_cache.get.return_value = test_data
    mock_cache.reset_mock()
    
    # Второй вызов - должно быть закэшировано
    txs = await loyalty_service.get_recent_transactions(user_id)
    assert txs == [{'id': 1, 'kind': 'accrual', 'delta_pts': 50}]
    assert not mock_cache.set.called  # Не должно быть вызова set
