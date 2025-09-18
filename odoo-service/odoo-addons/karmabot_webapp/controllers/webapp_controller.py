from odoo import http, fields
from odoo.http import request
import json

class WebAppController(http.Controller):
    
    @http.route('/api/bot/user', methods=['POST'], type='http', auth='none', csrf=False)
    def create_user(self, **kwargs):
        """Создание пользователя из бота"""
        try:
            data = request.jsonrequest
            partner = request.env['res.partner'].create({
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'bot_telegram_id': data.get('telegram_id')
            })
            return json.dumps({
                'success': True, 
                'user_id': partner.id,
                'message': 'Пользователь создан успешно'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    @http.route('/api/bot/card', methods=['POST'], type='http', auth='none', csrf=False)
    def create_card(self, **kwargs):
        """Создание карты лояльности"""
        try:
            data = request.jsonrequest
            card = request.env['loyalty.card'].create({
                'partner_id': data.get('user_id'),
                'card_number': data.get('card_number'),
                'balance': 0
            })
            return json.dumps({
                'success': True, 
                'card_id': card.id,
                'card_number': card.card_number,
                'message': 'Карта создана успешно'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    @http.route('/api/bot/transaction', methods=['POST'], type='http', auth='none', csrf=False)
    def create_transaction(self, **kwargs):
        """Создание транзакции"""
        try:
            data = request.jsonrequest
            transaction = request.env['loyalty.transaction'].create({
                'card_id': data.get('card_id'),
                'amount': data.get('amount'),
                'type': data.get('type'),
                'description': data.get('description'),
                'bot_transaction_id': data.get('bot_transaction_id')
            })
            return json.dumps({
                'success': True,
                'transaction_id': transaction.id,
                'new_balance': transaction.card_id.balance,
                'message': 'Транзакция создана успешно'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    @http.route('/api/bot/balance/<int:card_id>', methods=['GET'], type='http', auth='none', csrf=False)
    def get_balance(self, card_id, **kwargs):
        """Получение баланса карты"""
        try:
            card = request.env['loyalty.card'].browse(card_id)
            if not card.exists():
                return json.dumps({
                    'success': False,
                    'error': 'Карта не найдена'
                })
            return json.dumps({
                'success': True,
                'card_id': card.id,
                'balance': card.balance,
                'card_number': card.card_number
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
