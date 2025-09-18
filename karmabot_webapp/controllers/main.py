# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class WebappController(http.Controller):
    
    @http.route('/webapp', type='http', auth='public', website=True)
    def webapp_home(self, **kw):
        """Main webapp endpoint"""
        return request.render('karmabot_webapp.webapp_template', {
            'title': 'KarmaBot WebApp',
            'message': 'Welcome to KarmaBot WebApp'
        })
    
    @http.route('/webapp/api/test', type='json', auth='public')
    def api_test(self, **kw):
        """Test API endpoint"""
        return {
            'status': 'success',
            'message': 'KarmaBot WebApp API is working'
        }