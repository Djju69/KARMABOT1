import asyncio
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.enhanced_unified_service import enhanced_unified_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """Мониторинг системы и отправка алертов"""
    
    def __init__(self):
        self.alert_email = os.getenv('ALERT_EMAIL', 'admin@example.com')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.telegram_bot_token = os.getenv('ALERT_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('ALERT_CHAT_ID')
        
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 минут между одинаковыми алертами
        
        logger.info("🔍 SystemMonitor initialized")
    
    async def run_monitoring_loop(self):
        """Запустить цикл мониторинга"""
        logger.info("🔍 Starting system monitoring...")
        
        while True:
            try:
                await self.check_system_health()
                await asyncio.sleep(60)  # Проверка каждую минуту
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def check_system_health(self):
        """Проверить здоровье системы и отправить алерты"""
        try:
            dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
            system_status = dashboard_data['system_status']
            alerts = dashboard_data['alerts']
            
            # Проверяем критические алерты
            for alert in alerts:
                if alert['level'] == 'critical':
                    await self.send_critical_alert(alert)
                elif alert['level'] == 'warning':
                    await self.send_warning_alert(alert)
            
            # Проверяем общее состояние системы
            if not system_status['health']['overall']:
                await self.send_system_down_alert(system_status)
            
            # Проверяем очередь операций
            pending_ops = system_status['queue']['total_operations']
            if pending_ops > 200:
                await self.send_queue_overflow_alert(pending_ops)
            
            # Проверяем uptime
            uptime = system_status['uptime']['overall']
            if uptime < 90:
                await self.send_low_uptime_alert(uptime)
            
            # Логируем статус
            mode = system_status['mode']
            logger.info(f"✅ System check: Mode={mode}, Pending={pending_ops}, Uptime={uptime}%")
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            await self.send_monitoring_error_alert(str(e))
    
    async def send_critical_alert(self, alert):
        """Отправить критический алерт"""
        alert_key = f"critical_{alert['message']}"
        
        if self._should_send_alert(alert_key):
            subject = "🚨 CRITICAL: Multi-Platform System Alert"
            message = f"""
🚨 CRITICAL SYSTEM ALERT

Message: {alert['message']}
Since: {alert.get('since', 'Unknown')}
Action Required: {alert.get('action', 'No action specified')}
Platform Impact: {alert.get('platform_impact', 'All platforms may be affected')}

Time: {datetime.now().isoformat()}

🛡️ Fault-Tolerant System is handling the failure automatically, 
but immediate attention is required to restore full functionality.

Current System Mode: Degraded (operating with fallback mechanisms)
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"🚨 CRITICAL: {alert['message']}")
            
            self.last_alerts[alert_key] = datetime.now()
    
    async def send_warning_alert(self, alert):
        """Отправить предупреждающий алерт"""
        alert_key = f"warning_{alert['message']}"
        
        if self._should_send_alert(alert_key):
            subject = "⚠️ WARNING: Multi-Platform System Alert"
            message = f"""
⚠️ SYSTEM WARNING

Message: {alert['message']}
Since: {alert.get('since', 'Unknown')}
Recommended Action: {alert.get('action', 'Monitor situation')}
Platform Impact: {alert.get('platform_impact', 'Limited platform functionality')}

Time: {datetime.now().isoformat()}

The system is operating normally with some limitations.
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"⚠️ WARNING: {alert['message']}")
            
            self.last_alerts[alert_key] = datetime.now()
    
    async def send_system_down_alert(self, system_status):
        """Отправить алерт о падении системы"""
        alert_key = "system_down"
        
        if self._should_send_alert(alert_key):
            mode = system_status['mode']
            
            subject = "🔴 SYSTEM DEGRADED: Multi-Platform Database Services"
            message = f"""
🔴 SYSTEM DEGRADED ALERT

Current Mode: {mode}
PostgreSQL: {"❌ DOWN" if not system_status['health']['postgresql']['status'] else "✅ UP"}
Supabase: {"❌ DOWN" if not system_status['health']['supabase']['status'] else "✅ UP"}

🛡️ FAULT TOLERANCE STATUS:
- System is operating in degraded mode
- Users can still access cached data
- New operations are queued for processing
- All platforms (Telegram, Website, Mobile, Desktop, API) are affected

Platform Status:
🤖 Telegram Bot: Limited functionality
🌐 Website: Limited functionality  
📱 Mobile Apps: Offline mode
🖥️ Desktop Apps: Cache only
🔗 Partner API: Limited

Time: {datetime.now().isoformat()}

🚨 IMMEDIATE ACTION REQUIRED
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"🔴 SYSTEM DEGRADED: Mode={mode}")
            
            self.last_alerts[alert_key] = datetime.now()
    
    async def send_queue_overflow_alert(self, pending_operations):
        """Отправить алерт о переполнении очереди"""
        alert_key = "queue_overflow"
        
        if self._should_send_alert(alert_key):
            subject = "📊 Multi-Platform Queue Overflow Alert"
            message = f"""
