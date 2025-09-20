# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging
import jwt
import json

_logger = logging.getLogger(__name__)


class KarmaBotPartnerCabinetController(http.Controller):
    """Controller for KarmaBot Partner Cabinet"""
    
    @http.route('/my/partner', type='http', auth='public', website=True)
    def partner_cabinet(self, sso=None, **kw):
        """Partner cabinet page"""
        try:
            # Validate SSO token
            if not sso:
                return request.render('karmabot_cards.partner_cabinet_login')
            
            user_data = self._validate_sso_token(sso)
            if not user_data:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Invalid or expired token'
                })
            
            # Get partner from database
            partner = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not partner:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Partner not found'
                })
            
            # Check if user is a partner
            if partner.role not in ['partner', 'admin', 'super_admin']:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Access denied. Partner role required.'
                })
            
            # Get partner statistics
            stats = self._get_partner_stats(partner)
            
            # Get partner cards
            partner_cards = request.env['karmabot.partner.card'].sudo().search([
                ('partner_id', '=', partner.id)
            ], order='create_date desc')
            
            # Get recent activity
            recent_activity = self._get_recent_activity(partner)
            
            return request.render('karmabot_cards.partner_cabinet', {
                'partner': partner,
                'stats': stats,
                'partner_cards': partner_cards,
                'recent_activity': recent_activity,
                'sso_token': sso,
            })
            
        except Exception as e:
            _logger.error(f"Error in partner_cabinet: {e}")
            return request.render('karmabot_cards.partner_cabinet_login', {
                'error': 'An error occurred. Please try again.'
            })
    
    @http.route('/my/partner/create-card', type='http', auth='public', website=True)
    def create_card_form(self, sso=None, **kw):
        """Card creation form"""
        try:
            # Validate SSO token
            if not sso:
                return request.render('karmabot_cards.partner_cabinet_login')
            
            user_data = self._validate_sso_token(sso)
            if not user_data:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Invalid or expired token'
                })
            
            # Get partner
            partner = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not partner or partner.role not in ['partner', 'admin', 'super_admin']:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Access denied'
                })
            
            # Get categories
            categories = request.env['karmabot.category'].sudo().search([
                ('is_active', '=', True)
            ])
            
            return request.render('karmabot_cards.create_card_form', {
                'partner': partner,
                'categories': categories,
                'sso_token': sso,
            })
            
        except Exception as e:
            _logger.error(f"Error in create_card_form: {e}")
            return request.render('karmabot_cards.partner_cabinet_login', {
                'error': 'An error occurred'
            })
    
    @http.route('/my/partner/create-card', type='json', auth='public', methods=['POST'])
    def create_card(self, **kw):
        """Create new card via AJAX"""
        try:
            data = request.jsonrequest
            sso_token = data.get('sso_token')
            
            # Validate SSO token
            user_data = self._validate_sso_token(sso_token)
            if not user_data:
                return {'error': 'Invalid or expired token'}
            
            # Get partner
            partner = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not partner or partner.role not in ['partner', 'admin', 'super_admin']:
                return {'error': 'Access denied'}
            
            # Create card
            card_data = {
                'name': data.get('name'),
                'partner_id': partner.id,
                'category_id': data.get('category_id'),
                'description': data.get('description'),
                'address': data.get('address'),
                'phone': data.get('phone'),
                'email': data.get('email'),
                'website': data.get('website'),
                'discount_percent': data.get('discount_percent', 0),
                'special_offers': data.get('special_offers'),
                'status': 'draft',
            }
            
            card = request.env['karmabot.partner.card'].sudo().create(card_data)
            
            return {
                'success': True,
                'message': 'Card created successfully',
                'card_id': card.id
            }
            
        except Exception as e:
            _logger.error(f"Error in create_card: {e}")
            return {'error': 'An error occurred while creating the card'}
    
    @http.route('/my/partner/analytics', type='http', auth='public', website=True)
    def partner_analytics(self, sso=None, **kw):
        """Partner analytics page"""
        try:
            # Validate SSO token
            if not sso:
                return request.render('karmabot_cards.partner_cabinet_login')
            
            user_data = self._validate_sso_token(sso)
            if not user_data:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Invalid or expired token'
                })
            
            # Get partner
            partner = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not partner or partner.role not in ['partner', 'admin', 'super_admin']:
                return request.render('karmabot_cards.partner_cabinet_login', {
                    'error': 'Access denied'
                })
            
            # Get analytics data
            analytics = self._get_partner_analytics(partner)
            
            return request.render('karmabot_cards.partner_analytics', {
                'partner': partner,
                'analytics': analytics,
                'sso_token': sso,
            })
            
        except Exception as e:
            _logger.error(f"Error in partner_analytics: {e}")
            return request.render('karmabot_cards.partner_cabinet_login', {
                'error': 'An error occurred'
            })
    
    def _validate_sso_token(self, token):
        """Validate SSO token and return user data"""
        try:
            # Get JWT secret from settings
            jwt_secret = request.env['ir.config_parameter'].sudo().get_param('karmabot.jwt_secret')
            if not jwt_secret:
                _logger.error("JWT secret not configured")
                return None
            
            # Decode token
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            # Check token type
            if payload.get('token_type') != 'webapp_sso':
                return None
            
            # Check expiration
            if payload.get('exp', 0) < fields.Datetime.now().timestamp():
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            _logger.warning("SSO token expired")
            return None
        except jwt.InvalidTokenError:
            _logger.warning("Invalid SSO token")
            return None
        except Exception as e:
            _logger.error(f"Error validating SSO token: {e}")
            return None
    
    def _get_partner_stats(self, partner):
        """Get partner statistics"""
        try:
            # Get cards statistics
            cards = request.env['karmabot.partner.card'].sudo().search([
                ('partner_id', '=', partner.id)
            ])
            
            total_cards = len(cards)
            published_cards = len(cards.filtered(lambda c: c.status == 'published'))
            pending_cards = len(cards.filtered(lambda c: c.status == 'pending'))
            total_views = sum(cards.mapped('views_count'))
            total_scans = sum(cards.mapped('scans_count'))
            
            return {
                'total_cards': total_cards,
                'published_cards': published_cards,
                'pending_cards': pending_cards,
                'total_views': total_views,
                'total_scans': total_scans,
            }
            
        except Exception as e:
            _logger.error(f"Error getting partner stats: {e}")
            return {}
    
    def _get_recent_activity(self, partner):
        """Get recent activity for partner"""
        try:
            activities = []
            
            # Get recent card activities
            recent_cards = request.env['karmabot.partner.card'].sudo().search([
                ('partner_id', '=', partner.id)
            ], limit=5, order='write_date desc')
            
            for card in recent_cards:
                activities.append({
                    'title': f'Card "{card.name}" updated',
                    'description': f'Status: {card.status.title()}',
                    'date': card.write_date.strftime('%Y-%m-%d %H:%M')
                })
            
            return activities
            
        except Exception as e:
            _logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_partner_analytics(self, partner):
        """Get detailed analytics for partner"""
        try:
            # Get cards
            cards = request.env['karmabot.partner.card'].sudo().search([
                ('partner_id', '=', partner.id)
            ])
            
            # Calculate analytics
            analytics = {
                'total_cards': len(cards),
                'published_cards': len(cards.filtered(lambda c: c.status == 'published')),
                'pending_cards': len(cards.filtered(lambda c: c.status == 'pending')),
                'draft_cards': len(cards.filtered(lambda c: c.status == 'draft')),
                'rejected_cards': len(cards.filtered(lambda c: c.status == 'rejected')),
                'total_views': sum(cards.mapped('views_count')),
                'total_scans': sum(cards.mapped('scans_count')),
                'avg_views_per_card': sum(cards.mapped('views_count')) / len(cards) if cards else 0,
                'avg_scans_per_card': sum(cards.mapped('scans_count')) / len(cards) if cards else 0,
            }
            
            # Get monthly data
            current_month = fields.Date.today().replace(day=1)
            monthly_cards = cards.filtered(lambda c: c.create_date.date() >= current_month)
            analytics['monthly_new_cards'] = len(monthly_cards)
            
            return analytics
            
        except Exception as e:
            _logger.error(f"Error getting partner analytics: {e}")
            return {}
