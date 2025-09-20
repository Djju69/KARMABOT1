# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class KarmaBotLoyaltyTransaction(models.Model):
    """Extended KarmaBot Loyalty Transaction Model"""
    
    _name = 'karmabot.loyalty.transaction'
    _inherit = 'karmabot.loyalty.transaction'
    _description = 'Extended KarmaBot Loyalty Transaction'
    
    # Additional Fields
    achievement_id = fields.Many2one(
        'karmabot.achievement',
        string='Achievement',
        help="Achievement that generated this transaction"
    )
    
    referral_user_id = fields.Many2one(
        'karmabot.user',
        string='Referred User',
        help="User who was referred (for referral transactions)"
    )
    
    # Enhanced Fraud Detection
    ip_address = fields.Char(
        string='IP Address',
        help="IP address of the transaction"
    )
    
    device_fingerprint = fields.Char(
        string='Device Fingerprint',
        help="Device fingerprint for fraud detection"
    )
    
    user_agent = fields.Char(
        string='User Agent',
        help="User agent string"
    )
    
    # Transaction Metadata
    source = fields.Selection([
        ('telegram_bot', 'Telegram Bot'),
        ('webapp', 'Web Application'),
        ('mobile_app', 'Mobile App'),
        ('api', 'API'),
        ('admin', 'Admin Panel'),
    ], string='Source', default='telegram_bot', help="Source of the transaction")
    
    session_id = fields.Char(
        string='Session ID',
        help="Session identifier"
    )
    
    # Enhanced Analytics
    points_before = fields.Integer(
        string='Points Before',
        help="User's points before this transaction"
    )
    
    points_after = fields.Integer(
        string='Points After',
        help="User's points after this transaction"
    )
    
    level_before = fields.Integer(
        string='Level Before',
        help="User's level before this transaction"
    )
    
    level_after = fields.Integer(
        string='Level After',
        help="User's level after this transaction"
    )
    
    # Computed Fields
    is_level_up = fields.Boolean(
        string='Level Up',
        compute='_compute_is_level_up',
        help="Whether this transaction caused a level up"
    )
    
    @api.depends('level_before', 'level_after')
    def _compute_is_level_up(self):
        for record in self:
            record.is_level_up = record.level_after > record.level_before
    
    # Enhanced Methods
    @api.model
    def create_qr_reward(self, user_id, partner_card_id, points, qr_code_id=None, location_data=None, **kwargs):
        """Enhanced QR scan reward creation"""
        user = self.env['karmabot.user'].browse(user_id)
        
        # Get current user state
        points_before = user.available_points
        level_before = self._get_user_level(user_id)
        
        # Create transaction
        transaction_data = {
            'user_id': user_id,
            'partner_card_id': partner_card_id,
            'points': points,
            'transaction_type': 'qr_scan',
            'description': f'QR scan reward: {points} points',
            'qr_code_id': qr_code_id,
            'status': 'approved',
            'points_before': points_before,
            'level_before': level_before,
        }
        
        # Add location data
        if location_data:
            transaction_data.update({
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'location_accuracy': location_data.get('accuracy'),
            })
        
        # Add additional metadata
        transaction_data.update({
            'ip_address': kwargs.get('ip_address'),
            'device_fingerprint': kwargs.get('device_fingerprint'),
            'user_agent': kwargs.get('user_agent'),
            'source': kwargs.get('source', 'telegram_bot'),
            'session_id': kwargs.get('session_id'),
        })
        
        transaction = self.create(transaction_data)
        
        # Update user points and level
        user.write({
            'total_points': user.total_points + points,
            'available_points': user.available_points + points,
        })
        
        # Update transaction with final state
        level_after = self._get_user_level(user_id)
        transaction.write({
            'points_after': user.available_points,
            'level_after': level_after,
        })
        
        # Check for achievements
        if user.available_points > points_before:
            self.env['karmabot.achievement'].check_all_achievements_for_user(user_id)
        
        return transaction
    
    @api.model
    def create_referral_bonus(self, user_id, referred_user_id, points, **kwargs):
        """Enhanced referral bonus creation"""
        user = self.env['karmabot.user'].browse(user_id)
        referred_user = self.env['karmabot.user'].browse(referred_user_id)
        
        # Get current user state
        points_before = user.available_points
        level_before = self._get_user_level(user_id)
        
        # Create transaction
        transaction_data = {
            'user_id': user_id,
            'referral_user_id': referred_user_id,
            'points': points,
            'transaction_type': 'referral',
            'description': f'Referral bonus for {referred_user.name}: {points} points',
            'status': 'approved',
            'points_before': points_before,
            'level_before': level_before,
        }
        
        # Add metadata
        transaction_data.update({
            'ip_address': kwargs.get('ip_address'),
            'device_fingerprint': kwargs.get('device_fingerprint'),
            'user_agent': kwargs.get('user_agent'),
            'source': kwargs.get('source', 'telegram_bot'),
            'session_id': kwargs.get('session_id'),
        })
        
        transaction = self.create(transaction_data)
        
        # Update user points
        user.write({
            'total_points': user.total_points + points,
            'available_points': user.available_points + points,
        })
        
        # Update transaction with final state
        level_after = self._get_user_level(user_id)
        transaction.write({
            'points_after': user.available_points,
            'level_after': level_after,
        })
        
        return transaction
    
    @api.model
    def create_achievement_reward(self, user_id, achievement_id, points, **kwargs):
        """Create achievement reward transaction"""
        achievement = self.env['karmabot.achievement'].browse(achievement_id)
        user = self.env['karmabot.user'].browse(user_id)
        
        # Get current user state
        points_before = user.available_points
        level_before = self._get_user_level(user_id)
        
        # Create transaction
        transaction_data = {
            'user_id': user_id,
            'achievement_id': achievement_id,
            'points': points,
            'transaction_type': 'achievement_reward',
            'description': f'Achievement reward: {achievement.name}',
            'status': 'approved',
            'points_before': points_before,
            'level_before': level_before,
        }
        
        # Add metadata
        transaction_data.update({
            'ip_address': kwargs.get('ip_address'),
            'device_fingerprint': kwargs.get('device_fingerprint'),
            'user_agent': kwargs.get('user_agent'),
            'source': kwargs.get('source', 'telegram_bot'),
            'session_id': kwargs.get('session_id'),
        })
        
        transaction = self.create(transaction_data)
        
        # Update user points
        user.write({
            'total_points': user.total_points + points,
            'available_points': user.available_points + points,
        })
        
        # Update transaction with final state
        level_after = self._get_user_level(user_id)
        transaction.write({
            'points_after': user.available_points,
            'level_after': level_after,
        })
        
        return transaction
    
    def _get_user_level(self, user_id):
        """Get user's current level"""
        user = self.env['karmabot.user'].browse(user_id)
        
        # Get loyalty program
        program = self.env['karmabot.loyalty.program'].search([
            ('is_active', '=', True)
        ], limit=1)
        
        if program:
            level_info = program.calculate_user_level(user.total_points)
            return level_info['level']
        else:
            return 0
    
    def action_approve(self):
        """Enhanced approval with level tracking"""
        self.ensure_one()
        
        if self.status != 'pending':
            raise ValidationError(_("Only pending transactions can be approved"))
        
        user = self.env['karmabot.user'].browse(self.user_id.id)
        
        # Get current state
        points_before = user.available_points
        level_before = self._get_user_level(self.user_id.id)
        
        # Update user points
        if self.is_earning:
            user.write({
                'total_points': user.total_points + self.points,
                'available_points': user.available_points + self.points,
            })
        elif self.is_spending:
            user.write({
                'available_points': user.available_points + self.points,  # points is negative
                'spent_points': user.spent_points - self.points,  # subtract negative
            })
        
        # Update transaction
        level_after = self._get_user_level(self.user_id.id)
        self.write({
            'status': 'approved',
            'points_before': points_before,
            'points_after': user.available_points,
            'level_before': level_before,
            'level_after': level_after,
        })
        
        # Check for achievements if points increased
        if self.is_earning and user.available_points > points_before:
            self.env['karmabot.achievement'].check_all_achievements_for_user(self.user_id.id)
        
        _logger.info(f"Approved transaction {self.id} for user {user.name}")
    
    def action_reject(self, reason=None):
        """Enhanced rejection with detailed logging"""
        self.ensure_one()
        
        if self.status != 'pending':
            raise ValidationError(_("Only pending transactions can be rejected"))
        
        if not reason:
            raise UserError(_("Rejection reason is required"))
        
        self.write({
            'status': 'rejected',
            'description': f"{self.description or ''}\nRejected: {reason}",
            'fraud_check_passed': False,
        })
        
        _logger.info(f"Rejected transaction {self.id} for user {self.user_id.name}: {reason}")
    
    @api.model
    def get_user_transaction_history(self, user_id, limit=50, offset=0):
        """Get user's transaction history with pagination"""
        transactions = self.search([
            ('user_id', '=', user_id)
        ], limit=limit, offset=offset, order='create_date desc')
        
        return transactions
    
    @api.model
    def get_user_statistics(self, user_id):
        """Get comprehensive user statistics"""
        user = self.env['karmabot.user'].browse(user_id)
        
        # Get all transactions
        transactions = self.search([('user_id', '=', user_id)])
        
        # Calculate statistics
        total_earned = sum(transactions.filtered(lambda t: t.points > 0).mapped('points'))
        total_spent = abs(sum(transactions.filtered(lambda t: t.points < 0).mapped('points')))
        
        # Get transaction counts by type
        transaction_counts = {}
        for transaction_type in ['qr_scan', 'referral', 'welcome', 'daily_login', 'spend', 'achievement_reward']:
            count = len(transactions.filtered(lambda t: t.transaction_type == transaction_type))
            transaction_counts[transaction_type] = count
        
        # Get monthly trends
        monthly_earned = {}
        monthly_spent = {}
        
        for i in range(12):  # Last 12 months
            month_start = fields.Date.today() - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_transactions = transactions.filtered(
                lambda t: month_start <= t.create_date.date() <= month_end
            )
            
            month_earned = sum(month_transactions.filtered(lambda t: t.points > 0).mapped('points'))
            month_spent = abs(sum(month_transactions.filtered(lambda t: t.points < 0).mapped('points')))
            
            month_key = month_start.strftime('%Y-%m')
            monthly_earned[month_key] = month_earned
            monthly_spent[month_key] = month_spent
        
        return {
            'total_earned': total_earned,
            'total_spent': total_spent,
            'net_points': total_earned - total_spent,
            'transaction_counts': transaction_counts,
            'monthly_earned': monthly_earned,
            'monthly_spent': monthly_spent,
            'total_transactions': len(transactions),
            'level_ups': len(transactions.filtered('is_level_up')),
        }
    
    @api.model
    def cleanup_expired_transactions(self):
        """Clean up expired transactions"""
        # Get transactions that are expired and can be cleaned up
        expired_date = fields.Datetime.now() - timedelta(days=365)  # 1 year
        
        expired_transactions = self.search([
            ('create_date', '<', expired_date),
            ('status', '=', 'rejected')
        ])
        
        # Archive instead of delete
        expired_transactions.write({
            'status': 'cancelled',
            'description': f"{expired_transactions.description or ''}\nArchived: {fields.Datetime.now()}"
        })
        
        _logger.info(f"Archived {len(expired_transactions)} expired transactions")
        return len(expired_transactions)
