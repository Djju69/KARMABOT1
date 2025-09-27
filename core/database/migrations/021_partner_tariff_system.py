"""
Миграция 021: Тарифная система для партнеров
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_tariffs_table():
    """Создать таблицу тарифов"""
    return """
    -- Таблица тарифов для партнеров
    CREATE TABLE IF NOT EXISTS partner_tariffs (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        tariff_type VARCHAR(50) NOT NULL UNIQUE,
        price_vnd INTEGER NOT NULL DEFAULT 0,
        max_transactions_per_month INTEGER NOT NULL DEFAULT 15,
        commission_rate DECIMAL(5,4) NOT NULL DEFAULT 0.1200,
        analytics_enabled BOOLEAN NOT NULL DEFAULT FALSE,
        priority_support BOOLEAN NOT NULL DEFAULT FALSE,
        api_access BOOLEAN NOT NULL DEFAULT FALSE,
        custom_integrations BOOLEAN NOT NULL DEFAULT FALSE,
        dedicated_manager BOOLEAN NOT NULL DEFAULT FALSE,
        description TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Индексы для оптимизации
    CREATE INDEX IF NOT EXISTS idx_partner_tariffs_type ON partner_tariffs(tariff_type);
    CREATE INDEX IF NOT EXISTS idx_partner_tariffs_active ON partner_tariffs(is_active);
    
    -- Триггер для обновления updated_at
    CREATE OR REPLACE FUNCTION update_tariffs_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    CREATE TRIGGER trigger_update_tariffs_updated_at
        BEFORE UPDATE ON partner_tariffs
        FOR EACH ROW
        EXECUTE FUNCTION update_tariffs_updated_at();
    """

def create_partner_tariff_subscriptions_table():
    """Создать таблицу подписок партнеров на тарифы"""
    return """
    -- Таблица подписок партнеров на тарифы
    CREATE TABLE IF NOT EXISTS partner_tariff_subscriptions (
        id SERIAL PRIMARY KEY,
        partner_id INTEGER NOT NULL,
        tariff_id INTEGER NOT NULL REFERENCES partner_tariffs(id),
        started_at TIMESTAMP NOT NULL DEFAULT NOW(),
        expires_at TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        auto_renew BOOLEAN NOT NULL DEFAULT FALSE,
        payment_status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        
        -- Ограничения
        CONSTRAINT unique_active_subscription UNIQUE (partner_id, is_active) DEFERRABLE INITIALLY DEFERRED
    );
    
    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_subscriptions_partner ON partner_tariff_subscriptions(partner_id);
    CREATE INDEX IF NOT EXISTS idx_subscriptions_tariff ON partner_tariff_subscriptions(tariff_id);
    CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON partner_tariff_subscriptions(is_active);
    CREATE INDEX IF NOT EXISTS idx_subscriptions_expires ON partner_tariff_subscriptions(expires_at);
    
    -- Триггер для обновления updated_at
    CREATE TRIGGER trigger_update_subscriptions_updated_at
        BEFORE UPDATE ON partner_tariff_subscriptions
        FOR EACH ROW
        EXECUTE FUNCTION update_tariffs_updated_at();
    """

def seed_default_tariffs():
    """Заполнить таблицу предустановленными тарифами"""
    return """
    -- Вставляем предустановленные тарифы
    INSERT INTO partner_tariffs (
        name, tariff_type, price_vnd, max_transactions_per_month, 
        commission_rate, analytics_enabled, priority_support, 
        api_access, custom_integrations, dedicated_manager, description
    ) VALUES 
    (
        'FREE STARTER', 'free_starter', 0, 15, 0.1200, 
        FALSE, FALSE, FALSE, FALSE, FALSE,
        'Базовые карты, QR-коды, лимит 15 транзакций в месяц'
    ),
    (
        'BUSINESS', 'business', 490000, 100, 0.0600,
        TRUE, TRUE, FALSE, FALSE, FALSE, 
        'Расширенная аналитика, приоритетная поддержка, лимит 100 транзакций'
    ),
    (
        'ENTERPRISE', 'enterprise', 960000, -1, 0.0400,
        TRUE, TRUE, TRUE, TRUE, TRUE,
        'API доступ, кастомные интеграции, выделенный менеджер, безлимит транзакций'
    )
    ON CONFLICT (tariff_type) DO UPDATE SET
        name = EXCLUDED.name,
        price_vnd = EXCLUDED.price_vnd,
        max_transactions_per_month = EXCLUDED.max_transactions_per_month,
        commission_rate = EXCLUDED.commission_rate,
        analytics_enabled = EXCLUDED.analytics_enabled,
        priority_support = EXCLUDED.priority_support,
        api_access = EXCLUDED.api_access,
        custom_integrations = EXCLUDED.custom_integrations,
        dedicated_manager = EXCLUDED.dedicated_manager,
        description = EXCLUDED.description,
        updated_at = NOW();
    """

def apply_migration_021():
    """Применить миграцию 021: Тарифная система"""
    try:
        logger.info("🚀 Applying migration 021: Partner tariff system")
        
        # Создаем таблицы
        tariffs_table_sql = create_tariffs_table()
        subscriptions_table_sql = create_partner_tariff_subscriptions_table()
        seed_tariffs_sql = seed_default_tariffs()
        
        logger.info("✅ Migration 021 applied successfully: Partner tariff system")
        return {
            'tariffs_table': tariffs_table_sql,
            'subscriptions_table': subscriptions_table_sql, 
            'seed_tariffs': seed_tariffs_sql
        }
        
    except Exception as e:
        logger.error(f"❌ Migration 021 failed: {e}")
        raise

if __name__ == "__main__":
    # Для тестирования миграции
    result = apply_migration_021()
    print("Migration 021 SQL:")
    print("=" * 50)
    print(result['tariffs_table'])
    print("\n" + "=" * 50)
    print(result['subscriptions_table'])
    print("\n" + "=" * 50)
    print(result['seed_tariffs'])