📊 OPERATION QUEUE OVERFLOW

Pending Operations: {pending_operations}
Threshold: 200

This indicates that operations from all platforms are not being processed fast enough.

Affected Platforms:
🤖 Telegram: Orders and user operations queued
🌐 Website: Registration and orders delayed
📱 Mobile: Sync operations pending
🔗 API: Partner requests queued

Consider manual sync or database performance optimization.

Time: {datetime.now().isoformat()}
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"📊 Queue Overflow: {pending_operations} pending operations across all platforms")
            
            self.last_alerts[alert_key] = datetime.now()
    
    async def send_low_uptime_alert(self, uptime):
        """Отправить алерт о низком uptime"""
        alert_key = "low_uptime"
        
        if self._should_send_alert(alert_key):
            subject = "📉 Low Multi-Platform System Uptime Alert"
            message = f"""
📉 LOW SYSTEM UPTIME

Current Uptime: {uptime}%
Threshold: 90%

Multi-platform system reliability is below acceptable levels.
All platforms (Telegram, Website, Mobile, Desktop, API) are affected.

Please investigate recent outages and improve stability.

Time: {datetime.now().isoformat()}
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"📉 Low Uptime: {uptime}% - All platforms affected")
            
            self.last_alerts[alert_key] = datetime.now()
    
    async def send_monitoring_error_alert(self, error_message):
        """Отправить алерт об ошибке мониторинга"""
        alert_key = "monitoring_error"
        
        if self._should_send_alert(alert_key):
            subject = "🔧 Multi-Platform Monitoring System Error"
            message = f"""
🔧 MONITORING SYSTEM ERROR

Error: {error_message}

The monitoring system encountered an error while checking multi-platform system health.
This may indicate a serious system issue affecting all platforms.

Time: {datetime.now().isoformat()}
            """
            
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"🔧 Monitoring Error: {error_message[:100]}...")
            
            self.last_alerts[alert_key] = datetime.now()
    
    def _should_send_alert(self, alert_key):
        """Проверить, нужно ли отправлять алерт (cooldown)"""
        if alert_key not in self.last_alerts:
            return True
        
        last_sent = self.last_alerts[alert_key]
        cooldown_expired = datetime.now() - last_sent > timedelta(seconds=self.alert_cooldown)
        
        return cooldown_expired
    
    async def _send_alert_email(self, subject, message):
        """Отправить email алерт"""
        if not all([self.smtp_username, self.smtp_password, self.alert_email]):
            logger.warning("Email credentials not configured, skipping email alert")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_username, self.alert_email, text)
            server.quit()
            
            logger.info(f"📧 Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_telegram_alert(self, message):
        """Отправить Telegram алерт"""
        if not all([self.telegram_bot_token, self.telegram_chat_id]):
            logger.warning("Telegram credentials not configured, skipping Telegram alert")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📱 Telegram alert sent: {message[:50]}...")
            else:
                logger.error(f"Failed to send Telegram alert: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    async def send_recovery_notification(self, component):
        """Отправить уведомление о восстановлении компонента"""
        subject = f"✅ RECOVERY: {component} restored"
        message = f"""
✅ SYSTEM RECOVERY NOTIFICATION

Component: {component}
Status: Restored
Time: {datetime.now().isoformat()}

Multi-platform system functionality has been restored.
All platforms should now operate normally.
        """
        
        await self._send_alert_email(subject, message)
        await self._send_telegram_alert(f"✅ RECOVERY: {component} restored")
        
        logger.info(f"✅ Recovery notification sent for {component}")
    
    async def generate_daily_report(self):
        """Генерировать ежедневный отчет"""
        try:
            dashboard_data = enhanced_unified_db.get_admin_dashboard_data()
            system_status = dashboard_data['system_status']
            platform_stats = dashboard_data.get('platform_stats', {})
            
            subject = "📊 Daily Multi-Platform System Report"
            message = f"""
📊 DAILY SYSTEM REPORT - {datetime.now().strftime('%Y-%m-%d')}

