# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class SSOController(http.Controller):
    
    @http.route('/karmabot/sso/login', type='http', auth='public', website=True)
    def sso_login(self, **kwargs):
        """SSO login endpoint"""
        return request.render('karmabot_webapp.sso_login', {})
    
    @http.route('/karmabot/sso/callback', type='http', auth='public', website=True)
    def sso_callback(self, **kwargs):
        """SSO callback endpoint"""
        return request.render('karmabot_webapp.sso_callback', {})