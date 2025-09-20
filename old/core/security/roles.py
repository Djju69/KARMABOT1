"""
Модуль для управления ролями и разрешениями.
"""
from enum import Enum, auto
from typing import Set, Dict, List
from functools import wraps
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core.settings import settings

class Permission(Enum):
    """Разрешения для ролей"""
    # Просмотр каталога
    VIEW_CATALOG = auto()
    
    # Управление профилем
    MANAGE_OWN_PROFILE = auto()
    
    # Работа с карточками
    CREATE_CARD = auto()
    EDIT_OWN_CARD = auto()
    VIEW_OWN_CARDS = auto()
    DELETE_OWN_CARD = auto()
    
    # Модерация
    MODERATE_CARDS = auto()
    MODERATE_REVIEWS = auto()
    MANAGE_PARTNERS = auto()
    
    # Администрирование
    MANAGE_CATEGORIES = auto()
    MANAGE_DISCOUNTS = auto()
    MANAGE_LOYALTY = auto()
    VIEW_STATISTICS = auto()
    
    # Суперадмин
    MANAGE_ADMINS = auto()
    MANAGE_SETTINGS = auto()
    VIEW_AUDIT_LOG = auto()
    MANAGE_CARDS = auto()


class Role(Enum):
    """Роли пользователей"""
    USER = {
        Permission.VIEW_CATALOG,
        Permission.MANAGE_OWN_PROFILE,
        Permission.VIEW_OWN_CARDS
    }
    
    PARTNER = {
        Permission.VIEW_CATALOG,
        Permission.MANAGE_OWN_PROFILE,
        Permission.CREATE_CARD,
        Permission.EDIT_OWN_CARD,
        Permission.VIEW_OWN_CARDS,
        Permission.DELETE_OWN_CARD
    }
    
    MODERATOR = {
        Permission.VIEW_CATALOG,
        Permission.MANAGE_OWN_PROFILE,
        Permission.VIEW_OWN_CARDS,
        Permission.CREATE_CARD,
        Permission.EDIT_OWN_CARD,
        Permission.DELETE_OWN_CARD,
        Permission.MODERATE_CARDS,
        Permission.MODERATE_REVIEWS,
        Permission.VIEW_STATISTICS
    }
    
    ADMIN = {
        Permission.VIEW_CATALOG,
        Permission.MANAGE_OWN_PROFILE,
        Permission.MANAGE_PARTNERS,
        Permission.MANAGE_CATEGORIES,
        Permission.MANAGE_DISCOUNTS,
        Permission.MANAGE_LOYALTY,
        Permission.VIEW_STATISTICS,
        Permission.MODERATE_CARDS,
        Permission.MODERATE_REVIEWS
    }
    
    SUPER_ADMIN = set(Permission)


def has_permission(required_permission: Permission, user_role: Role) -> bool:
    """Проверяет, есть ли у роли указанное разрешение"""
    return required_permission in user_role.value


def require_permission(permission: Permission):
    """Декоратор для проверки прав доступа к хендлерам"""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: Message | CallbackQuery, state: FSMContext, *args, **kwargs):
            user_role = await get_user_role(message.from_user.id)
            
            if not has_permission(permission, user_role):
                if isinstance(message, CallbackQuery):
                    await message.answer("У вас недостаточно прав для этого действия")
                else:
                    await message.answer("У вас недостаточно прав для этого действия")
                return
                
            return await handler(message, state, *args, **kwargs)
        return wrapper
    return decorator


async def get_user_role(user_id: int) -> Role:
    """
    Получает роль пользователя из базы данных.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Role: Роль пользователя
    """
    from core.database import role_repository
    from core.settings import settings
    
    # Проверяем, является ли пользователь суперадмином
    if user_id == settings.bots.admin_id:
        return Role.SUPER_ADMIN
        
    # Получаем роль из базы данных
    role = await role_repository.get_user_role(user_id)
    return role or Role.USER  # По умолчанию USER


def get_available_roles() -> List[Dict]:
    """Возвращает список всех ролей с описанием"""
    return [
        {"name": "Пользователь", "value": "USER", "permissions": [p.name for p in Role.USER.value]},
        {"name": "Партнёр", "value": "PARTNER", "permissions": [p.name for p in Role.PARTNER.value]},
        {"name": "Модератор", "value": "MODERATOR", "permissions": [p.name for p in Role.MODERATOR.value]},
        {"name": "Администратор", "value": "ADMIN", "permissions": [p.name for p in Role.ADMIN.value]},
        {"name": "Суперадмин", "value": "SUPER_ADMIN", "permissions": [p.name for p in Role.SUPER_ADMIN.value]},
    ]