=== SYSTEM OVERVIEW ===
Mode: {system_status['mode']}
Overall Health: {"✅ Healthy" if system_status['health']['overall'] else "❌ Issues"}
Overall Uptime: {system_status['uptime']['overall']}%

=== DATABASE STATUS ===
PostgreSQL: {"✅ Online" if system_status['health']['postgresql']['status'] else "❌ Offline"} ({system_status['uptime']['postgresql']}% uptime)
Supabase: {"✅ Online" if system_status['health']['supabase']['status'] else "❌ Offline"} ({system_status['uptime']['supabase']}% uptime)

=== OPERATION QUEUE ===
Total Pending: {system_status['queue']['total_operations']}
PostgreSQL Queue: {system_status['queue']['by_target_db'].get('postgresql', 0)}
Supabase Queue: {system_status['queue']['by_target_db'].get('supabase', 0)}

=== CACHE STATUS ===
Total Items: {system_status['cache']['total_items']}
Valid Items: {system_status['cache']['valid_items']}
Memory Usage: {system_status['cache']['memory_usage_mb']:.1f} MB

=== PLATFORM STATISTICS ===
Total Platforms: {platform_stats.get('total_platforms', 'N/A')}
Active Users: {platform_stats.get('active_users', 'N/A')}
Daily Orders: {platform_stats.get('daily_orders', 'N/A')}

=== PLATFORM BREAKDOWN ===
🤖 Telegram: {platform_stats.get('telegram', {}).get('users', 'N/A')} users
🌐 Website: {platform_stats.get('website', {}).get('users', 'N/A')} users
📱 Mobile: {platform_stats.get('mobile', {}).get('users', 'N/A')} users
🖥️ Desktop: {platform_stats.get('desktop', {}).get('users', 'N/A')} users
🔗 API: {platform_stats.get('api', {}).get('requests', 'N/A')} requests

Generated: {datetime.now().isoformat()}
            """
            
            await self._send_alert_email(subject, message)
            logger.info("📊 Daily report sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")

class HealthChecker:
    """Проверка здоровья отдельных компонентов"""
    
    def __init__(self):
        self.last_health_status = {}
    
    async def check_database_health(self):
        """Проверить здоровье баз данных"""
        try:
            health_data = enhanced_unified_db.health_check()
            
            pg_status = health_data['health']['postgresql']['status']
            sb_status = health_data['health']['supabase']['status']
            
            # Проверяем изменения статуса
            if 'postgresql' in self.last_health_status:
                if self.last_health_status['postgresql'] != pg_status:
                    if pg_status:
                        logger.info("✅ PostgreSQL recovered")
                    else:
                        logger.warning("❌ PostgreSQL went offline")
            
            if 'supabase' in self.last_health_status:
                if self.last_health_status['supabase'] != sb_status:
                    if sb_status:
                        logger.info("✅ Supabase recovered")
                    else:
                        logger.warning("❌ Supabase went offline")
            
            self.last_health_status['postgresql'] = pg_status
            self.last_health_status['supabase'] = sb_status
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return None
    
    async def check_api_endpoints(self):
        """Проверить доступность API endpoints"""
        endpoints = [
            '/admin/health',
            '/platforms',
            '/telegram/users/',
            '/website/users/',
            '/mobile/users/',
            '/desktop/users/'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                # В реальном проекте здесь был бы HTTP запрос
                # response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                # results[endpoint] = response.status_code == 200
                results[endpoint] = True  # Заглушка
            except Exception:
                results[endpoint] = False
        
        return results

async def main():
    """Основная функция мониторинга"""
    monitor = SystemMonitor()
    health_checker = HealthChecker()
    
    logger.info("🚀 Starting Multi-Platform System Monitor")
    
    # Отправляем стартовое уведомление
    await monitor._send_telegram_alert("🚀 Multi-Platform System Monitor started")
    
    # Запускаем мониторинг
    monitor_task = asyncio.create_task(monitor.run_monitoring_loop())
    
    # Ежедневные отчеты (в реальности используйте cron)
    async def daily_reports():
        while True:
            now = datetime.now()
            # Отправляем отчет в 9:00 каждый день
            if now.hour == 9 and now.minute == 0:
                await monitor.generate_daily_report()
                await asyncio.sleep(60)  # Спим минуту, чтобы не повторять
            await asyncio.sleep(60)
    
    daily_task = asyncio.create_task(daily_reports())
    
    try:
        await asyncio.gather(monitor_task, daily_task)
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Critical monitoring error: {e}")
        await monitor._send_telegram_alert(f"🚨 CRITICAL: Monitoring system crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
