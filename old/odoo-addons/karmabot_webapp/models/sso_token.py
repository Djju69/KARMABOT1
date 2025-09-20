# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import jwt
import uuid
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class KarmaBotSSOToken(models.Model):
    """KarmaBot SSO Token Model - JWT token management"""
    
    _name = 'karmabot.sso_token'
    _description = 'KarmaBot SSO Token'
    _order = 'create_date desc'
    
    # Basic Information
    token_id = fields.Char(
        string='Token ID',
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
        help="Unique token identifier"
    )
    
    user_id = fields.Many2one(
        'karmabot.user',
        string='User',
        required=True,
        ondelete='cascade',
        help="User associated with this token"
    )
    
    # Token Details
    token_type = fields.Selection([
        ('webapp_sso', 'WebApp SSO'),
        ('api_access', 'API Access'),
        ('admin_session', 'Admin Session'),
        ('partner_access', 'Partner Access'),
    ], string='Token Type', required=True, default='webapp_sso')
    
    token_value = fields.Text(
        string='Token Value',
        help="Encoded JWT token"
    )
    
    # Status and Validity
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the token is active"
    )
    
    expires_at = fields.Datetime(
        string='Expires At',
        required=True,
        help="When the token expires"
    )
    
    used_at = fields.Datetime(
        string='Used At',
        help="When the token was last used"
    )
    
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        help="Number of times token was used"
    )
    
    # Security
    ip_address = fields.Char(
        string='IP Address',
        help="IP address that created the token"
    )
    
    user_agent = fields.Char(
        string='User Agent',
        help="User agent that created the token"
    )
    
    # Computed Fields
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        help="Whether the token is expired"
    )
    
    is_valid = fields.Boolean(
        string='Is Valid',
        compute='_compute_is_valid',
        help="Whether the token is valid for use"
    )
    
    @api.depends('expires_at')
    def _compute_is_expired(self):
        for record in self:
            if record.expires_at:
                record.is_expired = fields.Datetime.now() > record.expires_at
            else:
                record.is_expired = False
    
    @api.depends('is_active', 'is_expired')
    def _compute_is_valid(self):
        for record in self:
            record.is_valid = record.is_active and not record.is_expired
    
    # Constraints
    @api.constrains('expires_at')
    def _check_expires_at(self):
        for record in self:
            if record.expires_at and record.expires_at <= fields.Datetime.now():
                raise ValidationError(_("Expiration date must be in the future"))
    
    # Methods
    def generate_jwt_token(self):
        """Generate JWT token"""
        self.ensure_one()
        
        # Get JWT secret from settings
        jwt_secret = self.env['ir.config_parameter'].sudo().get_param('karmabot.jwt_secret')
        if not jwt_secret:
            raise UserError(_("JWT secret not configured"))
        
        # Create payload
        payload = {
            'token_id': self.token_id,
            'user_id': self.user_id.telegram_id,
            'username': self.user_id.telegram_username,
            'first_name': self.user_id.telegram_first_name,
            'role': self.user_id.role,
            'token_type': self.token_type,
            'iat': fields.Datetime.now().timestamp(),
            'exp': self.expires_at.timestamp(),
        }
        
        # Generate token
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        # Update token value
        self.write({'token_value': token})
        
        _logger.info(f"JWT token generated for user {self.user_id.name}")
        return token
    
    def validate_token(self, provided_token):
        """Validate JWT token"""
        self.ensure_one()
        
        if not self.is_valid:
            return False, "Token is not valid"
        
        if not self.token_value:
            return False, "Token value not found"
        
        # Compare tokens
        if self.token_value != provided_token:
            return False, "Token mismatch"
        
        # Update usage
        self.write({
            'used_at': fields.Datetime.now(),
            'usage_count': self.usage_count + 1
        })
        
        return True, "Token is valid"
    
    def decode_token_payload(self, token):
        """Decode JWT token payload without verification"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def action_deactivate(self):
        """Deactivate token"""
        self.ensure_one()
        self.write({'is_active': False})
        _logger.info(f"Token {self.token_id} deactivated")
    
    def action_activate(self):
        """Activate token"""
        self.ensure_one()
        self.write({'is_active': True})
        _logger.info(f"Token {self.token_id} activated")
    
    def action_extend_expiry(self, hours=24):
        """Extend token expiry"""
        self.ensure_one()
        new_expiry = fields.Datetime.now() + timedelta(hours=hours)
        self.write({'expires_at': new_expiry})
        _logger.info(f"Token {self.token_id} expiry extended to {new_expiry}")
    
    @api.model
    def create_webapp_token(self, user_id, expires_hours=1):
        """Create WebApp SSO token"""
        user = self.env['karmabot.user'].browse(user_id)
        if not user.exists():
            raise UserError(_("User not found"))
        
        # Create token
        expires_at = fields.Datetime.now() + timedelta(hours=expires_hours)
        token_data = {
            'user_id': user_id,
            'token_type': 'webapp_sso',
            'expires_at': expires_at,
            'is_active': True,
        }
        
        token = self.create(token_data)
        
        # Generate JWT
        jwt_token = token.generate_jwt_token()
        
        return token, jwt_token
    
    @api.model
    def create_admin_token(self, user_id, expires_hours=8):
        """Create admin session token"""
        user = self.env['karmabot.user'].browse(user_id)
        if not user.exists():
            raise UserError(_("User not found"))
        
        if user.role not in ['admin', 'super_admin']:
            raise UserError(_("Admin access required"))
        
        # Create token
        expires_at = fields.Datetime.now() + timedelta(hours=expires_hours)
        token_data = {
            'user_id': user_id,
            'token_type': 'admin_session',
            'expires_at': expires_at,
            'is_active': True,
        }
        
        token = self.create(token_data)
        
        # Generate JWT
        jwt_token = token.generate_jwt_token()
        
        return token, jwt_token
    
    @api.model
    def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        expired_tokens = self.search([
            ('expires_at', '<', fields.Datetime.now()),
            ('is_active', '=', True)
        ])
        
        expired_tokens.write({'is_active': False})
        
        _logger.info(f"Deactivated {len(expired_tokens)} expired tokens")
        return len(expired_tokens)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"Token {record.token_id[:8]} ({record.user_id.name})"
            result.append((record.id, name))
        return result


class KarmaBotWebAppSession(models.Model):
    """WebApp Session Model - Track user sessions"""
    
    _name = 'karmabot.webapp_session'
    _description = 'KarmaBot WebApp Session'
    _order = 'create_date desc'
    
    # Basic Information
    session_id = fields.Char(
        string='Session ID',
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
        help="Unique session identifier"
    )
    
    user_id = fields.Many2one(
        'karmabot.user',
        string='User',
        required=True,
        ondelete='cascade',
        help="User associated with this session"
    )
    
    sso_token_id = fields.Many2one(
        'karmabot.sso_token',
        string='SSO Token',
        ondelete='cascade',
        help="SSO token used for this session"
    )
    
    # Session Details
    session_type = fields.Selection([
        ('user_cabinet', 'User Cabinet'),
        ('partner_cabinet', 'Partner Cabinet'),
        ('admin_dashboard', 'Admin Dashboard'),
        ('super_admin', 'Super Admin'),
    ], string='Session Type', required=True)
    
    # Status and Timing
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the session is active"
    )
    
    started_at = fields.Datetime(
        string='Started At',
        default=fields.Datetime.now,
        help="When the session started"
    )
    
    last_activity = fields.Datetime(
        string='Last Activity',
        default=fields.Datetime.now,
        help="Last activity in the session"
    )
    
    ended_at = fields.Datetime(
        string='Ended At',
        help="When the session ended"
    )
    
    # Technical Details
    ip_address = fields.Char(
        string='IP Address',
        help="IP address of the session"
    )
    
    user_agent = fields.Char(
        string='User Agent',
        help="User agent of the session"
    )
    
    browser = fields.Char(
        string='Browser',
        help="Browser name"
    )
    
    os = fields.Char(
        string='Operating System',
        help="Operating system"
    )
    
    device_type = fields.Selection([
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ], string='Device Type', help="Type of device")
    
    # Computed Fields
    duration_minutes = fields.Integer(
        string='Duration (minutes)',
        compute='_compute_duration',
        help="Session duration in minutes"
    )
    
    @api.depends('started_at', 'ended_at', 'last_activity')
    def _compute_duration(self):
        for record in self:
            if record.ended_at:
                duration = record.ended_at - record.started_at
            else:
                duration = record.last_activity - record.started_at
            
            record.duration_minutes = int(duration.total_seconds() / 60)
    
    # Methods
    def update_activity(self):
        """Update last activity timestamp"""
        self.ensure_one()
        self.write({'last_activity': fields.Datetime.now()})
    
    def end_session(self):
        """End the session"""
        self.ensure_one()
        self.write({
            'is_active': False,
            'ended_at': fields.Datetime.now()
        })
        _logger.info(f"Session {self.session_id} ended")
    
    @api.model
    def create_session(self, user_id, session_type, sso_token_id=None, **kwargs):
        """Create new WebApp session"""
        user = self.env['karmabot.user'].browse(user_id)
        if not user.exists():
            raise UserError(_("User not found"))
        
        # End any existing active sessions for this user
        existing_sessions = self.search([
            ('user_id', '=', user_id),
            ('is_active', '=', True)
        ])
        existing_sessions.end_session()
        
        # Create new session
        session_data = {
            'user_id': user_id,
            'session_type': session_type,
            'sso_token_id': sso_token_id,
            'is_active': True,
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent'),
            'browser': kwargs.get('browser'),
            'os': kwargs.get('os'),
            'device_type': kwargs.get('device_type'),
        }
        
        session = self.create(session_data)
        
        _logger.info(f"New session created for user {user.name}: {session_type}")
        return session
    
    @api.model
    def cleanup_inactive_sessions(self, hours=24):
        """Clean up inactive sessions"""
        cutoff_time = fields.Datetime.now() - timedelta(hours=hours)
        
        inactive_sessions = self.search([
            ('last_activity', '<', cutoff_time),
            ('is_active', '=', True)
        ])
        
        inactive_sessions.end_session()
        
        _logger.info(f"Ended {len(inactive_sessions)} inactive sessions")
        return len(inactive_sessions)
    
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"Session {record.session_id[:8]} ({record.user_id.name})"
            result.append((record.id, name))
        return result
