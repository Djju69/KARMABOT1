# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class AdminController(http.Controller):
    """Контроллер для админских функций"""
    
    @http.route('/karmabot/admin/dashboard', type='http', auth='public', website=True)
    def admin_dashboard(self, **kw):
        """Админская панель"""
        try:
            return request.render('karmabot_webapp.admin_dashboard', {})
        except Exception as e:
            _logger.error(f"Error in admin_dashboard: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки админской панели'})
    
    @http.route('/karmabot/admin/users', type='http', auth='public', website=True)
    def admin_users(self, **kw):
        """Управление пользователями"""
        try:
            return request.render('karmabot_webapp.admin_users', {})
        except Exception as e:
            _logger.error(f"Error in admin_users: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки пользователей'})
    
    @http.route('/karmabot/admin/analytics', type='http', auth='public', website=True)
    def admin_analytics(self, **kw):
        """Аналитика для админов"""
        try:
            return request.render('karmabot_webapp.admin_analytics', {})
        except Exception as e:
            _logger.error(f"Error in admin_analytics: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки аналитики'})