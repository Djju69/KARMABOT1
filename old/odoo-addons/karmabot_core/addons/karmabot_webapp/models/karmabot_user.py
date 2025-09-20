# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class KarmaBotUser(models.Model):
    _name = 'karmabot.user'
    _description = 'KarmaBot User'
    _order = 'create_date desc'
    
    # Основные поля
    telegram_id = fields.Char(string='Telegram ID', required=True, index=True)
    display_name = fields.Char(string='Display Name', required=True)
    telegram_username = fields.Char(string='Telegram Username')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    city = fields.Char(string='City')
    
    # Роль и статус
    role = fields.Selection([
        ('user', 'User'),
        ('partner', 'Partner'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin')
    ], string='Role', default='user', required=True)
    
    is_active = fields.Boolean(string='Active', default=True)
    is_verified = fields.Boolean(string='Verified', default=False)
    
    # Баллы и статистика
    total_points = fields.Integer(string='Total Points', default=0)
    available_points = fields.Integer(string='Available Points', default=0)
    pending_points = fields.Integer(string='Pending Points', default=0)
    
    total_scans = fields.Integer(string='Total Scans', default=0)
    total_referrals = fields.Integer(string='Total Referrals', default=0)
    
    # Даты
    registration_date = fields.Datetime(string='Registration Date', default=fields.Datetime.now)
    last_activity = fields.Datetime(string='Last Activity', default=fields.Datetime.now)
    
    # Связи
    partner_id = fields.Many2one('res.partner', string='Odoo Partner')
    
    # Вычисляемые поля
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    
    @api.depends('display_name')
    def _compute_name(self):
        for record in self:
            record.name = record.display_name or f"User {record.telegram_id}"
    
    @api.constrains('telegram_id')
    def _check_telegram_id_unique(self):
        for record in self:
            if self.search_count([('telegram_id', '=', record.telegram_id), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Telegram ID must be unique'))
    
    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError(_('Invalid email format'))
    
    def update_activity(self):
        """Обновить время последней активности"""
        self.last_activity = fields.Datetime.now()
    
    def add_points(self, points, reason=''):
        """Добавить баллы пользователю"""
        self.total_points += points
        self.available_points += points
        self.update_activity()
        
        # Логирование
        _logger.info(f"Added {points} points to user {self.telegram_id}. Reason: {reason}")
    
    def spend_points(self, points, reason=''):
        """Потратить баллы пользователя"""
        if self.available_points < points:
            raise ValidationError(_('Not enough points available'))
        
        self.available_points -= points
        self.update_activity()
        
        # Логирование
        _logger.info(f"Spent {points} points from user {self.telegram_id}. Reason: {reason}")
    
    def get_level_info(self):
        """Получить информацию об уровне пользователя"""
        # Простая система уровней
        if self.total_points < 100:
            return {'level': 1, 'name': 'Newcomer', 'points_to_next': 100 - self.total_points}
        elif self.total_points < 300:
            return {'level': 2, 'name': 'Bronze', 'points_to_next': 300 - self.total_points}
        elif self.total_points < 600:
            return {'level': 3, 'name': 'Silver', 'points_to_next': 600 - self.total_points}
        elif self.total_points < 1000:
            return {'level': 4, 'name': 'Gold', 'points_to_next': 1000 - self.total_points}
        elif self.total_points < 1500:
            return {'level': 5, 'name': 'Platinum', 'points_to_next': 1500 - self.total_points}
        else:
            return {'level': 6, 'name': 'Diamond', 'points_to_next': 0}


class KarmaBotLoyaltyProgram(models.Model):
    _name = 'karmabot.loyalty.program'
    _description = 'KarmaBot Loyalty Program'
    
    name = fields.Char(string='Program Name', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    
    def calculate_user_level(self, points):
        """Вычислить уровень пользователя на основе баллов"""
        if points < 100:
            return {'level': 1, 'name': 'Newcomer', 'points_to_next': 100 - points}
        elif points < 300:
            return {'level': 2, 'name': 'Bronze', 'points_to_next': 300 - points}
        elif points < 600:
            return {'level': 3, 'name': 'Silver', 'points_to_next': 600 - points}
        elif points < 1000:
            return {'level': 4, 'name': 'Gold', 'points_to_next': 1000 - points}
        elif points < 1500:
            return {'level': 5, 'name': 'Platinum', 'points_to_next': 1500 - points}
        else:
            return {'level': 6, 'name': 'Diamond', 'points_to_next': 0}


class KarmaBotPartnerCard(models.Model):
    _name = 'karmabot.partner.card'
    _description = 'KarmaBot Partner Card'
    
    name = fields.Char(string='Card Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    card_number = fields.Char(string='Card Number', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending')
    
    # QR код и ссылка
    qr_code = fields.Char(string='QR Code')
    webapp_url = fields.Char(string='WebApp URL')
    
    # Даты
    create_date = fields.Datetime(string='Created', default=fields.Datetime.now)
    activation_date = fields.Datetime(string='Activated')
    
    def activate_card(self):
        """Активировать карту"""
        self.status = 'active'
        self.activation_date = fields.Datetime.now()


class KarmaBotLoyaltyTransaction(models.Model):
    _name = 'karmabot.loyalty.transaction'
    _description = 'KarmaBot Loyalty Transaction'
    
    user_id = fields.Many2one('karmabot.user', string='User', required=True)
    transaction_type = fields.Selection([
        ('earn', 'Earn Points'),
        ('spend', 'Spend Points'),
        ('bonus', 'Bonus Points'),
        ('penalty', 'Penalty Points')
    ], string='Transaction Type', required=True)
    
    points = fields.Integer(string='Points', required=True)
    reason = fields.Char(string='Reason')
    description = fields.Text(string='Description')
    
    # Связи
    partner_id = fields.Many2one('res.partner', string='Partner')
    card_id = fields.Many2one('karmabot.partner.card', string='Card')
    
    # Даты
    transaction_date = fields.Datetime(string='Transaction Date', default=fields.Datetime.now)
    
    # Статус
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='completed')


class KarmaBotWebAppSession(models.Model):
    _name = 'karmabot.webapp_session'
    _description = 'KarmaBot WebApp Session'
    
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
    
    @api.model
    def create_session(self, user_id, session_type, ip_address=None, user_agent=None):
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
            'is_active': True
        })
        
        return session
    
    def update_activity(self):
        """Обновить активность сессии"""
        self.last_activity = fields.Datetime.now()
    
    def end_session(self):
        """Завершить сессию"""
        self.is_active = False
        self.end_time = fields.Datetime.now()
