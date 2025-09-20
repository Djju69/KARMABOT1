# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class KarmaBotAchievement(models.Model):
    """KarmaBot Achievement Model - User achievements and badges"""
    
    _name = 'karmabot.achievement'
    _description = 'KarmaBot Achievement'
    _order = 'sequence, name'
    
    # Basic Information
    name = fields.Char(
        string='Achievement Name',
        required=True,
        translate=True,
        help="Name of the achievement"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Description of the achievement"
    )
    
    icon = fields.Char(
        string='Icon',
        default='🏆',
        help="Icon or emoji for the achievement"
    )
    
    color = fields.Char(
        string='Color',
        default='#FFD700',
        help="Hex color code for the achievement"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order"
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the achievement is active"
    )
    
    # Achievement Criteria
    achievement_type = fields.Selection([
        ('points_total', 'Total Points'),
        ('points_single', 'Single Transaction Points'),
        ('scans_total', 'Total QR Scans'),
        ('scans_daily', 'Daily QR Scans'),
        ('referrals_total', 'Total Referrals'),
        ('cards_linked', 'Cards Linked'),
        ('consecutive_days', 'Consecutive Days'),
        ('category_explorer', 'Category Explorer'),
        ('early_adopter', 'Early Adopter'),
        ('social_butterfly', 'Social Butterfly'),
    ], string='Achievement Type', required=True)
    
    target_value = fields.Integer(
        string='Target Value',
        required=True,
        help="Target value to achieve this achievement"
    )
    
    target_period = fields.Selection([
        ('lifetime', 'Lifetime'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Target Period', default='lifetime', help="Period for target calculation")
    
    # Rewards
    points_reward = fields.Integer(
        string='Points Reward',
        default=0,
        help="Points awarded when achievement is unlocked"
    )
    
    badge_image = fields.Binary(
        string='Badge Image',
        help="Badge image for the achievement"
    )
    
    # Related Data
    user_achievements = fields.One2many(
        'karmabot.user.achievement',
        'achievement_id',
        string='User Achievements',
        help="Users who have earned this achievement"
    )
    
    earned_count = fields.Integer(
        string='Earned Count',
        compute='_compute_earned_count',
        help="Number of users who earned this achievement"
    )
    
    @api.depends('user_achievements')
    def _compute_earned_count(self):
        for record in self:
            record.earned_count = len(record.user_achievements)
    
    # Constraints
    @api.constrains('target_value')
    def _check_target_value(self):
        for record in self:
            if record.target_value <= 0:
                raise ValidationError(_("Target value must be positive"))
    
    @api.constrains('points_reward')
    def _check_points_reward(self):
        for record in self:
            if record.points_reward < 0:
                raise ValidationError(_("Points reward cannot be negative"))
    
    # Methods
    def check_user_eligibility(self, user_id):
        """Check if user is eligible for this achievement"""
        self.ensure_one()
        
        user = self.env['karmabot.user'].browse(user_id)
        if not user.exists():
            return False, "User not found"
        
        # Check if user already has this achievement
        existing = self.env['karmabot.user.achievement'].search([
            ('user_id', '=', user_id),
            ('achievement_id', '=', self.id)
        ], limit=1)
        
        if existing:
            return False, "Achievement already earned"
        
        # Check achievement criteria
        if self.achievement_type == 'points_total':
            return user.total_points >= self.target_value, f"Need {self.target_value} total points"
        
        elif self.achievement_type == 'points_single':
            # Check for single transaction with target points
            max_transaction = self.env['karmabot.loyalty.transaction'].search([
                ('user_id', '=', user_id),
                ('points', '>=', self.target_value),
                ('status', '=', 'approved')
            ], limit=1)
            return bool(max_transaction), f"Need single transaction of {self.target_value} points"
        
        elif self.achievement_type == 'scans_total':
            return user.total_scans >= self.target_value, f"Need {self.target_value} total scans"
        
        elif self.achievement_type == 'scans_daily':
            # Check daily scans
            today = fields.Date.today()
            daily_scans = self.env['karmabot.loyalty.transaction'].search_count([
                ('user_id', '=', user_id),
                ('transaction_type', '=', 'qr_scan'),
                ('create_date', '>=', today),
                ('status', '=', 'approved')
            ])
            return daily_scans >= self.target_value, f"Need {self.target_value} scans today"
        
        elif self.achievement_type == 'referrals_total':
            return user.total_referrals >= self.target_value, f"Need {self.target_value} referrals"
        
        elif self.achievement_type == 'cards_linked':
            return user.linked_cards_count >= self.target_value, f"Need {self.target_value} linked cards"
        
        elif self.achievement_type == 'consecutive_days':
            # Check consecutive days with activity
            consecutive_days = self._calculate_consecutive_days(user_id)
            return consecutive_days >= self.target_value, f"Need {self.target_value} consecutive days"
        
        elif self.achievement_type == 'category_explorer':
            # Check unique categories scanned
            unique_categories = self._get_unique_categories_scanned(user_id)
            return len(unique_categories) >= self.target_value, f"Need {self.target_value} unique categories"
        
        elif self.achievement_type == 'early_adopter':
            # Check if user registered early
            days_since_registration = (fields.Date.today() - user.registration_date.date()).days
            return days_since_registration <= self.target_value, f"Must be registered within {self.target_value} days"
        
        elif self.achievement_type == 'social_butterfly':
            # Check social interactions (referrals, shares, etc.)
            social_score = user.total_referrals * 2  # Simple social score
            return social_score >= self.target_value, f"Need social score of {self.target_value}"
        
        return False, "Unknown achievement type"
    
    def _calculate_consecutive_days(self, user_id):
        """Calculate consecutive days with activity"""
        # Get all transaction dates for user
        transactions = self.env['karmabot.loyalty.transaction'].search([
            ('user_id', '=', user_id),
            ('status', '=', 'approved')
        ], order='create_date desc')
        
        if not transactions:
            return 0
        
        # Group by date
        dates = set()
        for transaction in transactions:
            dates.add(transaction.create_date.date())
        
        # Calculate consecutive days
        sorted_dates = sorted(dates, reverse=True)
        consecutive_days = 0
        current_date = fields.Date.today()
        
        for date in sorted_dates:
            if date == current_date:
                consecutive_days += 1
                current_date = current_date - fields.timedelta(days=1)
            else:
                break
        
        return consecutive_days
    
    def _get_unique_categories_scanned(self, user_id):
        """Get unique categories scanned by user"""
        # Get all QR scans for user
        scans = self.env['karmabot.loyalty.transaction'].search([
            ('user_id', '=', user_id),
            ('transaction_type', '=', 'qr_scan'),
            ('status', '=', 'approved')
        ])
        
        # Get unique categories
        categories = set()
        for scan in scans:
            if scan.partner_card_id and scan.partner_card_id.category_id:
                categories.add(scan.partner_card_id.category_id.id)
        
        return categories
    
    def award_to_user(self, user_id):
        """Award achievement to user"""
        self.ensure_one()
        
        user = self.env['karmabot.user'].browse(user_id)
        if not user.exists():
            raise UserError(_("User not found"))
        
        # Check eligibility
        eligible, message = self.check_user_eligibility(user_id)
        if not eligible:
            raise UserError(_("User not eligible: %s") % message)
        
        # Create user achievement record
        user_achievement = self.env['karmabot.user.achievement'].create({
            'user_id': user_id,
            'achievement_id': self.id,
            'earned_date': fields.Datetime.now(),
            'points_reward': self.points_reward,
        })
        
        # Award points if specified
        if self.points_reward > 0:
            user.action_add_points(self.points_reward, f'Achievement reward: {self.name}')
        
        # Create transaction record
        self.env['karmabot.loyalty.transaction'].create({
            'user_id': user_id,
            'points': self.points_reward,
            'transaction_type': 'achievement_reward',
            'description': f'Achievement reward: {self.name}',
            'status': 'approved',
        })
        
        _logger.info(f"Achievement '{self.name}' awarded to user {user.name}")
        return user_achievement
    
    @api.model
    def check_all_achievements_for_user(self, user_id):
        """Check all achievements for a user and award eligible ones"""
        achievements = self.search([('is_active', '=', True)])
        awarded_count = 0
        
        for achievement in achievements:
            try:
                eligible, _ = achievement.check_user_eligibility(user_id)
                if eligible:
                    achievement.award_to_user(user_id)
                    awarded_count += 1
            except Exception as e:
                _logger.error(f"Error checking achievement {achievement.name} for user {user_id}: {e}")
        
        return awarded_count


class KarmaBotUserAchievement(models.Model):
    """User Achievement Record"""
    
    _name = 'karmabot.user.achievement'
    _description = 'KarmaBot User Achievement'
    _order = 'earned_date desc'
    
    user_id = fields.Many2one(
        'karmabot.user',
        string='User',
        required=True,
        ondelete='cascade'
    )
    
    achievement_id = fields.Many2one(
        'karmabot.achievement',
        string='Achievement',
        required=True,
        ondelete='cascade'
    )
    
    earned_date = fields.Datetime(
        string='Earned Date',
        required=True,
        default=fields.Datetime.now
    )
    
    points_reward = fields.Integer(
        string='Points Reward',
        help="Points awarded for this achievement"
    )
    
    # Computed Fields
    achievement_name = fields.Char(
        string='Achievement Name',
        related='achievement_id.name',
        store=True
    )
    
    achievement_icon = fields.Char(
        string='Icon',
        related='achievement_id.icon',
        store=True
    )
    
    achievement_color = fields.Char(
        string='Color',
        related='achievement_id.color',
        store=True
    )
    
    @api.constrains('user_id', 'achievement_id')
    def _check_unique_achievement(self):
        for record in self:
            existing = self.search([
                ('user_id', '=', record.user_id.id),
                ('achievement_id', '=', record.achievement_id.id),
                ('id', '!=', record.id)
            ], limit=1)
            
            if existing:
                raise ValidationError(_("User already has this achievement"))
