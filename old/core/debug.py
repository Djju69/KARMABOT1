"""
Debug utilities for checking feature flags and system status
"""
import logging
from typing import Dict, Any
from aiogram import types

from .settings import settings

logger = logging.getLogger(__name__)

def get_feature_flags() -> Dict[str, Any]:
    """Get current feature flags status"""
    return {
        'FEATURE_NEW_MENU': settings.features.new_menu,
        'FEATURE_PARTNER_FSM': settings.features.partner_fsm,
        'FEATURE_MODERATION': settings.features.moderation,
        'FEATURE_QR_WEBAPP': settings.features.qr_webapp,
        'FEATURE_LISTEN_NOTIFY': settings.features.listen_notify,
    }

async def cmd_debug_features(message: types.Message):
    """Debug command to show current feature flags"""
    flags = get_feature_flags()
    
    response = [
        "🔧 *Текущие настройки функций:*",
        "",
        "*Флаг* | *Статус*",
        "----------------"
    ]
    
    for flag, status in flags.items():
        status_icon = "✅" if status else "❌"
        response.append(f"`{flag}`: {status_icon} {status}")
    
    response.extend([
        "",
        "Для изменения используйте переменные окружения в настройках.",
        "Например: `FEATURE_NEW_MENU=true`"
    ])
    
    await message.answer("\n".join(response), parse_mode="Markdown")

def register_debug_handlers(dp):
    """Register debug command handlers"""
    from aiogram import Dispatcher
    from aiogram.dispatcher.filters import Command
    
    if not isinstance(dp, Dispatcher):
        logger.warning("Debug handlers not registered: invalid dispatcher")
        return
    
    dp.register_message_handler(
        cmd_debug_features, 
        Command("debug_features", prefixes="/!"),  # Less likely to conflict
        state="*"
    )
    logger.info("Debug command handlers registered")
