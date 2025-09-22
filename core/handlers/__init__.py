"""
Core handlers module for KARMABOT1
"""
from .basic import router as basic_router
from .admin_cabinet import router as admin_router  
from .moderation import router as moderation_router
from .partner import partner_router
from .callback import router as callback_router
from .main_menu_router import router as main_menu_router
from .category_handlers_v2 import router as category_router
from .profile import router as profile_router
from .activity import router as activity_router
from .commands import router as commands_router
from .language import router as language_router
from . import ping

__all__ = [
    'basic_router',
    'admin_router', 
    'moderation_router',
    'partner_router',
    'callback_router',
    'main_menu_router',
    'category_router',
    'profile_router',
    'activity_router',
    'commands_router',
    'language_router',
    'ping'
]
