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
    # Заглушка - возвращаем роль пользователя по умолчанию
    return Role(name="user", permissions=["basic"])

def has_permission(role: Role, permission: str) -> bool:
    """Проверить есть ли у роли определенное разрешение"""
    return permission in (role.permissions or [])
