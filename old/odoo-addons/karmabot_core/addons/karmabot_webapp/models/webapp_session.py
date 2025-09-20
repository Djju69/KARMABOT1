# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class KarmaBotWebAppSession(models.Model):
    _name = 'karmabot.webapp_session'
    _description = 'KarmaBot WebApp Session'
    _order = 'create_date desc'
    
    # Основные поля
    user_id = fields.Many2one('karmabot.user', string='User', required=True)
    session_type = fields.Selection([
        ('user_cabinet', 'User Cabinet'),
        ('partner_cabinet', 'Partner Cabinet'),
        ('admin_cabinet', 'Admin Cabinet'),
        ('super_admin_cabinet', 'Super Admin Cabinet')
    ], string='Session Type', required=True)
    
    # Информация о сессии
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    is_active = fields.Boolean(string='Active', default=True)
    
    # Даты
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    last_activity = fields.Datetime(string='Last Activity', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    
    # Дополнительные данные
    session_data = fields.Text(string='Session Data', help='JSON data for session')
    
    @api.model
    def create_session(self, user_id, session_type, ip_address=None, user_agent=None, session_data=None):
        """Создать новую сессию WebApp"""
        # Деактивировать предыдущие сессии пользователя
        self.search([('user_id', '=', user_id), ('is_active', '=', True)]).write({
            'is_active': False,
            'end_time': fields.Datetime.now()
        })
        
        # Создать новую сессию
        session = self.create({
            'user_id': user_id,
            'session_type': session_type,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'session_data': session_data,
            'is_active': True
        })
        
        _logger.info(f"Created new WebApp session for user {user_id}, type: {session_type}")
        return session
    
    def update_activity(self):
        """Обновить активность сессии"""
        self.last_activity = fields.Datetime.now()
    
    def end_session(self):
        """Завершить сессию"""
        self.is_active = False
        self.end_time = fields.Datetime.now()
        _logger.info(f"Ended WebApp session {self.id}")
    
    @api.model
    def cleanup_inactive_sessions(self, hours=24):
        """Очистить неактивные сессии старше указанного количества часов"""
        cutoff_time = fields.Datetime.now() - fields.timedelta(hours=hours)
        
        inactive_sessions = self.search([
            ('last_activity', '<', cutoff_time),
            ('is_active', '=', True)
        ])
        
        if inactive_sessions:
            inactive_sessions.write({
                'is_active': False,
                'end_time': fields.Datetime.now()
            })
            _logger.info(f"Cleaned up {len(inactive_sessions)} inactive WebApp sessions")
    
    @api.model
    def get_active_sessions(self, user_id=None):
        """Получить активные сессии"""
        domain = [('is_active', '=', True)]
        if user_id:
            domain.append(('user_id', '=', user_id))
        
        return self.search(domain)
    
    def get_session_duration(self):
        """Получить продолжительность сессии"""
        if not self.is_active:
            end_time = self.end_time or fields.Datetime.now()
            duration = end_time - self.start_time
        else:
            duration = fields.Datetime.now() - self.start_time
        
        return duration
    
    def get_session_info(self):
        """Получить информацию о сессии"""
        return {
            'id': self.id,
            'user_id': self.user_id.id,
            'user_name': self.user_id.name,
            'session_type': self.session_type,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'duration': self.get_session_duration(),
            'is_active': self.is_active,
            'ip_address': self.ip_address
        }