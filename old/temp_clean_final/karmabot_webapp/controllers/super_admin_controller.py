# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class SuperAdminController(http.Controller):
    """Контроллер для супер-админских функций"""
    
    @http.route('/karmabot/superadmin/dashboard', type='http', auth='public', website=True)
    def superadmin_dashboard(self, **kw):
        """Супер-админская панель"""
        try:
            return request.render('karmabot_webapp.superadmin_dashboard', {})
        except Exception as e:
            _logger.error(f"Error in superadmin_dashboard: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки супер-админской панели'})
    
    @http.route('/karmabot/superadmin/settings', type='http', auth='public', website=True)
    def superadmin_settings(self, **kw):
        """Системные настройки"""
        try:
            return request.render('karmabot_webapp.superadmin_settings', {})
        except Exception as e:
            _logger.error(f"Error in superadmin_settings: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки настроек'})
    
    @http.route('/karmabot/superadmin/modules', type='http', auth='public', website=True)
    def superadmin_modules(self, **kw):
        """Управление модулями"""
        try:
            return request.render('karmabot_webapp.superadmin_modules', {})
        except Exception as e:
            _logger.error(f"Error in superadmin_modules: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки модулей'})