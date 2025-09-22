"""
Система мониторинга для мульти-платформенной системы
Проверка здоровья компонентов, алерты, ежедневные отчеты
"""
import asyncio
import logging
import smtplib
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback для старых версий Python
    MimeText = None
    MimeMultipart = None
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class HealthChecker:
    """Проверка здоровья отдельных компонентов"""
    
    def __init__(self):
        self.check_interval = 60  # секунд
        self.last_checks = {}
    
    async def check_component(self, component_name: str, check_func) -> Dict:
        """Проверить отдельный компонент"""
        try:
            start_time = datetime.utcnow()
            result = await check_func()
            end_time = datetime.utcnow()
            
            duration = (end_time - start_time).total_seconds()
            
            self.last_checks[component_name] = {
                'status': 'healthy' if result.get('healthy', False) else 'unhealthy',
                'timestamp': end_time.isoformat(),
                'duration': duration,
                'details': result
            }
            
            return self.last_checks[component_name]
            
        except Exception as e:
            logger.error(f"Error checking component {component_name}: {e}")
            self.last_checks[component_name] = {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            return self.last_checks[component_name]
    
    async def check_database_connectivity(self) -> Dict:
        """Проверить подключение к базе данных"""
        try:
            # Заглушка для тестирования
            await asyncio.sleep(0.1)  # Имитация проверки
            return {'healthy': True, 'response_time': 0.1}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def check_api_endpoints(self) -> Dict:
        """Проверить доступность API endpoints"""
        try:
            # Заглушка для тестирования
            await asyncio.sleep(0.05)  # Имитация проверки
            return {'healthy': True, 'endpoints_checked': 5}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def check_cache_performance(self) -> Dict:
        """Проверить производительность кэша"""
        try:
            # Заглушка для тестирования
            await asyncio.sleep(0.02)  # Имитация проверки
            return {'healthy': True, 'hit_rate': 0.95}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}

class SystemMonitor:
    """Главный монитор системы"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 минут между одинаковыми алертами
        self.daily_report_sent = False
        self.last_daily_report = None
        
        # Настройки уведомлений
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', ''),
            'to_emails': os.getenv('TO_EMAILS', '').split(',')
        }
        
        self.telegram_config = {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID', '')
        }
        
        logger.info("🔍 SystemMonitor initialized")
    
    async def run_monitoring_loop(self):
        """Запустить основной цикл мониторинга"""
        logger.info("🚀 Starting system monitoring loop")
        
        while True:
            try:
                await self._perform_health_checks()
                await self._check_daily_report()
                await asyncio.sleep(self.health_checker.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Подождать минуту при ошибке
    
    async def _perform_health_checks(self):
        """Выполнить проверки здоровья"""
        try:
            # Проверка компонентов
            components = {
                'database': self.health_checker.check_database_connectivity,
                'api_endpoints': self.health_checker.check_api_endpoints,
                'cache': self.health_checker.check_cache_performance
            }
            
            results = {}
            for component_name, check_func in components.items():
                result = await self.health_checker.check_component(component_name, check_func)
                results[component_name] = result
                
                # Проверить на алерты
                if result['status'] != 'healthy':
                    await self._check_and_send_alert({
                        'component': component_name,
                        'status': result['status'],
                        'message': f"Component {component_name} is {result['status']}",
                        'details': result
                    })
            
            logger.debug(f"Health check results: {results}")
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
    
    async def _check_and_send_alert(self, alert_data: Dict):
        """Проверить и отправить алерт"""
        try:
            alert_key = f"{alert_data['component']}_{alert_data['status']}"
            
            # Проверить cooldown
            if self._should_send_alert(alert_key):
                await self.send_critical_alert(alert_data)
                self.last_alerts[alert_key] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error checking alert: {e}")
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Проверить, нужно ли отправлять алерт"""
        if alert_key not in self.last_alerts:
            return True
        
        last_alert_time = self.last_alerts[alert_key]
        time_since_last = (datetime.utcnow() - last_alert_time).total_seconds()
        
        return time_since_last >= self.alert_cooldown
    
    async def send_critical_alert(self, alert: Dict):
        """Отправить критический алерт"""
        try:
            subject = "🚨 CRITICAL: Multi-Platform System Alert"
            message = f"""
🚨 CRITICAL SYSTEM ALERT

Component: {alert['component']}
Status: {alert['status']}
Message: {alert['message']}
Timestamp: {datetime.utcnow().isoformat()}

Details:
{json.dumps(alert.get('details', {}), indent=2)}

Please check the system immediately.

---
Multi-Platform System Monitor
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"🚨 CRITICAL: {alert['message']}")
            
            logger.warning(f"Critical alert sent: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending critical alert: {e}")
    
    async def send_warning_alert(self, alert: Dict):
        """Отправить предупреждение"""
        try:
            subject = "⚠️ WARNING: Multi-Platform System Alert"
            message = f"""
⚠️ SYSTEM WARNING

Component: {alert['component']}
Status: {alert['status']}
Message: {alert['message']}
Timestamp: {datetime.utcnow().isoformat()}

Details:
{json.dumps(alert.get('details', {}), indent=2)}

Please monitor the system.

