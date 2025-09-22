# Минимальные заглушки для совместимости

from typing import Optional, Any
from dataclasses import dataclass

@dataclass
class Role:
    """Класс роли пользователя"""
    name: str
    permissions: list = None
    
    def __init__(self, name: str, permissions: list = None):
        self.name = name
        self.permissions = permissions or []

async def get_user_role(user_id: int) -> Role:
    """Получить роль пользователя по ID"""
    from core.settings import settings
    
    # Проверяем супер-админов из настроек
    if hasattr(settings, 'super_admins') and user_id in settings.super_admins:
        return Role(name="super_admin", permissions=["admin", "super_admin", "basic"])
    
    # Проверяем обычных админов
    if hasattr(settings, 'admins') and user_id in settings.admins:
        return Role(name="admin", permissions=["admin", "basic"])
    
    # Проверяем партнеров
    if hasattr(settings, 'partners') and user_id in settings.partners:
        return Role(name="partner", permissions=["partner", "basic"])
    
    # По умолчанию - обычный пользователь
    return Role(name="user", permissions=["basic"])

def has_permission(role: Role, permission: str) -> bool:
    """Проверить есть ли у роли определенное разрешение"""
    return permission in (role.permissions or [])
