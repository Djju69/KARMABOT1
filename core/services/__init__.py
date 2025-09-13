# core.services package
from .admins import admins_service
from .profile import profile_service
from .odoo_api import odoo_api

__all__ = ['admins_service', 'profile_service', 'odoo_api']
