# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class SuperAdminController(http.Controller):
    
    @http.route('/karmabot/superadmin/settings', type='http', auth='public', website=True)
    def superadmin_settings(self, **kwargs):
        """Super admin settings page"""
        return request.render('karmabot_webapp.superadmin_settings', {})
    
    @http.route('/karmabot/superadmin/modules', type='http', auth='public', website=True)
    def superadmin_modules(self, **kwargs):
        """Super admin modules management page"""
        return request.render('karmabot_webapp.superadmin_modules', {})
    
    @http.route('/karmabot/superadmin/admins', type='http', auth='public', website=True)
    def superadmin_admins(self, **kwargs):
        """Super admin admins management page"""
        return request.render('karmabot_webapp.superadmin_admins', {})
    
    @http.route('/karmabot/superadmin/security', type='http', auth='public', website=True)
    def superadmin_security(self, **kwargs):
        """Super admin security page"""
        return request.render('karmabot_webapp.superadmin_security', {})