# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging
import jwt
import json

_logger = logging.getLogger(__name__)


class KarmaBotLoyaltyAPIController(http.Controller):
    """API Controller for KarmaBot Loyalty System"""
    
    @http.route('/api/loyalty/scan-qr', type='json', auth='public', methods=['POST'])
    def scan_qr_code(self, **kw):
        """Process QR code scan and award points"""
        try:
            data = request.jsonrequest
            
            # Validate required fields
            required_fields = ['user_id', 'qr_code_id', 'points']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}
            
            user_id = data['user_id']
            qr_code_id = data['qr_code_id']
            points = data['points']
            
            # Get user
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return {'error': 'User not found'}
            
            # Get QR code
            qr_code = request.env['karmabot.qr_code'].sudo().search([
                ('code_id', '=', qr_code_id)
            ], limit=1)
            
            if not qr_code:
                return {'error': 'QR code not found'}
            
            # Validate QR code
            if not qr_code.is_valid:
                return {'error': 'QR code is not valid'}
            
            # Get loyalty program
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            if not program:
                return {'error': 'No active loyalty program'}
            
            # Validate transaction
            valid, message = program.validate_transaction(
                user.id, points, 'qr_scan',
                ip_address=data.get('ip_address'),
                device_fingerprint=data.get('device_fingerprint'),
                user_agent=data.get('user_agent'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )
            
            if not valid:
                return {'error': message}
            
            # Create transaction
            location_data = None
            if data.get('latitude') and data.get('longitude'):
                location_data = {
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'accuracy': data.get('accuracy', 0)
                }
            
            transaction = request.env['karmabot.loyalty.transaction'].sudo().create_qr_reward(
                user_id=user.id,
                partner_card_id=qr_code.partner_card_id.id,
                points=points,
                qr_code_id=qr_code_id,
                location_data=location_data,
                ip_address=data.get('ip_address'),
                device_fingerprint=data.get('device_fingerprint'),
                user_agent=data.get('user_agent'),
                source=data.get('source', 'telegram_bot'),
                session_id=data.get('session_id')
            )
            
            # Update QR code scan count
            qr_code.action_scan(user.id)
            
            # Check for achievements
            achievements_earned = request.env['karmabot.achievement'].sudo().check_all_achievements_for_user(user.id)
            
            return {
                'success': True,
                'message': f'QR code scanned successfully! Earned {points} points.',
                'transaction_id': transaction.id,
                'user_points': user.available_points,
                'achievements_earned': achievements_earned,
                'level_up': transaction.is_level_up
            }
            
        except Exception as e:
            _logger.error(f"Error in scan_qr_code: {e}")
            return {'error': 'An error occurred while processing QR scan'}
    
    @http.route('/api/loyalty/referral', type='json', auth='public', methods=['POST'])
    def process_referral(self, **kw):
        """Process referral bonus"""
        try:
            data = request.jsonrequest
            
            # Validate required fields
            required_fields = ['referrer_id', 'referred_id']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}
            
            referrer_id = data['referrer_id']
            referred_id = data['referred_id']
            
            # Get users
            referrer = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(referrer_id))
            ], limit=1)
            
            referred = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(referred_id))
            ], limit=1)
            
            if not referrer or not referred:
                return {'error': 'User not found'}
            
            # Check if already referred
            existing_referral = request.env['karmabot.loyalty.transaction'].sudo().search([
                ('user_id', '=', referrer.id),
                ('referral_user_id', '=', referred.id),
                ('transaction_type', '=', 'referral')
            ], limit=1)
            
            if existing_referral:
                return {'error': 'Referral already processed'}
            
            # Get loyalty program
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            if not program:
                return {'error': 'No active loyalty program'}
            
            # Check referral limits
            referral_count = request.env['karmabot.loyalty.transaction'].sudo().search_count([
                ('user_id', '=', referrer.id),
                ('transaction_type', '=', 'referral')
            ])
            
            if referral_count >= program.max_referrals_per_user:
                return {'error': 'Referral limit reached'}
            
            # Create referral transaction
            transaction = request.env['karmabot.loyalty.transaction'].sudo().create_referral_bonus(
                user_id=referrer.id,
                referred_user_id=referred.id,
                points=program.referral_bonus,
                ip_address=data.get('ip_address'),
                device_fingerprint=data.get('device_fingerprint'),
                user_agent=data.get('user_agent'),
                source=data.get('source', 'telegram_bot'),
                session_id=data.get('session_id')
            )
            
            # Update referrer's referral count
            referrer.write({
                'total_referrals': referrer.total_referrals + 1
            })
            
            # Set referred user's referrer
            referred.write({
                'referred_by': referrer.id
            })
            
            return {
                'success': True,
                'message': f'Referral bonus awarded! Earned {program.referral_bonus} points.',
                'transaction_id': transaction.id,
                'referrer_points': referrer.available_points,
                'referral_count': referrer.total_referrals
            }
            
        except Exception as e:
            _logger.error(f"Error in process_referral: {e}")
            return {'error': 'An error occurred while processing referral'}
    
    @http.route('/api/loyalty/user-stats', type='json', auth='public', methods=['POST'])
    def get_user_stats(self, **kw):
        """Get user loyalty statistics"""
        try:
            data = request.jsonrequest
            
            if 'user_id' not in data:
                return {'error': 'Missing user_id'}
            
            user_id = data['user_id']
            
            # Get user
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return {'error': 'User not found'}
            
            # Get loyalty program
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            # Calculate level
            level_info = {}
            if program:
                level_info = program.calculate_user_level(user.total_points)
            
            # Get transaction statistics
            transaction_stats = request.env['karmabot.loyalty.transaction'].sudo().get_user_statistics(user.id)
            
            # Get achievements
            user_achievements = request.env['karmabot.user.achievement'].sudo().search([
                ('user_id', '=', user.id)
            ])
            
            achievements = []
            for achievement in user_achievements:
                achievements.append({
                    'name': achievement.achievement_name,
                    'icon': achievement.achievement_icon,
                    'color': achievement.achievement_color,
                    'earned_date': achievement.earned_date.isoformat(),
                    'points_reward': achievement.points_reward
                })
            
            return {
                'success': True,
                'user_stats': {
                    'total_points': user.total_points,
                    'available_points': user.available_points,
                    'spent_points': user.spent_points,
                    'total_scans': user.total_scans,
                    'total_referrals': user.total_referrals,
                    'level': level_info.get('level', 0),
                    'level_name': level_info.get('name', 'Newcomer'),
                    'points_to_next': level_info.get('points_to_next', 0),
                    'next_level_points': level_info.get('next_level_points', 0),
                    'multiplier': level_info.get('multiplier', 1.0),
                    'transaction_stats': transaction_stats,
                    'achievements': achievements
                }
            }
            
        except Exception as e:
            _logger.error(f"Error in get_user_stats: {e}")
            return {'error': 'An error occurred while fetching user stats'}
    
    @http.route('/api/loyalty/spend-points', type='json', auth='public', methods=['POST'])
    def spend_points(self, **kw):
        """Spend user points"""
        try:
            data = request.jsonrequest
            
            # Validate required fields
            required_fields = ['user_id', 'points', 'description']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}
            
            user_id = data['user_id']
            points = data['points']
            description = data['description']
            
            # Get user
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return {'error': 'User not found'}
            
            # Check if user has enough points
            if user.available_points < points:
                return {'error': 'Insufficient points'}
            
            # Get loyalty program
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            if not program:
                return {'error': 'No active loyalty program'}
            
            # Check minimum redemption
            if points < program.min_redeem_points:
                return {'error': f'Minimum redemption is {program.min_redeem_points} points'}
            
            # Create spend transaction
            transaction = request.env['karmabot.loyalty.transaction'].sudo().create_spend_transaction(
                user_id=user.id,
                points=points,
                description=description
            )
            
            # Update user points
            user.action_spend_points(points, description)
            
            return {
                'success': True,
                'message': f'Successfully spent {points} points.',
                'transaction_id': transaction.id,
                'remaining_points': user.available_points
            }
            
        except Exception as e:
            _logger.error(f"Error in spend_points: {e}")
            return {'error': 'An error occurred while spending points'}
    
    @http.route('/api/loyalty/analytics', type='json', auth='public', methods=['POST'])
    def get_loyalty_analytics(self, **kw):
        """Get loyalty program analytics (admin only)"""
        try:
            data = request.jsonrequest
            
            # Validate admin access
            if 'admin_token' not in data:
                return {'error': 'Admin access required'}
            
            # Get loyalty program
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            if not program:
                return {'error': 'No active loyalty program'}
            
            # Get program statistics
            stats = program.get_program_statistics()
            
            return {
                'success': True,
                'analytics': stats
            }
            
        except Exception as e:
            _logger.error(f"Error in get_loyalty_analytics: {e}")
            return {'error': 'An error occurred while fetching analytics'}
