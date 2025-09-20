# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import hashlib
import time

_logger = logging.getLogger(__name__)


class KarmaBotSSOToken(models.Model):
    _name = 'karmabot.sso_token'
    _description = 'KarmaBot SSO Token'
    _order = 'create_date desc'
    
    # Основные поля
    token = fields.Char(string='Token', required=True, index=True)
    user_id = fields.Many2one('karmabot.user', string='User', required=True)
    
    # Тип токена
    token_type = fields.Selection([
        ('webapp_sso', 'WebApp SSO'),
        ('api_access', 'API Access'),
        ('temp_access', 'Temporary Access')
    ], string='Token Type', default='webapp_sso', required=True)
    
    # Статус и срок действия
    is_active = fields.Boolean(string='Active', default=True)
    expires_at = fields.Datetime(string='Expires At')
    
    # Информация о создании
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    
    # Даты
    create_date = fields.Datetime(string='Created', default=fields.Datetime.now)
    last_used = fields.Datetime(string='Last Used')
    
    @api.constrains('token')
    def _check_token_unique(self):
        for record in self:
            if self.search_count([('token', '=', record.token), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Token must be unique'))
    
    @api.model
    def generate_token(self, user_id, token_type='webapp_sso', expires_hours=24):
        """Генерировать новый SSO токен"""
        # Создать уникальный токен
        timestamp = str(int(time.time()))
        random_data = f"{user_id}:{timestamp}:{token_type}"
        token_hash = hashlib.sha256(random_data.encode()).hexdigest()[:32]
        
        # Простой формат токена: user_id:timestamp:hash
        token = f"{user_id}:{timestamp}:{token_hash}"
        
        # Вычислить время истечения
        expires_at = fields.Datetime.now() + fields.timedelta(hours=expires_hours)
        
        # Создать запись токена
        sso_token = self.create({
            'token': token,
            'user_id': user_id,
            'token_type': token_type,
            'expires_at': expires_at,
            'is_active': True
        })
        
        return sso_token
    
    @api.model
    def validate_token(self, token):
        """Валидировать SSO токен"""
        if not token:
            return None
        
        # Найти токен
        sso_token = self.search([
            ('token', '=', token),
            ('is_active', '=', True)
        ], limit=1)
        
        if not sso_token:
            return None
        
        # Проверить срок действия
        if sso_token.expires_at and sso_token.expires_at < fields.Datetime.now():
            sso_token.is_active = False
            return None
        
        # Обновить время последнего использования
        sso_token.last_used = fields.Datetime.now()
        
        return {
            'user_id': sso_token.user_id.id,
            'telegram_id': sso_token.user_id.telegram_id,
            'token_type': sso_token.token_type,
            'expires_at': sso_token.expires_at
        }
    
    def deactivate_token(self):
        """Деактивировать токен"""
        self.is_active = False
    
    @api.model
    def cleanup_expired_tokens(self):
        """Очистить истекшие токены"""
        expired_tokens = self.search([
            ('expires_at', '<', fields.Datetime.now()),
            ('is_active', '=', True)
        ])
        
        if expired_tokens:
            expired_tokens.write({'is_active': False})
            _logger.info(f"Deactivated {len(expired_tokens)} expired SSO tokens")