"""
Модуль для управления безопасностью и доступом.
Включает роли, разрешения, 2FA и проверки доступа.
"""
from .roles import Role, Permission, has_permission, require_permission, get_user_role, get_available_roles
from .two_factor_auth import TwoFactorAuth, two_factor_auth

__all__ = [
    'Role', 
    'Permission', 
    'has_permission', 
    'require_permission', 
    'get_user_role', 
    'get_available_roles',
    'TwoFactorAuth',
    'two_factor_auth'
]
