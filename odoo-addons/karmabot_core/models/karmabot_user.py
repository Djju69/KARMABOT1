# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class KarmaBotUser(models.Model):
    """KarmaBot User Model - Core user management with Telegram integration"""
    
    _name = 'karmabot.user'
    _description = 'KarmaBot User'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # Basic Information
    name = fields.Char(
        string='Display Name',
        required=True,
        tracking=True,
        help="User's display name in the system"
    )
    
    telegram_id = fields.Char(
        string='Telegram ID',
        required=True,
        index=True,
        unique=True,
        tracking=True,
        help="Unique Telegram user ID"
    )
    
    telegram_username = fields.Char(
        string='Telegram Username',
        tracking=True,
        help="Telegram username (@username)"
    )
    
    telegram_first_name = fields.Char(
        string='First Name',
        tracking=True,
        help="User's first name from Telegram"
    )
    
    telegram_last_name = fields.Char(
        string='Last Name',
        tracking=True,
        help="User's last name from Telegram"
    )
    
    # User Status and Role
    role = fields.Selection([
        ('user', 'User'),
        ('partner', 'Partner'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    ], string='Role', default='user', required=True, tracking=True)
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Whether the user is active in the system"
    )
    
    is_verified = fields.Boolean(
        string='Verified',
        default=False,
        tracking=True,
        help="Whether the user is verified"
    )
    
    # Points and Loyalty
    total_points = fields.Integer(
        string='Total Points',
        default=0,
        tracking=True,
        help="Total points earned by the user"
    )
    
    available_points = fields.Integer(
        string='Available Points',
        default=0,
        tracking=True,
        help="Points available for spending"
    )
    
    pending_points = fields.Integer(
        string='Pending Points',
        default=0,
        tracking=True,
        help="Points pending approval"
    )
    
    spent_points = fields.Integer(
        string='Spent Points',
        default=0,
        tracking=True,
        help="Total points spent by the user"
    )
    
    # Activity Tracking
    registration_date = fields.Datetime(
        string='Registration Date',
        default=fields.Datetime.now,
        tracking=True,
        help="When the user registered"
    )
    
    last_activity = fields.Datetime(
        string='Last Activity',
        tracking=True,
        help="Last time user was active"
    )
    
    total_scans = fields.Integer(
        string='Total QR Scans',
        default=0,
        tracking=True,
        help="Total number of QR codes scanned"
    )
    
    total_referrals = fields.Integer(
        string='Total Referrals',
        default=0,
        tracking=True,
        help="Number of users referred by this user"
    )
    
    # Linked Cards
    linked_cards = fields.One2many(
        'karmabot.user.card',
        'user_id',
        string='Linked Cards',
        help="Cards linked to this user"
    )
    
    linked_cards_count = fields.Integer(
        string='Linked Cards Count',
        compute='_compute_linked_cards_count',
        help="Number of cards linked to this user"
    )
    
    # Transactions
    transactions = fields.One2many(
        'karmabot.loyalty.transaction',
        'user_id',
        string='Transactions',
        help="Loyalty transactions for this user"
    )
    
    transactions_count = fields.Integer(
        string='Transactions Count',
        compute='_compute_transactions_count',
        help="Number of transactions for this user"
    )
    
    # Referral System
    referral_code = fields.Char(
        string='Referral Code',
        compute='_compute_referral_code',
        store=True,
        help="Unique referral code for this user"
    )
    
    referred_by = fields.Many2one(
        'karmabot.user',
        string='Referred By',
        help="User who referred this user"
    )
    
    referrals = fields.One2many(
        'karmabot.user',
        'referred_by',
        string='Referrals',
        help="Users referred by this user"
    )
    
    # Preferences
    language = fields.Selection([
        ('ru', 'Russian'),
        ('en', 'English'),
        ('vi', 'Vietnamese'),
        ('ko', 'Korean'),
    ], string='Language', default='ru', tracking=True)
    
    notifications_enabled = fields.Boolean(
        string='Notifications Enabled',
        default=True,
        tracking=True,
        help="Whether user wants to receive notifications"
    )
    
    # Computed Fields
    @api.depends('linked_cards')
    def _compute_linked_cards_count(self):
        for record in self:
            record.linked_cards_count = len(record.linked_cards)
    
    @api.depends('transactions')
    def _compute_transactions_count(self):
        for record in self:
            record.transactions_count = len(record.transactions)
    
    @api.depends('telegram_id')
    def _compute_referral_code(self):
        for record in self:
            if record.telegram_id:
                # Generate referral code from telegram_id
                import hashlib
                hash_obj = hashlib.md5(record.telegram_id.encode())
                record.referral_code = f"REF{hash_obj.hexdigest()[:8].upper()}"
            else:
                record.referral_code = False
    
    # Constraints
    @api.constrains('telegram_id')
    def _check_telegram_id(self):
        for record in self:
            if record.telegram_id and not record.telegram_id.isdigit():
                raise ValidationError(_("Telegram ID must be numeric"))
    
    @api.constrains('available_points', 'total_points', 'spent_points')
    def _check_points_consistency(self):
        for record in self:
            if record.available_points < 0:
                raise ValidationError(_("Available points cannot be negative"))
            if record.spent_points < 0:
                raise ValidationError(_("Spent points cannot be negative"))
            if record.total_points < record.spent_points:
                raise ValidationError(_("Total points cannot be less than spent points"))
    
    # Methods
    def action_add_points(self, points, reason='Manual adjustment'):
        """Add points to user account"""
        self.ensure_one()
        if points <= 0:
            raise UserError(_("Points must be positive"))
        
        self.write({
            'total_points': self.total_points + points,
            'available_points': self.available_points + points,
        })
        
        # Create transaction record
        self.env['karmabot.loyalty.transaction'].create({
            'user_id': self.id,
            'points': points,
            'transaction_type': 'manual_adjustment',
            'description': reason,
        })
        
        _logger.info(f"Added {points} points to user {self.name} ({self.telegram_id})")
    
    def action_spend_points(self, points, reason='Points spent'):
        """Spend points from user account"""
        self.ensure_one()
        if points <= 0:
            raise UserError(_("Points must be positive"))
        if self.available_points < points:
            raise UserError(_("Insufficient points"))
        
        self.write({
            'available_points': self.available_points - points,
            'spent_points': self.spent_points + points,
        })
        
        # Create transaction record
        self.env['karmabot.loyalty.transaction'].create({
            'user_id': self.id,
            'points': -points,
            'transaction_type': 'spend',
            'description': reason,
        })
        
        _logger.info(f"Spent {points} points from user {self.name} ({self.telegram_id})")
    
    def action_update_activity(self):
        """Update user's last activity timestamp"""
        self.ensure_one()
        self.write({
            'last_activity': fields.Datetime.now()
        })
    
    def action_verify_user(self):
        """Verify user account"""
        self.ensure_one()
        self.write({
            'is_verified': True
        })
        _logger.info(f"Verified user {self.name} ({self.telegram_id})")
    
    def action_deactivate_user(self):
        """Deactivate user account"""
        self.ensure_one()
        self.write({
            'is_active': False
        })
        _logger.info(f"Deactivated user {self.name} ({self.telegram_id})")
    
    def action_activate_user(self):
        """Activate user account"""
        self.ensure_one()
        self.write({
            'is_active': True
        })
        _logger.info(f"Activated user {self.name} ({self.telegram_id})")
    
    @api.model
    def create_from_telegram(self, telegram_data):
        """Create user from Telegram data"""
        telegram_id = str(telegram_data.get('id'))
        
        # Check if user already exists
        existing_user = self.search([('telegram_id', '=', telegram_id)], limit=1)
        if existing_user:
            # Update existing user
            existing_user.write({
                'telegram_username': telegram_data.get('username'),
                'telegram_first_name': telegram_data.get('first_name'),
                'telegram_last_name': telegram_data.get('last_name'),
                'last_activity': fields.Datetime.now(),
            })
            return existing_user
        
        # Create new user
        user_data = {
            'telegram_id': telegram_id,
            'telegram_username': telegram_data.get('username'),
            'telegram_first_name': telegram_data.get('first_name'),
            'telegram_last_name': telegram_data.get('last_name'),
            'name': telegram_data.get('first_name', '') + ' ' + (telegram_data.get('last_name') or ''),
            'role': 'user',
            'is_active': True,
            'is_verified': False,
            'registration_date': fields.Datetime.now(),
            'last_activity': fields.Datetime.now(),
        }
        
        return self.create(user_data)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} (@{record.telegram_username})" if record.telegram_username else record.name
            result.append((record.id, name))
        return result


