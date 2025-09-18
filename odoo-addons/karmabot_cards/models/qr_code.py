# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class KarmaBotQRCode(models.Model):
    """KarmaBot QR Code Model - QR code management and tracking"""
    
    _name = 'karmabot.qr_code'
    _description = 'KarmaBot QR Code'
    _order = 'create_date desc'
    
    # Basic Information
    code_id = fields.Char(
        string='QR Code ID',
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
        help="Unique QR code identifier"
    )
    
    partner_card_id = fields.Many2one(
        'karmabot.partner.card',
        string='Partner Card',
        required=True,
        ondelete='cascade',
        help="Associated partner card"
    )
    
    # QR Code Data
    qr_data = fields.Char(
        string='QR Data',
        required=True,
        help="Data encoded in QR code"
    )
    
    qr_type = fields.Selection([
        ('card', 'Card QR'),
        ('promo', 'Promo QR'),
        ('event', 'Event QR'),
        ('custom', 'Custom QR'),
    ], string='QR Type', default='card', required=True)
    
    # Status and Validity
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the QR code is active"
    )
    
    expires_at = fields.Datetime(
        string='Expires At',
        help="When the QR code expires"
    )
    
    max_scans = fields.Integer(
        string='Max Scans',
        default=0,
        help="Maximum number of scans (0 = unlimited)"
    )
    
    # Analytics
    scans_count = fields.Integer(
        string='Scans Count',
        default=0,
        help="Number of times QR code was scanned"
    )
    
    last_scan_date = fields.Datetime(
        string='Last Scan Date',
        help="Date of last scan"
    )
    
    unique_scans_count = fields.Integer(
        string='Unique Scans',
        default=0,
        help="Number of unique users who scanned"
    )
    
    # Security
    signature = fields.Char(
        string='Signature',
        help="HMAC signature for security"
    )
    
    secret_key = fields.Char(
        string='Secret Key',
        help="Secret key for signature generation"
    )
    
    # Computed Fields
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        help="Whether the QR code is expired"
    )
    
    is_valid = fields.Boolean(
        string='Is Valid',
        compute='_compute_is_valid',
        help="Whether the QR code is valid for scanning"
    )
    
    @api.depends('expires_at')
    def _compute_is_expired(self):
        for record in self:
            if record.expires_at:
                record.is_expired = fields.Datetime.now() > record.expires_at
            else:
                record.is_expired = False
    
    @api.depends('is_active', 'is_expired', 'scans_count', 'max_scans')
    def _compute_is_valid(self):
        for record in self:
            if not record.is_active or record.is_expired:
                record.is_valid = False
            elif record.max_scans > 0 and record.scans_count >= record.max_scans:
                record.is_valid = False
            else:
                record.is_valid = True
    
    # Constraints
    @api.constrains('max_scans')
    def _check_max_scans(self):
        for record in self:
            if record.max_scans < 0:
                raise ValidationError(_("Max scans cannot be negative"))
    
    @api.constrains('scans_count')
    def _check_scans_count(self):
        for record in self:
            if record.scans_count < 0:
                raise ValidationError(_("Scans count cannot be negative"))
    
    # Methods
    def action_scan(self, user_id=None):
        """Process QR code scan"""
        self.ensure_one()
        
        if not self.is_valid:
            raise UserError(_("QR code is not valid for scanning"))
        
        # Increment scan count
        self.write({
            'scans_count': self.scans_count + 1,
            'last_scan_date': fields.Datetime.now()
        })
        
        # Update partner card scan count
        if self.partner_card_id:
            self.partner_card_id.action_scan_qr()
        
        # Create scan record
        scan_data = {
            'qr_code_id': self.id,
            'scan_date': fields.Datetime.now(),
            'is_valid': True,
        }
        
        if user_id:
            scan_data['user_id'] = user_id
        
        self.env['karmabot.qr_scan'].create(scan_data)
        
        _logger.info(f"QR code {self.code_id} scanned by user {user_id}")
        
        return {
            'success': True,
            'message': 'QR code scanned successfully',
            'card_name': self.partner_card_id.name if self.partner_card_id else 'Unknown',
            'points': self._calculate_points(),
        }
    
    def _calculate_points(self):
        """Calculate points for QR scan"""
        self.ensure_one()
        
        # Get loyalty program
        program = self.env['karmabot.loyalty.program'].search([
            ('is_active', '=', True)
        ], limit=1)
        
        if program:
            return program.points_per_scan
        else:
            return 10  # Default points
    
    def action_generate_signature(self):
        """Generate HMAC signature for QR code"""
        self.ensure_one()
        
        if not self.secret_key:
            # Generate secret key
            self.secret_key = str(uuid.uuid4())
        
        # Create signature
        message = f"{self.code_id}:{self.qr_data}:{self.partner_card_id.id}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        self.write({'signature': signature})
        
        _logger.info(f"Signature generated for QR code {self.code_id}")
    
    def action_validate_signature(self, provided_signature):
        """Validate QR code signature"""
        self.ensure_one()
        
        if not self.signature:
            return False
        
        return hmac.compare_digest(self.signature, provided_signature)
    
    def action_deactivate(self):
        """Deactivate QR code"""
        self.ensure_one()
        self.write({'is_active': False})
        _logger.info(f"QR code {self.code_id} deactivated")
    
    def action_activate(self):
        """Activate QR code"""
        self.ensure_one()
        self.write({'is_active': True})
        _logger.info(f"QR code {self.code_id} activated")
    
    def action_reset_scans(self):
        """Reset scan count"""
        self.ensure_one()
        self.write({
            'scans_count': 0,
            'unique_scans_count': 0,
            'last_scan_date': False
        })
        _logger.info(f"Scan count reset for QR code {self.code_id}")
    
    @api.model
    def create_for_card(self, partner_card_id, qr_type='card', expires_at=None, max_scans=0):
        """Create QR code for partner card"""
        try:
            partner_card = self.env['karmabot.partner.card'].browse(partner_card_id)
            if not partner_card.exists():
                raise UserError(_("Partner card not found"))
            
            # Generate QR data
            qr_data = f"KARMA_CARD:{partner_card.qr_code_id}"
            
            # Create QR code
            qr_code_data = {
                'partner_card_id': partner_card_id,
                'qr_data': qr_data,
                'qr_type': qr_type,
                'expires_at': expires_at,
                'max_scans': max_scans,
                'is_active': True,
            }
            
            qr_code = self.create(qr_code_data)
            
            # Generate signature
            qr_code.action_generate_signature()
            
            _logger.info(f"QR code created for card {partner_card.name}")
            return qr_code
            
        except Exception as e:
            _logger.error(f"Error creating QR code: {e}")
            raise UserError(_("Error creating QR code: %s") % str(e))
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"QR {record.code_id[:8]} ({record.partner_card_id.name})"
            result.append((record.id, name))
        return result


class KarmaBotQRScan(models.Model):
    """QR Code Scan Record"""
    
    _name = 'karmabot.qr_scan'
    _description = 'KarmaBot QR Scan'
    _order = 'scan_date desc'
    
    qr_code_id = fields.Many2one(
        'karmabot.qr_code',
        string='QR Code',
        required=True,
        ondelete='cascade'
    )
    
    user_id = fields.Many2one(
        'karmabot.user',
        string='User',
        help="User who scanned the QR code"
    )
    
    scan_date = fields.Datetime(
        string='Scan Date',
        required=True,
        default=fields.Datetime.now
    )
    
    is_valid = fields.Boolean(
        string='Valid Scan',
        default=True,
        help="Whether the scan was valid"
    )
    
    points_awarded = fields.Integer(
        string='Points Awarded',
        default=0,
        help="Points awarded for this scan"
    )
    
    location_latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="Scan location latitude"
    )
    
    location_longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="Scan location longitude"
    )
    
    fraud_score = fields.Float(
        string='Fraud Score',
        default=0.0,
        help="Fraud detection score"
    )
    
    fraud_check_passed = fields.Boolean(
        string='Fraud Check Passed',
        default=True,
        help="Whether fraud check passed"
    )
