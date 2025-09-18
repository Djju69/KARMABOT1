# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging
import jwt
import json

_logger = logging.getLogger(__name__)


class KarmaBotUserCabinetController(http.Controller):
    """Controller for KarmaBot User Cabinet"""
    
    @http.route('/my/profile', type='http', auth='public', website=True)
    def user_cabinet(self, sso=None, **kw):
        """User cabinet page"""
        try:
            # Validate SSO token
            if not sso:
                return request.render('karmabot_core.user_cabinet_login')
            
            user_data = self._validate_sso_token(sso)
            if not user_data:
                return request.render('karmabot_core.user_cabinet_login', {
                    'error': 'Invalid or expired token'
                })
            
            # Get user from database
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not user:
                return request.render('karmabot_core.user_cabinet_login', {
                    'error': 'User not found'
                })
            
            # Get user statistics
            stats = self._get_user_stats(user)
            
            # Get recent transactions
            recent_transactions = request.env['karmabot.loyalty.transaction'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=10, order='create_date desc')
            
            # Get linked cards
            linked_cards = request.env['karmabot.user.card'].sudo().search([
                ('user_id', '=', user.id),
                ('is_active', '=', True)
            ])
            
            return request.render('karmabot_core.user_cabinet', {
                'user': user,
                'stats': stats,
                'recent_transactions': recent_transactions,
                'linked_cards': linked_cards,
                'sso_token': sso,
            })
            
        except Exception as e:
            _logger.error(f"Error in user_cabinet: {e}")
            return request.render('karmabot_core.user_cabinet_login', {
                'error': 'An error occurred. Please try again.'
            })
    
    @http.route('/my/profile/add-card', type='json', auth='public', methods=['POST'])
    def add_user_card(self, **kw):
        """Add card to user account"""
        try:
            data = request.jsonrequest
            sso_token = data.get('sso_token')
            card_number = data.get('card_number')
            card_type = data.get('card_type', 'physical')
            
            # Validate SSO token
            user_data = self._validate_sso_token(sso_token)
            if not user_data:
                return {'error': 'Invalid or expired token'}
            
            # Get user
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not user:
                return {'error': 'User not found'}
            
            # Check if card already exists
            existing_card = request.env['karmabot.user.card'].sudo().search([
                ('card_number', '=', card_number)
            ], limit=1)
            
            if existing_card:
                return {'error': 'Card already linked to another user'}
            
            # Create new card
            card = request.env['karmabot.user.card'].sudo().create({
                'user_id': user.id,
                'card_number': card_number,
                'card_type': card_type,
                'is_active': True,
            })
            
            return {
                'success': True,
                'message': 'Card added successfully',
                'card_id': card.id
            }
            
        except Exception as e:
            _logger.error(f"Error in add_user_card: {e}")
            return {'error': 'An error occurred while adding the card'}
    
    @http.route('/my/profile/spend-points', type='json', auth='public', methods=['POST'])
    def spend_user_points(self, **kw):
        """Spend user points"""
        try:
            data = request.jsonrequest
            sso_token = data.get('sso_token')
            points = data.get('points')
            description = data.get('description', 'Points spent')
            
            # Validate SSO token
            user_data = self._validate_sso_token(sso_token)
            if not user_data:
                return {'error': 'Invalid or expired token'}
            
            # Get user
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not user:
                return {'error': 'User not found'}
            
            # Check if user has enough points
            if user.available_points < points:
                return {'error': 'Insufficient points'}
            
            # Spend points
            user.action_spend_points(points, description)
            
            return {
                'success': True,
                'message': f'{points} points spent successfully',
                'remaining_points': user.available_points
            }
            
        except Exception as e:
            _logger.error(f"Error in spend_user_points: {e}")
            return {'error': 'An error occurred while spending points'}
    
    @http.route('/my/profile/transactions', type='json', auth='public', methods=['POST'])
    def get_user_transactions(self, **kw):
        """Get user transactions with pagination"""
        try:
            data = request.jsonrequest
            sso_token = data.get('sso_token')
            page = data.get('page', 1)
            limit = data.get('limit', 20)
            
            # Validate SSO token
            user_data = self._validate_sso_token(sso_token)
            if not user_data:
                return {'error': 'Invalid or expired token'}
            
            # Get user
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not user:
                return {'error': 'User not found'}
            
            # Get transactions
            offset = (page - 1) * limit
            transactions = request.env['karmabot.loyalty.transaction'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=limit, offset=offset, order='create_date desc')
            
            # Format transactions
            transaction_list = []
            for transaction in transactions:
                transaction_list.append({
                    'id': transaction.id,
                    'type': transaction.transaction_type,
                    'points': transaction.points,
                    'description': transaction.description,
                    'date': transaction.transaction_date.isoformat(),
                    'status': transaction.status,
                })
            
            return {
                'success': True,
                'transactions': transaction_list,
                'page': page,
                'limit': limit,
            }
            
        except Exception as e:
            _logger.error(f"Error in get_user_transactions: {e}")
            return {'error': 'An error occurred while fetching transactions'}
    
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
    
    def _get_user_stats(self, user):
        """Get user statistics"""
        try:
            # Calculate level
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            level_info = {}
            if program:
                level_info = program.calculate_user_level(user.total_points)
            
            # Get monthly stats
            current_month = fields.Date.today().replace(day=1)
            monthly_transactions = request.env['karmabot.loyalty.transaction'].sudo().search([
                ('user_id', '=', user.id),
                ('create_date', '>=', current_month),
                ('points', '>', 0)
            ])
            monthly_points = sum(monthly_transactions.mapped('points'))
            
            return {
                'total_points': user.total_points,
                'available_points': user.available_points,
                'spent_points': user.spent_points,
                'total_scans': user.total_scans,
                'total_referrals': user.total_referrals,
                'monthly_points': monthly_points,
                'level': level_info.get('level', 0),
                'level_name': level_info.get('name', 'Newcomer'),
                'points_to_next': level_info.get('points_to_next', 0),
                'next_level_points': level_info.get('next_level_points', 0),
            }
            
        except Exception as e:
            _logger.error(f"Error getting user stats: {e}")
            return {}
