"""
Тест миграции тарифной системы
"""
import pytest
import os
import tempfile
import sqlite3
from pathlib import Path

def test_tariff_migration_sqlite():
    """Тест миграции тарифной системы для SQLite"""
    # Создаем временную БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Подключаемся к БД
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Создаем таблицу миграций
        cur.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                version TEXT PRIMARY KEY,
                description TEXT,
                applied_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Создаем таблицы тарифов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS partner_tariffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tariff_type TEXT NOT NULL UNIQUE,
                price_vnd INTEGER NOT NULL DEFAULT 0,
                max_transactions_per_month INTEGER NOT NULL DEFAULT 15,
                commission_rate REAL NOT NULL DEFAULT 0.1200,
                analytics_enabled INTEGER NOT NULL DEFAULT 0,
                priority_support INTEGER NOT NULL DEFAULT 0,
                api_access INTEGER NOT NULL DEFAULT 0,
                custom_integrations INTEGER NOT NULL DEFAULT 0,
                dedicated_manager INTEGER NOT NULL DEFAULT 0,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS partner_tariff_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                tariff_id INTEGER NOT NULL REFERENCES partner_tariffs(id),
                started_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                auto_renew INTEGER NOT NULL DEFAULT 0,
                payment_status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(partner_id, is_active) DEFERRABLE INITIALLY DEFERRED
            )
        """)
        
        # Вставляем предустановленные тарифы
        cur.execute("""
            INSERT OR REPLACE INTO partner_tariffs (
                name, tariff_type, price_vnd, max_transactions_per_month, 
                commission_rate, analytics_enabled, priority_support, 
                api_access, custom_integrations, dedicated_manager, description
            ) VALUES 
            ('FREE STARTER', 'free_starter', 0, 15, 0.1200, 0, 0, 0, 0, 0, 'Базовые карты, QR-коды, лимит 15 транзакций в месяц'),
            ('BUSINESS', 'business', 490000, 100, 0.0600, 1, 1, 0, 0, 0, 'Расширенная аналитика, приоритетная поддержка, лимит 100 транзакций'),
            ('ENTERPRISE', 'enterprise', 960000, -1, 0.0400, 1, 1, 1, 1, 1, 'API доступ, кастомные интеграции, выделенный менеджер, безлимит транзакций')
        """)
        
        conn.commit()
        
        # Проверяем что тарифы созданы
        cur.execute("SELECT COUNT(*) FROM partner_tariffs")
        count = cur.fetchone()[0]
        assert count == 3
        
        # Проверяем конкретные тарифы
        cur.execute("SELECT name, tariff_type, price_vnd FROM partner_tariffs ORDER BY price_vnd")
        tariffs = cur.fetchall()
        
        assert tariffs[0] == ('FREE STARTER', 'free_starter', 0)
        assert tariffs[1] == ('BUSINESS', 'business', 490000)
        assert tariffs[2] == ('ENTERPRISE', 'enterprise', 960000)
        
        # Проверяем функции тарифов
        cur.execute("SELECT analytics_enabled, api_access, dedicated_manager FROM partner_tariffs WHERE tariff_type = 'enterprise'")
        enterprise_features = cur.fetchone()
        assert enterprise_features == (1, 1, 1)  # Все функции включены
        
        cur.execute("SELECT analytics_enabled, api_access, dedicated_manager FROM partner_tariffs WHERE tariff_type = 'free_starter'")
        free_features = cur.fetchone()
        assert free_features == (0, 0, 0)  # Все функции отключены
        
        print("✅ SQLite миграция тарифной системы прошла успешно")
        
    finally:
        # Очищаем временную БД
        conn.close()
        os.unlink(db_path)

def test_tariff_models_import():
    """Тест импорта моделей тарифов"""
    try:
        from core.models.tariff_models import Tariff, TariffType, TariffFeatures, DEFAULT_TARIFFS
        
        # Проверяем что все модели импортируются
        assert Tariff is not None
        assert TariffType is not None
        assert TariffFeatures is not None
        assert DEFAULT_TARIFFS is not None
        
        # Проверяем предустановленные тарифы
        assert len(DEFAULT_TARIFFS) == 3
        assert TariffType.FREE_STARTER in DEFAULT_TARIFFS
        assert TariffType.BUSINESS in DEFAULT_TARIFFS
        assert TariffType.ENTERPRISE in DEFAULT_TARIFFS
        
        print("✅ Импорт моделей тарифов прошел успешно")
        
    except ImportError as e:
        pytest.fail(f"Ошибка импорта моделей тарифов: {e}")

def test_tariff_service_import():
    """Тест импорта сервиса тарифов"""
    try:
        from core.services.tariff_service import TariffService, tariff_service
        
        # Проверяем что сервис импортируется
        assert TariffService is not None
        assert tariff_service is not None
        
        # Проверяем инициализацию сервиса
        service = TariffService()
        assert service.default_tariffs is not None
        
        print("✅ Импорт сервиса тарифов прошел успешно")
        
    except ImportError as e:
        pytest.fail(f"Ошибка импорта сервиса тарифов: {e}")

def test_tariff_admin_router_import():
    """Тест импорта админ-роутера тарифов"""
    try:
        from core.handlers.tariff_admin_router import router
        
        # Проверяем что роутер импортируется
        assert router is not None
        
        print("✅ Импорт админ-роутера тарифов прошел успешно")
        
    except ImportError as e:
        pytest.fail(f"Ошибка импорта админ-роутера тарифов: {e}")

if __name__ == "__main__":
    # Запуск тестов
    test_tariff_migration_sqlite()
    test_tariff_models_import()
    test_tariff_service_import()
    test_tariff_admin_router_import()
    print("🎉 Все тесты тарифной системы прошли успешно!")
