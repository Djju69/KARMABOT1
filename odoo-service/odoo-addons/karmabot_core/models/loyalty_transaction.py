# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KarmaBotLoyaltyTransaction(models.Model):
    """KarmaBot Loyalty Transaction Model - Track all loyalty points transactions"""
    
    _name = 'karmabot.loyalty.transaction'
    _description = 'KarmaBot Loyalty Transaction'
    _order = 'create_date desc'
    
    # Basic Information
    user_id = fields.Many2one(
        'karmabot.user',
        string='User',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    partner_card_id = fields.Many2one(
        'karmabot.partner.card',
        string='Partner Card',
        help="Card that generated this transaction"
    )
    
    points = fields.Integer(
        string='Points',
        required=True,
        help="Points amount (positive for earning, negative for spending)"
    )
    
    transaction_type = fields.Selection([
        ('qr_scan', 'QR Code Scan'),
        ('referral', 'Referral Bonus'),
        ('welcome', 'Welcome Bonus'),
        ('daily_login', 'Daily Login'),
        ('manual_adjustment', 'Manual Adjustment'),
        ('spend', 'Points Spend'),
        ('expire', 'Points Expiry'),
        ('refund', 'Refund'),
    ], string='Transaction Type', required=True, index=True)
    
    description = fields.Text(
        string='Description',
        help="Transaction description"
    )
    
    # Status and Validation
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='approved', required=True, index=True)
    
    fraud_check_passed = fields.Boolean(
        string='Fraud Check Passed',
        default=True,
        help="Whether fraud check passed for this transaction"
    )
    
    fraud_score = fields.Float(
        string='Fraud Score',
        default=0.0,
        help="Fraud detection score (0-1)"
    )
    
    # Geolocation Data
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="Transaction location latitude"
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="Transaction location longitude"
    )
    
    location_accuracy = fields.Float(
        string='Location Accuracy (m)',
        help="Location accuracy in meters"
    )
    
    # Timing
    transaction_date = fields.Datetime(
        string='Transaction Date',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    expiry_date = fields.Datetime(
        string='Expiry Date',
        help="When these points will expire"
    )
    
    # Related Data
    qr_code_id = fields.Char(
        string='QR Code ID',
        help="ID of the scanned QR code"
    )
    
    referral_user_id = fields.Many2one(
        'karmabot.user',
        string='Referred User',
        help="User who was referred (for referral transactions)"
    )
    
    # Computed Fields
    is_earning = fields.Boolean(
        string='Is Earning',
        compute='_compute_is_earning',
        store=True,
        help="Whether this is a points earning transaction"
    )
    
    is_spending = fields.Boolean(
        string='Is Spending',
        compute='_compute_is_spending',
        store=True,
        help="Whether this is a points spending transaction"
    )
    
    @api.depends('points')
    def _compute_is_earning(self):
        for record in self:
            record.is_earning = record.points > 0
    
    @api.depends('points')
    def _compute_is_spending(self):
        for record in self:
            record.is_spending = record.points < 0
    
    # Constraints
    @api.constrains('points')
    def _check_points(self):
        for record in self:
            if record.points == 0:
                raise ValidationError(_("Points amount cannot be zero"))
    
    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        for record in self:
            if record.latitude and (record.latitude < -90 or record.latitude > 90):
                raise ValidationError(_("Latitude must be between -90 and 90"))
            if record.longitude and (record.longitude < -180 or record.longitude > 180):
                raise ValidationError(_("Longitude must be between -180 and 180"))
    
    # Methods
    def action_approve(self):
        """Approve transaction"""
        self.ensure_one()
        if self.status != 'pending':
            raise ValidationError(_("Only pending transactions can be approved"))
        
        self.write({'status': 'approved'})
        
        # Update user points
        if self.is_earning:
            self.user_id.write({
                'total_points': self.user_id.total_points + self.points,
                'available_points': self.user_id.available_points + self.points,
            })
        elif self.is_spending:
            self.user_id.write({
                'available_points': self.user_id.available_points + self.points,  # points is negative
                'spent_points': self.user_id.spent_points - self.points,  # subtract negative
            })
        
        _logger.info(f"Approved transaction {self.id} for user {self.user_id.name}")
    
    def action_reject(self, reason=None):
        """Reject transaction"""
        self.ensure_one()
        if self.status != 'pending':
            raise ValidationError(_("Only pending transactions can be rejected"))
        
        self.write({
            'status': 'rejected',
            'description': f"{self.description or ''}\nRejected: {reason or 'No reason provided'}"
        })
        
        _logger.info(f"Rejected transaction {self.id} for user {self.user_id.name}: {reason}")
    
    def action_cancel(self, reason=None):
        """Cancel transaction"""
        self.ensure_one()
        if self.status not in ['pending', 'approved']:
            raise ValidationError(_("Only pending or approved transactions can be cancelled"))
        
        # If approved, reverse the points
        if self.status == 'approved':
            if self.is_earning:
                self.user_id.write({
                    'total_points': self.user_id.total_points - self.points,
                    'available_points': self.user_id.available_points - self.points,
                })
            elif self.is_spending:
                self.user_id.write({
                    'available_points': self.user_id.available_points - self.points,  # points is negative
                    'spent_points': self.user_id.spent_points + self.points,  # add negative
                })
        
        self.write({
            'status': 'cancelled',
            'description': f"{self.description or ''}\nCancelled: {reason or 'No reason provided'}"
        })
        
        _logger.info(f"Cancelled transaction {self.id} for user {self.user_id.name}: {reason}")
    
    @api.model
    def create_qr_reward(self, user_id, partner_card_id, points, qr_code_id=None, location_data=None):
        """Create QR scan reward transaction"""
        transaction_data = {
            'user_id': user_id,
            'partner_card_id': partner_card_id,
            'points': points,
            'transaction_type': 'qr_scan',
            'description': f'QR scan reward: {points} points',
            'qr_code_id': qr_code_id,
            'status': 'approved',
        }
        
        if location_data:
            transaction_data.update({
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'location_accuracy': location_data.get('accuracy'),
            })
        
        return self.create(transaction_data)
    
    @api.model
    def create_referral_bonus(self, user_id, referred_user_id, points):
        """Create referral bonus transaction"""
        return self.create({
            'user_id': user_id,
            'referral_user_id': referred_user_id,
            'points': points,
            'transaction_type': 'referral',
            'description': f'Referral bonus: {points} points',
            'status': 'approved',
        })
    
    @api.model
    def create_welcome_bonus(self, user_id, points):
        """Create welcome bonus transaction"""
        return self.create({
            'user_id': user_id,
            'points': points,
            'transaction_type': 'welcome',
            'description': f'Welcome bonus: {points} points',
            'status': 'approved',
        })
    
    @api.model
    def create_daily_login_bonus(self, user_id, points):
        """Create daily login bonus transaction"""
        return self.create({
            'user_id': user_id,
            'points': points,
            'transaction_type': 'daily_login',
            'description': f'Daily login bonus: {points} points',
            'status': 'approved',
        })
    
    @api.model
    def create_spend_transaction(self, user_id, points, description):
        """Create points spending transaction"""
        return self.create({
            'user_id': user_id,
            'points': -abs(points),  # Ensure negative
            'transaction_type': 'spend',
            'description': description,
            'status': 'approved',
        })
    
    def _run_fraud_checks(self):
        """Run fraud detection checks"""
        self.ensure_one()
        
        # Get loyalty program settings
        program = self.env['karmabot.loyalty.program'].search([('is_active', '=', True)], limit=1)
        if not program or not program.fraud_check_enabled:
            return True, 0.0
        
        fraud_score = program._calculate_fraud_score(
            self.user_id.id,
            abs(self.points),
            self.transaction_type
        )
        
        self.write({
            'fraud_score': fraud_score,
            'fraud_check_passed': fraud_score <= program.fraud_score_threshold
        })
        
        return self.fraud_check_passed, fraud_score
