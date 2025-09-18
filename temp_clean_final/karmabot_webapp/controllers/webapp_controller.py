# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging
import jwt
import json

_logger = logging.getLogger(__name__)


class KarmaBotWebAppController(http.Controller):
    """Main WebApp Controller - Landing page and routing"""
    
    @http.route('/karmabot/webapp', type='http', auth='public', website=True)
    def karmabot_webapp(self, user_id=None, **kw):
        """Красивая форма регистрации и личного кабинета"""
        try:
            # Если user_id передан, попробовать найти пользователя
            if user_id:
                user = request.env['karmabot.user'].sudo().search([
                    ('telegram_id', '=', str(user_id))
                ], limit=1)
                
                if user:
                    # Пользователь найден - показать личный кабинет
                    return request.render('karmabot_webapp.user_cabinet', {
                        'user': user,
                        'is_registered': True
                    })
                else:
                    # Пользователь не найден - показать форму регистрации
                    return request.render('karmabot_webapp.registration_form', {
                        'telegram_id': user_id,
                        'is_registration': True
                    })
            else:
                # Нет user_id - показать общую страницу
                return request.render('karmabot_webapp.webapp_landing')
                
        except Exception as e:
            _logger.error(f"Error in karmabot_webapp: {e}")
            return request.render('karmabot_webapp.webapp_landing', {
                'error': 'Произошла ошибка. Попробуйте позже.'
            })
    
    @http.route('/webapp', type='http', auth='public', website=True)
    def webapp_landing(self, sso=None, **kw):
        """WebApp landing page with role-based routing"""
        try:
            # If no SSO token, show login page
            if not sso:
                return request.render('karmabot_webapp.webapp_login')
            
            # Validate SSO token
            user_data = self._validate_sso_token(sso)
            if not user_data:
                return request.render('karmabot_webapp.webapp_login', {
                    'error': 'Invalid or expired token'
                })
            
            # Get user from database
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', user_data['telegram_id'])
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.webapp_login', {
                    'error': 'User not found'
                })
            
            # Create WebApp session
            session = request.env['karmabot.webapp_session'].sudo().create_session(
                user_id=user.id,
                session_type='user_cabinet',
                ip_address=request.httprequest.environ.get('REMOTE_ADDR'),
                user_agent=request.httprequest.environ.get('HTTP_USER_AGENT')
            )
            
            # Route based on user role
            if user.role == 'user':
                return request.redirect(f'/my/profile?sso={sso}')
            elif user.role == 'partner':
                return request.redirect(f'/my/partner?sso={sso}')
            elif user.role == 'admin':
                return request.redirect(f'/web#menu_id=karmabot_admin&sso={sso}')
            elif user.role == 'super_admin':
                return request.redirect(f'/web#menu_id=karmabot_super_admin&sso={sso}')
            else:
                return request.render('karmabot_webapp.webapp_login', {
                    'error': 'Invalid user role'
                })
            
        except Exception as e:
            _logger.error(f"Error in webapp_landing: {e}")
            return request.render('karmabot_webapp.webapp_login', {
                'error': 'An error occurred. Please try again.'
            })
    
    @http.route('/webapp/api/cabinet-url', type='json', auth='public', methods=['POST'])
    def get_cabinet_url(self, **kw):
        """Get cabinet URL based on user role"""
        try:
            data = request.jsonrequest
            
            if 'sso_token' not in data:
                return {'error': 'SSO token required'}
            
            sso_token = data['sso_token']
            
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
            
            # Generate cabinet URL based on role
            base_url = request.httprequest.host_url.rstrip('/')
            
            if user.role == 'user':
                cabinet_url = f"{base_url}/my/profile?sso={sso_token}"
            elif user.role == 'partner':
                cabinet_url = f"{base_url}/my/partner?sso={sso_token}"
            elif user.role == 'admin':
                cabinet_url = f"{base_url}/web#menu_id=karmabot_admin&sso={sso_token}"
            elif user.role == 'super_admin':
                cabinet_url = f"{base_url}/web#menu_id=karmabot_super_admin&sso={sso_token}"
            else:
                return {'error': 'Invalid user role'}
            
            return {
                'success': True,
                'cabinet_url': cabinet_url,
                'user_role': user.role,
                'user_name': user.name
            }
            
        except Exception as e:
            _logger.error(f"Error in get_cabinet_url: {e}")
            return {'error': 'An error occurred while generating cabinet URL'}
    
    @http.route('/webapp/api/user-info', type='json', auth='public', methods=['POST'])
    def get_user_info(self, **kw):
        """Get user information for WebApp"""
        try:
            data = request.jsonrequest
            
            if 'sso_token' not in data:
                return {'error': 'SSO token required'}
            
            sso_token = data['sso_token']
            
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
            
            # Get loyalty program for level calculation
            program = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)
            
            level_info = {}
            if program:
                level_info = program.calculate_user_level(user.total_points)
            
            return {
                'success': True,
                'user_info': {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'name': user.name,
                    'username': user.telegram_username,
                    'role': user.role,
                    'total_points': user.total_points,
                    'available_points': user.available_points,
                    'level': level_info.get('level', 0),
                    'level_name': level_info.get('name', 'Newcomer'),
                    'points_to_next': level_info.get('points_to_next', 0),
                    'total_scans': user.total_scans,
                    'total_referrals': user.total_referrals,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error in get_user_info: {e}")
            return {'error': 'An error occurred while fetching user info'}
    
    @http.route('/webapp/api/heartbeat', type='json', auth='public', methods=['POST'])
    def heartbeat(self, **kw):
        """Update session activity"""
        try:
            data = request.jsonrequest
            
            if 'sso_token' not in data:
                return {'error': 'SSO token required'}
            
            sso_token = data['sso_token']
            
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
            
            # Update session activity
            active_session = request.env['karmabot.webapp_session'].sudo().search([
                ('user_id', '=', user.id),
                ('is_active', '=', True)
            ], limit=1)
            
            if active_session:
                active_session.update_activity()
            
            return {'success': True, 'timestamp': fields.Datetime.now().isoformat()}
            
        except Exception as e:
            _logger.error(f"Error in heartbeat: {e}")
            return {'error': 'An error occurred during heartbeat'}
    
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
    
    @http.route('/karmabot/webapp/register', type='json', auth='public', methods=['POST'])
    def register_user(self, **kw):
        """Регистрация нового пользователя"""
        try:
            data = request.jsonrequest
            
            # Проверить обязательные поля
            if not data.get('telegram_id') or not data.get('full_name'):
                return {'success': False, 'error': 'Не заполнены обязательные поля'}
            
            # Проверить, не зарегистрирован ли уже пользователь
            existing_user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(data['telegram_id']))
            ], limit=1)
            
            if existing_user:
                return {'success': False, 'error': 'Пользователь уже зарегистрирован'}
            
            # Создать нового пользователя
            user_vals = {
                'telegram_id': str(data['telegram_id']),
                'display_name': data['full_name'],
                'telegram_username': data.get('username', ''),
                'phone': data.get('phone', ''),
                'email': data.get('email', ''),
                'city': data.get('city', ''),
                'role': 'user',
                'total_points': 0,
                'available_points': 0,
                'pending_points': 0,
                'is_active': True,
                'is_verified': False,
                'registration_date': fields.Datetime.now(),
                'last_activity': fields.Datetime.now()
            }
            
            new_user = request.env['karmabot.user'].sudo().create(user_vals)
            
            # Создать партнера в Odoo
            partner_vals = {
                'name': data['full_name'],
                'phone': data.get('phone', ''),
                'email': data.get('email', ''),
                'customer_rank': 1,
                'is_company': False,
                'active': True
            }
            
            partner = request.env['res.partner'].sudo().create(partner_vals)
            
            # Связать пользователя с партнером
            new_user.write({'partner_id': partner.id})
            
            return {
                'success': True,
                'message': 'Регистрация успешно завершена',
                'user_id': new_user.id
            }
            
        except Exception as e:
            _logger.error(f"Error in register_user: {e}")
            return {'success': False, 'error': 'Произошла ошибка при регистрации'}
    
    @http.route('/karmabot/webapp/cards', type='http', auth='public', website=True)
    def user_cards(self, user_id=None, **kw):
        """Страница карт пользователя"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            # Получить карты пользователя
            cards = request.env['karmabot.partner.card'].sudo().search([
                ('partner_id', '=', user.partner_id.id)
            ])
            
            return request.render('karmabot_webapp.user_cards', {
                'user': user,
                'cards': cards
            })
            
        except Exception as e:
            _logger.error(f"Error in user_cards: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки карт'})
    
    @http.route('/karmabot/webapp/history', type='http', auth='public', website=True)
    def user_history(self, user_id=None, **kw):
        """Страница истории операций"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            # Получить транзакции пользователя
            transactions = request.env['karmabot.loyalty.transaction'].sudo().search([
                ('user_id', '=', user.id)
            ], order='create_date desc', limit=20)
            
            return request.render('karmabot_webapp.user_history', {
                'user': user,
                'transactions': transactions
            })
            
        except Exception as e:
            _logger.error(f"Error in user_history: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки истории'})
    
    @http.route('/karmabot/webapp/bonuses', type='http', auth='public', website=True)
    def user_bonuses(self, user_id=None, **kw):
        """Страница бонусов и скидок"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            # Получить доступные бонусы
            bonuses = request.env['karmabot.loyalty.program'].sudo().search([
                ('is_active', '=', True)
            ])
            
            return request.render('karmabot_webapp.user_bonuses', {
                'user': user,
                'bonuses': bonuses
            })
            
        except Exception as e:
            _logger.error(f"Error in user_bonuses: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки бонусов'})
    
    @http.route('/karmabot/webapp/settings', type='http', auth='public', website=True)
    def user_settings(self, user_id=None, **kw):
        """Страница настроек пользователя"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            return request.render('karmabot_webapp.user_settings', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in user_settings: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки настроек'})
    
    @http.route('/karmabot/webapp/support', type='http', auth='public', website=True)
    def user_support(self, user_id=None, **kw):
        """Страница поддержки"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            return request.render('karmabot_webapp.user_support', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in user_support: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки поддержки'})
    
    @http.route('/karmabot/webapp/statistics', type='http', auth='public', website=True)
    def user_statistics(self, user_id=None, **kw):
        """Страница статистики пользователя"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            # Получить статистику
            stats = {
                'total_points': user.total_points,
                'available_points': user.available_points,
                'total_scans': user.total_scans,
                'total_referrals': user.total_referrals,
                'registration_date': user.registration_date,
                'last_activity': user.last_activity
            }
            
            return request.render('karmabot_webapp.user_statistics', {
                'user': user,
                'stats': stats
            })
            
        except Exception as e:
            _logger.error(f"Error in user_statistics: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки статистики'})
    
    # === КОНТРОЛЛЕРЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ (USER) ===
    
    @http.route('/karmabot/webapp/points', type='http', auth='public', website=True)
    def user_points(self, user_id=None, **kw):
        """Страница баллов пользователя"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            return request.render('karmabot_webapp.user_points', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in user_points: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки баллов'})
    
    @http.route('/karmabot/webapp/referrals', type='http', auth='public', website=True)
    def user_referrals(self, user_id=None, **kw):
        """Страница рефералов пользователя"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Пользователь не найден'})
            
            return request.render('karmabot_webapp.user_referrals', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in user_referrals: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки рефералов'})
    
    # === КОНТРОЛЛЕРЫ ДЛЯ ПАРТНЕРОВ (PARTNER) ===
    
    @http.route('/karmabot/webapp/partner/cards', type='http', auth='public', website=True)
    def partner_cards(self, user_id=None, **kw):
        """Страница карточек партнера"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'partner':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            # Получить карточки партнера
            cards = request.env['karmabot.partner.card'].sudo().search([
                ('partner_id', '=', user.partner_id.id)
            ])
            
            return request.render('karmabot_webapp.partner_cards', {
                'user': user,
                'cards': cards
            })
            
        except Exception as e:
            _logger.error(f"Error in partner_cards: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки карточек'})
    
    @http.route('/karmabot/webapp/partner/analytics', type='http', auth='public', website=True)
    def partner_analytics(self, user_id=None, **kw):
        """Страница аналитики партнера"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'partner':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.partner_analytics', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in partner_analytics: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки аналитики'})
    
    @http.route('/karmabot/webapp/partner/qr', type='http', auth='public', website=True)
    def partner_qr(self, user_id=None, **kw):
        """Страница QR-кодов партнера"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'partner':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.partner_qr', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in partner_qr: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки QR-кодов'})
    
    @http.route('/karmabot/webapp/partner/clients', type='http', auth='public', website=True)
    def partner_clients(self, user_id=None, **kw):
        """Страница клиентов партнера"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'partner':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.partner_clients', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in partner_clients: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки клиентов'})
    
    # === КОНТРОЛЛЕРЫ ДЛЯ АДМИНОВ (ADMIN) ===
    
    @http.route('/karmabot/webapp/admin/moderation', type='http', auth='public', website=True)
    def admin_moderation(self, user_id=None, **kw):
        """Страница модерации админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role not in ['admin', 'super_admin']:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            # Получить карточки на модерацию
            pending_cards = request.env['karmabot.partner.card'].sudo().search([
                ('status', '=', 'pending')
            ])
            
            return request.render('karmabot_webapp.admin_moderation', {
                'user': user,
                'pending_cards': pending_cards
            })
            
        except Exception as e:
            _logger.error(f"Error in admin_moderation: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки модерации'})
    
    @http.route('/karmabot/webapp/admin/users', type='http', auth='public', website=True)
    def admin_users(self, user_id=None, **kw):
        """Страница управления пользователями админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role not in ['admin', 'super_admin']:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            # Получить всех пользователей
            all_users = request.env['karmabot.user'].sudo().search([])
            
            return request.render('karmabot_webapp.admin_users', {
                'user': user,
                'all_users': all_users
            })
            
        except Exception as e:
            _logger.error(f"Error in admin_users: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки пользователей'})
    
    @http.route('/karmabot/webapp/admin/analytics', type='http', auth='public', website=True)
    def admin_analytics(self, user_id=None, **kw):
        """Страница аналитики админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role not in ['admin', 'super_admin']:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.admin_analytics', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in admin_analytics: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки аналитики'})
    
    @http.route('/karmabot/webapp/admin/notifications', type='http', auth='public', website=True)
    def admin_notifications(self, user_id=None, **kw):
        """Страница уведомлений админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role not in ['admin', 'super_admin']:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.admin_notifications', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in admin_notifications: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки уведомлений'})
    
    # === КОНТРОЛЛЕРЫ ДЛЯ СУПЕР-АДМИНОВ (SUPER_ADMIN) ===
    
    @http.route('/karmabot/webapp/superadmin/settings', type='http', auth='public', website=True)
    def superadmin_settings(self, user_id=None, **kw):
        """Страница системных настроек супер-админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'super_admin':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.superadmin_settings', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in superadmin_settings: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки настроек'})
    
    @http.route('/karmabot/webapp/superadmin/modules', type='http', auth='public', website=True)
    def superadmin_modules(self, user_id=None, **kw):
        """Страница управления модулями супер-админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'super_admin':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.superadmin_modules', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in superadmin_modules: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки модулей'})
    
    @http.route('/karmabot/webapp/superadmin/admins', type='http', auth='public', website=True)
    def superadmin_admins(self, user_id=None, **kw):
        """Страница управления админами супер-админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'super_admin':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            # Получить всех админов
            admins = request.env['karmabot.user'].sudo().search([
                ('role', 'in', ['admin', 'super_admin'])
            ])
            
            return request.render('karmabot_webapp.superadmin_admins', {
                'user': user,
                'admins': admins
            })
            
        except Exception as e:
            _logger.error(f"Error in superadmin_admins: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки админов'})
    
    @http.route('/karmabot/webapp/superadmin/security', type='http', auth='public', website=True)
    def superadmin_security(self, user_id=None, **kw):
        """Страница безопасности супер-админа"""
        try:
            if not user_id:
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Не указан ID пользователя'})
            
            user = request.env['karmabot.user'].sudo().search([
                ('telegram_id', '=', str(user_id))
            ], limit=1)
            
            if not user or user.role != 'super_admin':
                return request.render('karmabot_webapp.user_cabinet', {'error': 'Доступ запрещен'})
            
            return request.render('karmabot_webapp.superadmin_security', {
                'user': user
            })
            
        except Exception as e:
            _logger.error(f"Error in superadmin_security: {e}")
            return request.render('karmabot_webapp.user_cabinet', {'error': 'Ошибка загрузки безопасности'})
