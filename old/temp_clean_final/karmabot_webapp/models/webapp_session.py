# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import uuid
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


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
