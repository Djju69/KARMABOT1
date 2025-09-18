# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KarmaBotLoyaltyProgram(models.Model):
    """KarmaBot Loyalty Program Model - Configuration for loyalty system"""
    
    _name = 'karmabot.loyalty.program'
    _description = 'KarmaBot Loyalty Program'
    
    name = fields.Char(
        string='Program Name',
        required=True,
        help="Name of the loyalty program"
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the program is active"
    )
    
    # Points Configuration
    points_per_scan = fields.Integer(
        string='Points per QR Scan',
        default=10,
        help="Points awarded for each QR code scan"
    )
    
    referral_bonus = fields.Integer(
        string='Referral Bonus',
        default=50,
        help="Points awarded for successful referral"
    )
    
    welcome_bonus = fields.Integer(
        string='Welcome Bonus',
        default=25,
        help="Points awarded for new user registration"
    )
    
    daily_login_bonus = fields.Integer(
        string='Daily Login Bonus',
        default=5,
        help="Points awarded for daily login"
    )
    
    # Limits and Restrictions
    max_points_per_day = fields.Integer(
        string='Max Points per Day',
        default=100,
        help="Maximum points a user can earn per day"
    )
    
    max_scans_per_place = fields.Integer(
        string='Max Scans per Place per Day',
        default=3,
        help="Maximum scans per place per day"
    )
    
    min_redeem_points = fields.Integer(
        string='Minimum Redeem Points',
        default=100,
        help="Minimum points required for redemption"
    )
    
    points_expiry_days = fields.Integer(
        string='Points Expiry Days',
        default=365,
        help="Days after which points expire"
    )
    
    # Redemption Configuration
    redemption_rate = fields.Float(
        string='Redemption Rate',
        default=0.01,
        help="Points to currency conversion rate (1 point = 0.01 currency)"
    )
    
    max_redemption_per_day = fields.Integer(
        string='Max Redemption per Day',
        default=1000,
        help="Maximum points that can be redeemed per day"
    )
    
    # Anti-Fraud Settings
    fraud_check_enabled = fields.Boolean(
        string='Enable Fraud Check',
        default=True,
        help="Enable fraud detection for transactions"
    )
    
    fraud_score_threshold = fields.Float(
        string='Fraud Score Threshold',
        default=0.7,
        help="Threshold for fraud detection (0-1)"
    )
    
    geolocation_check = fields.Boolean(
        string='Enable Geolocation Check',
        default=True,
        help="Check user location against card location"
    )
    
    max_distance_km = fields.Float(
        string='Max Distance (km)',
        default=1.0,
        help="Maximum distance for valid scan (in kilometers)"
    )
    
    # Level System
    level_system_enabled = fields.Boolean(
        string='Enable Level System',
        default=True,
        help="Enable user level system"
    )
    
    level_thresholds = fields.Text(
        string='Level Thresholds',
        default='[100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]',
        help="JSON array of points required for each level"
    )
    
    level_names = fields.Text(
        string='Level Names',
        default='["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Legend", "Mythic"]',
        help="JSON array of level names"
    )
    
    # Methods
    def get_level_thresholds(self):
        """Get level thresholds as list"""
        import json
        try:
            return json.loads(self.level_thresholds)
        except (json.JSONDecodeError, TypeError):
            return [100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]
    
    def get_level_names(self):
        """Get level names as list"""
        import json
        try:
            return json.loads(self.level_names)
        except (json.JSONDecodeError, TypeError):
            return ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Legend", "Mythic"]
    
    def calculate_user_level(self, total_points):
        """Calculate user level based on total points"""
        thresholds = self.get_level_thresholds()
        names = self.get_level_names()
        
        level = 0
        for i, threshold in enumerate(thresholds):
            if total_points >= threshold:
                level = i + 1
            else:
                break
        
        return {
            'level': level,
            'name': names[level - 1] if level > 0 else 'Newcomer',
            'next_level_points': thresholds[level] if level < len(thresholds) else None,
            'points_to_next': thresholds[level] - total_points if level < len(thresholds) else 0,
        }
    
    def validate_transaction(self, user_id, points, transaction_type='qr_scan'):
        """Validate if transaction is allowed"""
        user = self.env['karmabot.user'].browse(user_id)
        
        # Check daily limits
        if transaction_type == 'qr_scan':
            today_points = self._get_today_points(user_id)
            if today_points + points > self.max_points_per_day:
                return False, _("Daily points limit exceeded")
        
        # Check fraud if enabled
        if self.fraud_check_enabled:
            fraud_score = self._calculate_fraud_score(user_id, points, transaction_type)
            if fraud_score > self.fraud_score_threshold:
                return False, _("Transaction flagged as potentially fraudulent")
        
        return True, "Valid"
    
    def _get_today_points(self, user_id):
        """Get points earned today by user"""
        today = fields.Date.today()
        transactions = self.env['karmabot.loyalty.transaction'].search([
            ('user_id', '=', user_id),
            ('transaction_type', '=', 'qr_scan'),
            ('create_date', '>=', today),
            ('points', '>', 0),
        ])
        return sum(transactions.mapped('points'))
    
    def _calculate_fraud_score(self, user_id, points, transaction_type):
        """Calculate fraud score for transaction"""
        # Simple fraud detection logic
        # In real implementation, this would be more sophisticated
        
        user = self.env['karmabot.user'].browse(user_id)
        
        # Check if user is new (higher risk)
        if user.total_scans < 5:
            return 0.3
        
        # Check if points amount is suspicious
        if points > self.points_per_scan * 2:
            return 0.5
        
        # Check if user has many failed transactions
        failed_transactions = self.env['karmabot.loyalty.transaction'].search([
            ('user_id', '=', user_id),
            ('fraud_check_passed', '=', False),
        ])
        
        if len(failed_transactions) > 3:
            return 0.8
        
        return 0.1  # Low risk
    
    @api.constrains('points_per_scan', 'referral_bonus', 'welcome_bonus')
    def _check_positive_values(self):
        for record in self:
            if record.points_per_scan < 0:
                raise ValidationError(_("Points per scan must be positive"))
            if record.referral_bonus < 0:
                raise ValidationError(_("Referral bonus must be positive"))
            if record.welcome_bonus < 0:
                raise ValidationError(_("Welcome bonus must be positive"))
    
    @api.constrains('max_points_per_day', 'min_redeem_points')
    def _check_limits(self):
        for record in self:
            if record.max_points_per_day <= 0:
                raise ValidationError(_("Max points per day must be positive"))
            if record.min_redeem_points <= 0:
                raise ValidationError(_("Minimum redeem points must be positive"))
