# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import json
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class KarmaBotLoyaltyProgram(models.Model):
    """Extended KarmaBot Loyalty Program Model"""
    
    _name = 'karmabot.loyalty.program'
    _inherit = 'karmabot.loyalty.program'
    _description = 'Extended KarmaBot Loyalty Program'
    
    # Additional Fields
    program_code = fields.Char(
        string='Program Code',
        required=True,
        default='DEFAULT',
        help="Unique program code"
    )
    
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        help="Program start date"
    )
    
    end_date = fields.Date(
        string='End Date',
        help="Program end date (optional)"
    )
    
    # Advanced Settings
    enable_achievements = fields.Boolean(
        string='Enable Achievements',
        default=True,
        help="Enable achievement system"
    )
    
    enable_levels = fields.Boolean(
        string='Enable Level System',
        default=True,
        help="Enable user level progression"
    )
    
    enable_referrals = fields.Boolean(
        string='Enable Referrals',
        default=True,
        help="Enable referral system"
    )
    
    enable_daily_bonus = fields.Boolean(
        string='Enable Daily Bonus',
        default=True,
        help="Enable daily login bonus"
    )
    
    # Level System Configuration
    level_multiplier = fields.Float(
        string='Level Multiplier',
        default=1.0,
        help="Points multiplier based on user level"
    )
    
    max_level_multiplier = fields.Float(
        string='Max Level Multiplier',
        default=2.0,
        help="Maximum points multiplier"
    )
    
    # Referral System
    referral_expiry_days = fields.Integer(
        string='Referral Expiry Days',
        default=30,
        help="Days after which referral bonus expires"
    )
    
    max_referrals_per_user = fields.Integer(
        string='Max Referrals per User',
        default=10,
        help="Maximum referrals per user"
    )
    
    # Anti-Fraud Advanced Settings
    enable_ip_check = fields.Boolean(
        string='Enable IP Check',
        default=False,
        help="Check for duplicate IP addresses"
    )
    
    enable_device_fingerprint = fields.Boolean(
        string='Enable Device Fingerprint',
        default=False,
        help="Check for duplicate device fingerprints"
    )
    
    fraud_cooldown_minutes = fields.Integer(
        string='Fraud Cooldown (minutes)',
        default=60,
        help="Cooldown period after fraud detection"
    )
    
    # Analytics
    total_users = fields.Integer(
        string='Total Users',
        compute='_compute_total_users',
        help="Total users in the program"
    )
    
    active_users = fields.Integer(
        string='Active Users',
        compute='_compute_active_users',
        help="Active users (last 30 days)"
    )
    
    total_points_earned = fields.Integer(
        string='Total Points Earned',
        compute='_compute_total_points',
        help="Total points earned in the program"
    )
    
    total_points_spent = fields.Integer(
        string='Total Points Spent',
        compute='_compute_total_points',
        help="Total points spent in the program"
    )
    
    @api.depends('start_date', 'end_date')
    def _compute_total_users(self):
        for record in self:
            domain = [('registration_date', '>=', record.start_date)]
            if record.end_date:
                domain.append(('registration_date', '<=', record.end_date))
            
            record.total_users = self.env['karmabot.user'].search_count(domain)
    
    @api.depends('start_date', 'end_date')
    def _compute_active_users(self):
        for record in self:
            thirty_days_ago = fields.Date.today() - timedelta(days=30)
            domain = [
                ('last_activity', '>=', thirty_days_ago),
                ('registration_date', '>=', record.start_date)
            ]
            if record.end_date:
                domain.append(('registration_date', '<=', record.end_date))
            
            record.active_users = self.env['karmabot.user'].search_count(domain)
    
    @api.depends('start_date', 'end_date')
    def _compute_total_points(self):
        for record in self:
            domain = [('create_date', '>=', record.start_date)]
            if record.end_date:
                domain.append(('create_date', '<=', record.end_date))
            
            transactions = self.env['karmabot.loyalty.transaction'].search(domain)
            
            earned_points = sum(transactions.filtered(lambda t: t.points > 0).mapped('points'))
            spent_points = abs(sum(transactions.filtered(lambda t: t.points < 0).mapped('points')))
            
            record.total_points_earned = earned_points
            record.total_points_spent = spent_points
    
    # Methods
    def calculate_user_level(self, total_points):
        """Enhanced level calculation with multipliers"""
        thresholds = self.get_level_thresholds()
        names = self.get_level_names()
        
        level = 0
        for i, threshold in enumerate(thresholds):
            if total_points >= threshold:
                level = i + 1
            else:
                break
        
        # Calculate multiplier
        multiplier = min(
            self.level_multiplier + (level - 1) * 0.1,
            self.max_level_multiplier
        )
        
        return {
            'level': level,
            'name': names[level - 1] if level > 0 else 'Newcomer',
            'next_level_points': thresholds[level] if level < len(thresholds) else None,
            'points_to_next': thresholds[level] - total_points if level < len(thresholds) else 0,
            'multiplier': multiplier,
        }
    
    def validate_transaction(self, user_id, points, transaction_type='qr_scan', **kwargs):
        """Enhanced transaction validation with advanced fraud detection"""
        user = self.env['karmabot.user'].browse(user_id)
        
        # Basic validation
        valid, message = super().validate_transaction(user_id, points, transaction_type)
        if not valid:
            return False, message
        
        # Advanced fraud checks
        if self.fraud_check_enabled:
            fraud_score = self._calculate_advanced_fraud_score(user_id, points, transaction_type, **kwargs)
            if fraud_score > self.fraud_score_threshold:
                return False, _("Transaction flagged as potentially fraudulent")
        
        # IP check
        if self.enable_ip_check:
            if self._check_duplicate_ip(user_id, kwargs.get('ip_address')):
                return False, _("Duplicate IP address detected")
        
        # Device fingerprint check
        if self.enable_device_fingerprint:
            if self._check_duplicate_device(user_id, kwargs.get('device_fingerprint')):
                return False, _("Duplicate device fingerprint detected")
        
        return True, "Valid"
    
    def _calculate_advanced_fraud_score(self, user_id, points, transaction_type, **kwargs):
        """Advanced fraud detection algorithm"""
        user = self.env['karmabot.user'].browse(user_id)
        fraud_score = 0.0
        
        # Check transaction frequency
        recent_transactions = self.env['karmabot.loyalty.transaction'].search([
            ('user_id', '=', user_id),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
        ])
        
        if len(recent_transactions) > 10:
            fraud_score += 0.3
        
        # Check points amount
        if points > self.points_per_scan * 5:
            fraud_score += 0.2
        
        # Check location consistency
        if kwargs.get('latitude') and kwargs.get('longitude'):
            if not self._check_location_consistency(user_id, kwargs['latitude'], kwargs['longitude']):
                fraud_score += 0.4
        
        # Check time patterns
        if self._check_suspicious_time_pattern(user_id):
            fraud_score += 0.2
        
        # Check user behavior
        if user.total_scans < 5 and points > self.points_per_scan * 2:
            fraud_score += 0.3
        
        return min(fraud_score, 1.0)
    
    def _check_duplicate_ip(self, user_id, ip_address):
        """Check for duplicate IP addresses"""
        if not ip_address:
            return False
        
        # Check if same IP used by different users recently
        recent_transactions = self.env['karmabot.loyalty.transaction'].search([
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
        ])
        
        # This would require storing IP addresses in transactions
        # For now, return False
        return False
    
    def _check_duplicate_device(self, user_id, device_fingerprint):
        """Check for duplicate device fingerprints"""
        if not device_fingerprint:
            return False
        
        # Similar to IP check, would require storing device fingerprints
        return False
    
    def _check_location_consistency(self, user_id, latitude, longitude):
        """Check if location is consistent with user's usual locations"""
        # Get user's recent transaction locations
        recent_transactions = self.env['karmabot.loyalty.transaction'].search([
            ('user_id', '=', user_id),
            ('latitude', '!=', False),
            ('longitude', '!=', False),
            ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], limit=10)
        
        if not recent_transactions:
            return True  # No location history, allow
        
        # Check if new location is within reasonable distance
        for transaction in recent_transactions:
            distance = self._calculate_distance(
                latitude, longitude,
                transaction.latitude, transaction.longitude
            )
            
            if distance > self.max_distance_km * 10:  # 10x normal distance
                return False
        
        return True
    
    def _check_suspicious_time_pattern(self, user_id):
        """Check for suspicious time patterns"""
        # Check if user is scanning at unusual hours
        current_hour = fields.Datetime.now().hour
        
        # Unusual hours: 2 AM - 6 AM
        if 2 <= current_hour <= 6:
            return True
        
        return False
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers"""
        import math
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def get_program_statistics(self):
        """Get comprehensive program statistics"""
        self.ensure_one()
        
        stats = {
            'total_users': self.total_users,
            'active_users': self.active_users,
            'total_points_earned': self.total_points_earned,
            'total_points_spent': self.total_points_spent,
            'points_circulation': self.total_points_earned - self.total_points_spent,
            'average_points_per_user': self.total_points_earned / self.total_users if self.total_users > 0 else 0,
            'redemption_rate': self.total_points_spent / self.total_points_earned if self.total_points_earned > 0 else 0,
        }
        
        # Get monthly trends
        monthly_stats = self._get_monthly_statistics()
        stats['monthly_trends'] = monthly_stats
        
        return stats
    
    def _get_monthly_statistics(self):
        """Get monthly statistics for the program"""
        monthly_stats = []
        
        for i in range(12):  # Last 12 months
            month_start = fields.Date.today() - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            # Get transactions for this month
            transactions = self.env['karmabot.loyalty.transaction'].search([
                ('create_date', '>=', month_start),
                ('create_date', '<=', month_end)
            ])
            
            earned_points = sum(transactions.filtered(lambda t: t.points > 0).mapped('points'))
            spent_points = abs(sum(transactions.filtered(lambda t: t.points < 0).mapped('points')))
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'earned_points': earned_points,
                'spent_points': spent_points,
                'transaction_count': len(transactions),
            })
        
        return monthly_stats
    
    def action_export_statistics(self):
        """Export program statistics to CSV"""
        self.ensure_one()
        
        stats = self.get_program_statistics()
        
        # Create CSV content
        csv_content = "Metric,Value\n"
        csv_content += f"Total Users,{stats['total_users']}\n"
        csv_content += f"Active Users,{stats['active_users']}\n"
        csv_content += f"Total Points Earned,{stats['total_points_earned']}\n"
        csv_content += f"Total Points Spent,{stats['total_points_spent']}\n"
        csv_content += f"Points Circulation,{stats['points_circulation']}\n"
        csv_content += f"Average Points per User,{stats['average_points_per_user']:.2f}\n"
        csv_content += f"Redemption Rate,{stats['redemption_rate']:.2%}\n"
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=karmabot.loyalty.program&id={self.id}&field=csv_export&filename_field=name&download=true',
            'target': 'new',
        }
