from odoo import http
from odoo.http import request

class TelegramController(http.Controller):
    
    @http.route('/telegram/login', type='http', auth='public', website=False)
    def telegram_login(self, telegram_id=None, username=None, **kw):
        """Страница входа для Telegram пользователей"""
        return request.render('karmabot_webapp.telegram_login_simple', {
            'telegram_id': telegram_id,
            'username': username,
        })
    
    @http.route('/telegram/auth', type='http', auth='public', methods=['POST'], website=False)
    def telegram_auth(self, telegram_id=None, username=None, **kw):
        """Аутентификация Telegram пользователя"""
        
        if not telegram_id:
            return request.redirect('/telegram/login')
        
        # Найти или создать пользователя
        user = request.env['res.users'].sudo().search([
            ('login', '=', f'telegram_{telegram_id}')
        ], limit=1)
        
        if not user:
            # Создать нового пользователя
            user = request.env['res.users'].sudo().create({
                'name': username or f'Telegram User {telegram_id}',
                'login': f'telegram_{telegram_id}',
                'email': f'telegram_{telegram_id}@example.com',
                'password': telegram_id,  # Простой пароль для демо
            })
        
        # Вход в систему
        request.session.authenticate(request.session.db, user.login, telegram_id)
        return request.redirect('/telegram/cabinet')
    
    @http.route('/telegram/cabinet', type='http', auth='user', website=False)
    def telegram_cabinet(self, **kw):
        """Личный кабинет"""
        return request.render('karmabot_webapp.telegram_cabinet_simple', {
            'user': request.env.user,
        })