---
Multi-Platform System Monitor
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"⚠️ WARNING: {alert['message']}")
            
            logger.info(f"Warning alert sent: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending warning alert: {e}")
    
    async def _send_alert_email(self, subject: str, message: str):
        """Отправить алерт по email"""
        try:
            if not all([self.email_config['username'], self.email_config['password'], self.email_config['from_email']]):
                logger.warning("Email configuration incomplete, skipping email alert")
                return
            
            if MimeMultipart is None or MimeText is None:
                logger.warning("Email modules not available, skipping email alert")
                return
            
            msg = MimeMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['to_emails'])
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['from_email'], self.email_config['to_emails'], text)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def _send_telegram_alert(self, message: str):
        """Отправить алерт в Telegram"""
        try:
            if not all([self.telegram_config['bot_token'], self.telegram_config['chat_id']]):
                logger.warning("Telegram configuration incomplete, skipping Telegram alert")
                return
            
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            data = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info("Telegram alert sent successfully")
                    else:
                        logger.error(f"Telegram alert failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
    
    async def _check_daily_report(self):
        """Проверить необходимость ежедневного отчета"""
        try:
            now = datetime.utcnow()
            
            # Проверить, нужно ли отправить ежедневный отчет
            if self.last_daily_report:
                last_report_date = datetime.fromisoformat(self.last_daily_report)
                if (now - last_report_date).days < 1:
                    return
            
            # Отправить ежедневный отчет в 9:00
            if now.hour == 9 and now.minute < 5:
                await self.send_daily_report()
                self.last_daily_report = now.isoformat()
                self.daily_report_sent = True
            
        except Exception as e:
            logger.error(f"Error checking daily report: {e}")
    
    async def send_daily_report(self):
        """Отправить ежедневный отчет"""
        try:
            # Получить статистику системы
            from database.fault_tolerant_service import fault_tolerant_db
            system_status = fault_tolerant_db.get_system_status()
            
            subject = "📊 Daily Report: Multi-Platform System"
            message = f"""
📊 DAILY SYSTEM REPORT
{datetime.utcnow().strftime('%Y-%m-%d')}

=== SYSTEM STATUS ===
Mode: {system_status['mode']}
Overall Health: {'✅ Healthy' if system_status['health']['overall'] else '❌ Issues'}

=== DATABASE STATUS ===
PostgreSQL: {'✅ Online' if system_status['health']['postgresql']['status'] else '❌ Offline'}
Supabase: {'✅ Online' if system_status['health']['supabase']['status'] else '❌ Offline'}

=== UPTIME STATISTICS ===
PostgreSQL Uptime: {system_status['uptime']['postgresql']}%
Supabase Uptime: {system_status['uptime']['supabase']}%
Overall Uptime: {system_status['uptime']['overall']}%

=== OPERATIONS ===
Total Operations: {system_status['operations']['total_operations']}
Successful: {system_status['operations']['successful_operations']}
Failed: {system_status['operations']['failed_operations']}
Cached: {system_status['operations']['cached_operations']}
Queued: {system_status['operations']['queued_operations']}

=== QUEUE STATUS ===
Total Queued Operations: {system_status['queue']['total_operations']}
Critical Priority: {system_status['queue']['by_priority'].get(4, 0)}
High Priority: {system_status['queue']['by_priority'].get(3, 0)}

=== CACHE STATUS ===
Total Items: {system_status['cache']['total_items']}
Valid Items: {system_status['cache']['valid_items']}
Expired Items: {system_status['cache']['expired_items']}
Memory Usage: {system_status['cache']['memory_usage_mb']:.2f} MB

=== RECOMMENDATIONS ===
"""
            
            # Добавить рекомендации
            if system_status['mode'] == 'CACHE_ONLY':
                message += "⚠️ System running in cache-only mode. Consider restoring database connectivity.\n"
            
            if system_status['queue']['total_operations'] > 50:
                message += "⚠️ High number of queued operations. Consider running forced sync.\n"
            
            if system_status['cache']['expired_items'] > system_status['cache']['valid_items']:
                message += "⚠️ High number of expired cache items. Consider cache cleanup.\n"
            
            if not any([system_status['mode'] == 'CACHE_ONLY', 
                       system_status['queue']['total_operations'] > 50,
                       system_status['cache']['expired_items'] > system_status['cache']['valid_items']]):
                message += "✅ System operating optimally.\n"
            
            message += "\n---\nMulti-Platform System Monitor"
            
            await self._send_alert_email(subject, message)
            
            # Краткий отчет в Telegram
            telegram_message = f"""
📊 Daily Report - {datetime.utcnow().strftime('%Y-%m-%d')}

🟢 System Mode: {system_status['mode']}
📊 Operations: {system_status['operations']['successful_operations']}/{system_status['operations']['total_operations']}
📋 Queue: {system_status['queue']['total_operations']} operations
💾 Cache: {system_status['cache']['valid_items']} items
            """
            
            await self._send_telegram_alert(telegram_message)
            
            logger.info("Daily report sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
    
    def get_monitoring_status(self) -> Dict:
        """Получить статус мониторинга"""
        return {
            'monitor_active': True,
            'last_checks': self.health_checker.last_checks,
            'last_alerts': {k: v.isoformat() for k, v in self.last_alerts.items()},
            'daily_report_sent': self.daily_report_sent,
            'last_daily_report': self.last_daily_report,
            'email_configured': bool(self.email_config['username'] and self.email_config['password']),
            'telegram_configured': bool(self.telegram_config['bot_token'] and self.telegram_config['chat_id'])
        }
