#!/usr/bin/env python3
"""
Проверка переменных окружения Railway
"""
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_railway_variables():
    """Проверка переменных Railway"""
    logger.info("🔍 Проверка переменных Railway...")
    
    # Обязательные переменные
    required_vars = [
        'BOT_TOKEN',
        'ADMIN_ID', 
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'PORT'
    ]
    
    # Railway переменные
    railway_vars = [
        'RAILWAY_ENVIRONMENT',
        'RAILWAY_STATIC_URL',
        'PORT'
    ]
    
    # Настройки бота
    bot_vars = [
        'DISABLE_POLLING',
        'WEBHOOK_URL'
    ]
    
    # Feature flags
    feature_vars = [
        'FEATURE_QR_WEBAPP',
        'FEATURE_PARTNER_FSM',
        'FEATURE_NEW_MENU',
        'FEATURE_MODERATION',
        'FEATURE_LISTEN_NOTIFY'
    ]
    
    # Проверяем обязательные переменные
    logger.info("\n📋 ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ:")
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * min(len(value), 10)}...")
        else:
            logger.error(f"❌ {var}: НЕ НАЙДЕНА")
            missing_required.append(var)
    
    # Проверяем Railway переменные
    logger.info("\n🚂 RAILWAY ПЕРЕМЕННЫЕ:")
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: НЕ НАЙДЕНА")
    
    # Проверяем настройки бота
    logger.info("\n🤖 НАСТРОЙКИ БОТА:")
    for var in bot_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: НЕ НАЙДЕНА")
    
    # Проверяем feature flags
    logger.info("\n🎛️ FEATURE FLAGS:")
    for var in feature_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: НЕ НАЙДЕНА")
    
    # Проверяем проблемные значения
    logger.info("\n🚨 ПРОБЛЕМНЫЕ ЗНАЧЕНИЯ:")
    problems = []
    
    disable_polling = os.getenv('DISABLE_POLLING')
    if disable_polling == '0':
        problems.append("DISABLE_POLLING=0 (должно быть true для Railway)")
    
    qr_webapp = os.getenv('FEATURE_QR_WEBAPP')
    if qr_webapp == '1':
        problems.append("FEATURE_QR_WEBAPP=1 (должно быть true)")
    
    if problems:
        for problem in problems:
            logger.error(f"❌ {problem}")
    else:
        logger.info("✅ Проблемных значений не найдено")
    
    # Итоговая оценка
    logger.info(f"\n📊 ИТОГОВАЯ ОЦЕНКА:")
    logger.info(f"Обязательных переменных: {len(required_vars) - len(missing_required)}/{len(required_vars)}")
    logger.info(f"Проблемных значений: {len(problems)}")
    
    if missing_required:
        logger.error(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_required)}")
        return False
    elif problems:
        logger.warning(f"⚠️ Найдены проблемные значения: {len(problems)}")
        return False
    else:
        logger.info("✅ Все переменные настроены корректно!")
        return True

if __name__ == "__main__":
    check_railway_variables()
