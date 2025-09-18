# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class AdminController(http.Controller):
    
    @http.route('/karmabot/admin/dashboard', type='http', auth='public', website=True)
    def admin_dashboard(self, **kwargs):
        """Admin dashboard page"""
        return request.render('karmabot_webapp.admin_dashboard', {})
    
    @http.route('/karmabot/admin/users', type='http', auth='public', website=True)
    def admin_users(self, **kwargs):
        """Admin users management page"""
        return request.render('karmabot_webapp.admin_users', {})
    
    @http.route('/karmabot/admin/analytics', type='http', auth='public', website=True)
    def admin_analytics(self, **kwargs):
        """Admin analytics page"""
        return request.render('karmabot_webapp.admin_analytics', {})