class KarmaBotUserCard(models.Model):
    """User's linked cards"""
    
    _name = 'karmabot.user.card'
    _description = 'User Linked Card'
    _order = 'create_date desc'
    
    user_id = fields.Many2one(
        'karmabot.user',
        string='User',
        required=True,
        ondelete='cascade'
    )
    
    card_number = fields.Char(
        string='Card Number',
        required=True,
        help="Physical or virtual card number"
    )
    
    card_type = fields.Selection([
        ('physical', 'Physical Card'),
        ('virtual', 'Virtual Card'),
        ('qr', 'QR Code'),
    ], string='Card Type', default='physical', required=True)
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the card is active"
    )
    
    linked_date = fields.Datetime(
        string='Linked Date',
        default=fields.Datetime.now,
        help="When the card was linked"
    )
    
    last_used = fields.Datetime(
        string='Last Used',
        help="When the card was last used"
    )
    
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        help="Number of times the card was used"
    )
    
    @api.constrains('card_number')
    def _check_card_number(self):
        for record in self:
            if not record.card_number:
                raise ValidationError(_("Card number is required"))
    
    def action_use_card(self):
        """Mark card as used"""
        self.ensure_one()
        self.write({
            'last_used': fields.Datetime.now(),
            'usage_count': self.usage_count + 1,
        })
