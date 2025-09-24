"""
Временный обработчик для исправления каталога в продакшене
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from core.database.migrations import diagnose_and_fix_catalog

logger = logging.getLogger(__name__)

# Создаем временный роутер
temp_router = Router()

@temp_router.message(Command("fix_catalog"))
async def cmd_fix_catalog(message: Message):
    """ВРЕМЕННАЯ команда для исправления каталога в продакшене"""
    
    # Проверяем что это супер-админ
    if message.from_user.id != 6391215556:
        await message.reply("❌ Доступ запрещен. Только супер-админ может использовать эту команду.")
        return
        
    await message.reply("🔧 Начинаю диагностику и исправление каталога в продакшене...")
    
    try:
        # Запускаем диагностику и исправление
        await diagnose_and_fix_catalog()
        
        await message.reply("✅ Каталог исправлен! Проверьте все категории в боте.")
        logger.info("✅ Команда /fix_catalog выполнена успешно")
        
    except Exception as e:
        error_msg = f"❌ Ошибка при исправлении каталога: {e}"
        await message.reply(error_msg)
        logger.error(f"❌ Ошибка команды /fix_catalog: {e}")

@temp_router.message(Command("catalog_status"))
async def cmd_catalog_status(message: Message):
    """Команда для проверки статуса каталога"""
    
    # Проверяем что это супер-админ
    if message.from_user.id != 6391215556:
        await message.reply("❌ Доступ запрещен. Только супер-админ может использовать эту команду.")
        return
        
    await message.reply("🔍 Проверяю статус каталога...")
    
    try:
        # Запускаем только диагностику без исправления
        await diagnose_and_fix_catalog()
        
        await message.reply("✅ Диагностика завершена. Проверьте логи для подробностей.")
        
    except Exception as e:
        error_msg = f"❌ Ошибка при диагностике: {e}"
        await message.reply(error_msg)
        logger.error(f"❌ Ошибка команды /catalog_status: {e}")
