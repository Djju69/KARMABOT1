# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import uuid
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class KarmaBotPartnerCard(models.Model):
    """KarmaBot Partner Card Model - Partner business cards"""
    
    _name = 'karmabot.partner.card'
    _description = 'KarmaBot Partner Card'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # Basic Information
    name = fields.Char(
        string='Business Name',
        required=True,
        tracking=True,
        help="Name of the business"
    )
    
    partner_id = fields.Many2one(
        'karmabot.user',
        string='Partner',
        required=True,
        domain=[('role', 'in', ['partner', 'admin', 'super_admin'])],
        tracking=True,
        help="Partner who owns this card"
    )
    
    category_id = fields.Many2one(
        'karmabot.category',
        string='Category',
        required=True,
        tracking=True,
        help="Business category"
    )
    
    # Business Details
    description = fields.Text(
        string='Description',
        tracking=True,
        help="Business description"
    )
    
    address = fields.Text(
        string='Address',
        tracking=True,
        help="Business address"
    )
    
    phone = fields.Char(
        string='Phone',
        tracking=True,
        help="Business phone number"
    )
    
    email = fields.Char(
        string='Email',
        tracking=True,
        help="Business email"
    )
    
    website = fields.Char(
        string='Website',
        tracking=True,
        help="Business website"
    )
    
    # Location
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="Business latitude"
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="Business longitude"
    )
    
    # Offers and Discounts
    discount_percent = fields.Float(
        string='Discount %',
        default=0.0,
        tracking=True,
        help="Discount percentage for loyalty points"
    )
    
    special_offers = fields.Text(
        string='Special Offers',
        tracking=True,
        help="Special offers and promotions"
    )
    
    min_points_required = fields.Integer(
        string='Min Points Required',
        default=0,
        tracking=True,
        help="Minimum points required for discount"
    )
    
    # Status and Moderation
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help="Reason for rejection"
    )
    
    moderation_notes = fields.Text(
        string='Moderation Notes',
        help="Internal moderation notes"
    )
    
    # Images
    image_1 = fields.Binary(
        string='Image 1',
        help="First business image"
    )
    
    image_2 = fields.Binary(
        string='Image 2',
        help="Second business image"
    )
    
    image_3 = fields.Binary(
        string='Image 3',
        help="Third business image"
    )
    
    image_4 = fields.Binary(
        string='Image 4',
        help="Fourth business image"
    )
    
    image_5 = fields.Binary(
        string='Image 5',
        help="Fifth business image"
    )
    
    image_6 = fields.Binary(
        string='Image 6',
        help="Sixth business image"
    )
    
    # QR Code
    qr_code_id = fields.Char(
        string='QR Code ID',
        default=lambda self: str(uuid.uuid4()),
        help="Unique QR code identifier"
    )
    
    qr_code_image = fields.Binary(
        string='QR Code Image',
        help="Generated QR code image"
    )
    
    # Analytics
    views_count = fields.Integer(
        string='Views Count',
        default=0,
        tracking=True,
        help="Number of times card was viewed"
    )
    
    scans_count = fields.Integer(
        string='Scans Count',
        default=0,
        tracking=True,
        help="Number of QR code scans"
    )
    
    last_scan_date = fields.Datetime(
        string='Last Scan Date',
        help="Date of last QR code scan"
    )
    
    # Computed Fields
    is_published = fields.Boolean(
        string='Is Published',
        compute='_compute_is_published',
        store=True,
        help="Whether the card is published and visible to users"
    )
    
    has_images = fields.Boolean(
        string='Has Images',
        compute='_compute_has_images',
        help="Whether the card has any images"
    )
    
    image_count = fields.Integer(
        string='Image Count',
        compute='_compute_image_count',
        help="Number of images uploaded"
    )
    
    @api.depends('status')
    def _compute_is_published(self):
        for record in self:
            record.is_published = record.status == 'published'
    
    @api.depends('image_1', 'image_2', 'image_3', 'image_4', 'image_5', 'image_6')
    def _compute_has_images(self):
        for record in self:
            record.has_images = any([
                record.image_1, record.image_2, record.image_3,
                record.image_4, record.image_5, record.image_6
            ])
    
    @api.depends('image_1', 'image_2', 'image_3', 'image_4', 'image_5', 'image_6')
    def _compute_image_count(self):
        for record in self:
            count = 0
            if record.image_1: count += 1
            if record.image_2: count += 1
            if record.image_3: count += 1
            if record.image_4: count += 1
            if record.image_5: count += 1
            if record.image_6: count += 1
            record.image_count = count
    
    # Constraints
    @api.constrains('discount_percent')
    def _check_discount_percent(self):
        for record in self:
            if record.discount_percent < 0 or record.discount_percent > 100:
                raise ValidationError(_("Discount percentage must be between 0 and 100"))
    
    @api.constrains('min_points_required')
    def _check_min_points(self):
        for record in self:
            if record.min_points_required < 0:
                raise ValidationError(_("Minimum points required cannot be negative"))
    
    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        for record in self:
            if record.latitude and (record.latitude < -90 or record.latitude > 90):
                raise ValidationError(_("Latitude must be between -90 and 90"))
            if record.longitude and (record.longitude < -180 or record.longitude > 180):
                raise ValidationError(_("Longitude must be between -180 and 180"))
    
    # Methods
    def action_submit_for_moderation(self):
        """Submit card for moderation"""
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_("Only draft cards can be submitted for moderation"))
        
        # Validate required fields
        if not self.name or not self.category_id:
            raise UserError(_("Business name and category are required"))
        
        if not self.description:
            raise UserError(_("Business description is required"))
        
        if not self.address:
            raise UserError(_("Business address is required"))
        
        if not self.phone:
            raise UserError(_("Business phone is required"))
        
        self.write({
            'status': 'pending',
            'moderation_notes': 'Submitted for moderation'
        })
        
        # Create activity for moderators
        self.activity_schedule(
            'karmabot_cards.mail_activity_type_moderation',
            summary=f'Card "{self.name}" needs moderation',
            note=f'New card submitted by {self.partner_id.name}',
            user_id=self.env.ref('karmabot.group_karmabot_admin').users[0].id if self.env.ref('karmabot.group_karmabot_admin').users else False
        )
        
        _logger.info(f"Card {self.name} submitted for moderation by {self.partner_id.name}")
    
    def action_approve(self):
        """Approve card"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Only pending cards can be approved"))
        
        self.write({
            'status': 'approved',
            'moderation_notes': f'Approved by {self.env.user.name} on {fields.Datetime.now()}'
        })
        
        # Notify partner
        self.message_post(
            body=f'Your card "{self.name}" has been approved!',
            message_type='notification'
        )
        
        _logger.info(f"Card {self.name} approved by {self.env.user.name}")
    
    def action_reject(self, reason=None):
        """Reject card"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Only pending cards can be rejected"))
        
        if not reason:
            raise UserError(_("Rejection reason is required"))
        
        self.write({
            'status': 'rejected',
            'rejection_reason': reason,
            'moderation_notes': f'Rejected by {self.env.user.name} on {fields.Datetime.now()}: {reason}'
        })
        
        # Notify partner
        self.message_post(
            body=f'Your card "{self.name}" has been rejected. Reason: {reason}',
            message_type='notification'
        )
        
        _logger.info(f"Card {self.name} rejected by {self.env.user.name}: {reason}")
    
    def action_publish(self):
        """Publish card"""
        self.ensure_one()
        if self.status != 'approved':
            raise UserError(_("Only approved cards can be published"))
        
        self.write({
            'status': 'published',
            'moderation_notes': f'Published by {self.env.user.name} on {fields.Datetime.now()}'
        })
        
        # Generate QR code if not exists
        if not self.qr_code_image:
            self._generate_qr_code()
        
        _logger.info(f"Card {self.name} published by {self.env.user.name}")
    
    def action_archive(self):
        """Archive card"""
        self.ensure_one()
        if self.status not in ['published', 'approved']:
            raise UserError(_("Only published or approved cards can be archived"))
        
        self.write({
            'status': 'archived',
            'moderation_notes': f'Archived by {self.env.user.name} on {fields.Datetime.now()}'
        })
        
        _logger.info(f"Card {self.name} archived by {self.env.user.name}")
    
    def action_view_card(self):
        """Increment view count"""
        self.ensure_one()
        self.write({
            'views_count': self.views_count + 1
        })
    
    def action_scan_qr(self):
        """Increment scan count"""
        self.ensure_one()
        self.write({
            'scans_count': self.scans_count + 1,
            'last_scan_date': fields.Datetime.now()
        })
        
        _logger.info(f"QR code scanned for card {self.name}")
    
    def _generate_qr_code(self):
        """Generate QR code for the card"""
        self.ensure_one()
        try:
            import qrcode
            from io import BytesIO
            import base64
            
            # Create QR code data
            qr_data = f"KARMA_CARD:{self.qr_code_id}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_image = base64.b64encode(buffer.getvalue())
            
            self.write({
                'qr_code_image': qr_image
            })
            
            _logger.info(f"QR code generated for card {self.name}")
            
        except ImportError:
            _logger.warning("qrcode library not installed, cannot generate QR code")
        except Exception as e:
            _logger.error(f"Error generating QR code: {e}")
    
    @api.model
    def create_from_telegram(self, partner_id, card_data):
        """Create card from Telegram data"""
        try:
            # Validate partner
            partner = self.env['karmabot.user'].browse(partner_id)
            if not partner.exists() or partner.role not in ['partner', 'admin', 'super_admin']:
                raise UserError(_("Invalid partner"))
            
            # Create card
            card_data.update({
                'partner_id': partner_id,
                'status': 'draft',
                'qr_code_id': str(uuid.uuid4()),
            })
            
            card = self.create(card_data)
            
            _logger.info(f"Card created from Telegram: {card.name}")
            return card
            
        except Exception as e:
            _logger.error(f"Error creating card from Telegram: {e}")
            raise UserError(_("Error creating card: %s") % str(e))
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} ({record.category_id.name})"
            result.append((record.id, name))
        return result
