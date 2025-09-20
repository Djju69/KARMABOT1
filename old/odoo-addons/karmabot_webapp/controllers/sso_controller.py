# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class SSOController(http.Controller):
    """Контроллер для SSO функций"""
    
    @http.route('/karmabot/sso/login', type='http', auth='public', website=True)
    def sso_login(self, **kw):
        """SSO вход"""
        try:
            return request.render('karmabot_webapp.sso_login', {})
        except Exception as e:
            _logger.error(f"Error in sso_login: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка SSO входа'})
    
    @http.route('/karmabot/sso/logout', type='http', auth='public', website=True)
    def sso_logout(self, **kw):
        """SSO выход"""
        try:
            return request.render('karmabot_webapp.sso_logout', {})
        except Exception as e:
            _logger.error(f"Error in sso_logout: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка SSO выхода'})
    
    @http.route('/karmabot/sso/validate', type='http', auth='public', website=True)
    def sso_validate(self, **kw):
        """Валидация SSO токена"""
        try:
            return request.render('karmabot_webapp.sso_validate', {})
        except Exception as e:
            _logger.error(f"Error in sso_validate: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка валидации SSO'})