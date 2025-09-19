#!/usr/bin/env python3
"""
API эндпоинты для модерации в WebApp
"""
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
import sys

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.db_adapter import db_v2
from core.settings import settings

logger = logging.getLogger(__name__)

class ModerationAPIHandler(BaseHTTPRequestHandler):
    """Обработчик API запросов для модерации"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/moderation/applications':
            self.handle_get_applications()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/moderation/approve/'):
            app_id = parsed_path.path.split('/')[-1]
            self.handle_approve_application(app_id)
        elif parsed_path.path.startswith('/api/moderation/reject/'):
            app_id = parsed_path.path.split('/')[-1]
            self.handle_reject_application(app_id)
        else:
            self.send_error(404, "Not Found")
    
    def handle_get_applications(self):
        """Получить список заявок на модерацию"""
        try:
            # Получаем заявки партнеров со статусом 'pending'
            applications = db_v2.execute_query("""
                SELECT id, name, phone, email, telegram_user_id, created_at, status
                FROM partner_applications 
                WHERE status = 'pending' 
                ORDER BY created_at ASC 
                LIMIT 50
            """)
            
            # Преобразуем в список словарей
            apps_list = []
            for app in applications:
                apps_list.append({
                    'id': app['id'],
                    'name': app['name'],
                    'phone': app['phone'],
                    'email': app['email'],
                    'telegram_user_id': app['telegram_user_id'],
                    'created_at': app['created_at'].isoformat() if hasattr(app['created_at'], 'isoformat') else str(app['created_at']),
                    'status': app['status']
                })
            
            response = {
                'success': True,
                'applications': apps_list,
                'count': len(apps_list)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def handle_approve_application(self, app_id):
        """Одобрить заявку партнера"""
        try:
            # Обновляем статус заявки
            db_v2.execute_query("""
                UPDATE partner_applications 
                SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (app_id,))
            
            # Получаем данные заявки для уведомления
            app_data = db_v2.execute_query("""
                SELECT name, phone, email, telegram_user_id
                FROM partner_applications 
                WHERE id = ?
            """, (app_id,))
            
            if app_data:
                app = app_data[0]
                # Отправляем уведомление партнеру
                self.send_partner_notification(
                    app['telegram_user_id'],
                    f"✅ Ваша заявка на партнерство одобрена!\n\n"
                    f"Добро пожаловать в команду партнеров KARMA!"
                )
            
            response = {
                'success': True,
                'message': 'Заявка одобрена'
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error approving application {app_id}: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def handle_reject_application(self, app_id):
        """Отклонить заявку партнера"""
        try:
            # Обновляем статус заявки
            db_v2.execute_query("""
                UPDATE partner_applications 
                SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (app_id,))
            
            # Получаем данные заявки для уведомления
            app_data = db_v2.execute_query("""
                SELECT name, phone, email, telegram_user_id
                FROM partner_applications 
                WHERE id = ?
            """, (app_id,))
            
            if app_data:
                app = app_data[0]
                # Отправляем уведомление партнеру
                self.send_partner_notification(
                    app['telegram_user_id'],
                    f"❌ Ваша заявка на партнерство отклонена.\n\n"
                    f"Вы можете подать новую заявку, исправив указанные недочеты."
                )
            
            response = {
                'success': True,
                'message': 'Заявка отклонена'
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error rejecting application {app_id}: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def send_partner_notification(self, telegram_user_id, message):
        """Отправить уведомление партнеру"""
        try:
            # Здесь можно добавить отправку уведомления через Telegram Bot API
            # Пока просто логируем
            logger.info(f"Sending notification to user {telegram_user_id}: {message}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def send_json_response(self, data, status=200):
        """Отправить JSON ответ"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Отключить стандартное логирование HTTP сервера"""
        pass

def start_moderation_api_server(port=8081):
    """Запустить API сервер для модерации"""
    try:
        server = HTTPServer(('0.0.0.0', port), ModerationAPIHandler)
        logger.info(f"Moderation API server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error starting moderation API server: {e}")

if __name__ == "__main__":
    start_moderation_api_server()
