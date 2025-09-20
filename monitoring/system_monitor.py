import asyncio
import logging
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
import aiohttp
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    level: str  # 'critical', 'warning', 'info'
    message: str
    action: str
    since: Optional[str] = None
    platform_impact: Optional[str] = None

class HealthChecker:
    """Проверка здоровья отдельных компонентов"""
    
    def __init__(self):
        self.check_interval = 30  # секунд
        self.last_checks = {}
    
    async def check_postgresql(self) -> Dict[str, Any]:
        """Проверка PostgreSQL"""
        try:
            # Здесь должна быть реальная проверка PostgreSQL
            # Для демонстрации возвращаем успешный статус
            return {
                'status': True,
                'response_time_ms': 45,
                'connections': 12,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                'status': False,
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def check_supabase(self) -> Dict[str, Any]:
        """Проверка Supabase"""
        try:
            # Здесь должна быть реальная проверка Supabase
            # Для демонстрации возвращаем успешный статус
            return {
                'status': True,
                'response_time_ms': 78,
                'api_calls_today': 1250,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                'status': False,
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Проверка Redis"""
        try:
            # Здесь должна быть реальная проверка Redis
            return {
                'status': True,
                'memory_usage_mb': 128,
                'connected_clients': 5,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': False,
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }

class SystemMonitor:
    """Мониторинг системы и отправка алертов"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 минут между одинаковыми алертами
        
        # Настройки уведомлений
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', 'admin@example.com')
        
        self.telegram_bot_token = os.getenv('ALERT_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('ALERT_CHAT_ID', '')
        
        # Статистика
        self.stats = {
            'total_checks': 0,
            'critical_alerts': 0,
            'warning_alerts': 0,
            'info_alerts': 0,
            'last_report': None
        }
    
    async def run_monitoring_loop(self):
        """Основной цикл мониторинга"""
        logger.info("🔍 Starting system monitoring loop")
        
        while True:
            try:
                await self._perform_health_checks()
                await self._check_system_metrics()
                await self._generate_recommendations()
                
                # Ежедневный отчет в 9:00
                now = datetime.now()
                if now.hour == 9 and now.minute < 5:
                    await self._send_daily_report()
                
                await asyncio.sleep(30)  # Проверка каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # При ошибке ждем дольше
    
    async def _perform_health_checks(self):
        """Выполнить проверки здоровья системы"""
        self.stats['total_checks'] += 1
        
        # Проверяем PostgreSQL
        pg_status = await self.health_checker.check_postgresql()
        if not pg_status['status']:
            await self._send_critical_alert(Alert(
                level='critical',
                message='PostgreSQL database is down',
                action='Check database connection and restart if necessary',
                platform_impact='All platforms affected'
            ))
        
        # Проверяем Supabase
        sb_status = await self.health_checker.check_supabase()
        if not sb_status['status']:
            await self._send_warning_alert(Alert(
                level='warning',
                message='Supabase service is unavailable',
                action='Check Supabase status and API keys',
                platform_impact='Loyalty system degraded'
            ))
        
        # Проверяем Redis
        redis_status = await self.health_checker.check_redis()
        if not redis_status['status']:
            await self._send_warning_alert(Alert(
                level='warning',
                message='Redis cache is unavailable',
                action='Check Redis connection and restart service',
                platform_impact='Performance degraded'
            ))
    
    async def _check_system_metrics(self):
        """Проверить системные метрики"""
        try:
            # Здесь можно добавить проверки:
            # - Использование памяти
            # - Загрузка CPU
            # - Размер очереди операций
            # - Количество активных соединений
            
            # Пример проверки размера очереди
            queue_size = await self._get_queue_size()
            if queue_size > 1000:
                await self._send_warning_alert(Alert(
                    level='warning',
                    message=f'Operation queue is large: {queue_size} operations',
                    action='Consider increasing processing capacity',
                    platform_impact='Delayed operations'
                ))
            
        except Exception as e:
            logger.error(f"Error checking system metrics: {e}")
    
    async def _get_queue_size(self) -> int:
        """Получить размер очереди операций"""
        try:
            # Здесь должна быть реальная проверка размера очереди
            # Для демонстрации возвращаем случайное число
            import random
            return random.randint(0, 1500)
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0
    
    async def _generate_recommendations(self):
        """Генерировать рекомендации по оптимизации"""
        recommendations = []
        
        try:
            # Проверяем uptime баз данных
            pg_uptime = await self._get_database_uptime('postgresql')
            sb_uptime = await self._get_database_uptime('supabase')
            
            if pg_uptime < 95:
                recommendations.append(f"PostgreSQL uptime is {pg_uptime}%. Consider investigating stability issues.")
            
            if sb_uptime < 95:
                recommendations.append(f"Supabase uptime is {sb_uptime}%. Check service reliability.")
            
            # Проверяем использование кеша
            cache_hit_rate = await self._get_cache_hit_rate()
            if cache_hit_rate < 80:
                recommendations.append(f"Cache hit rate is {cache_hit_rate}%. Consider optimizing cache strategy.")
            
            # Проверяем производительность API
            avg_response_time = await self._get_avg_response_time()
            if avg_response_time > 1000:
                recommendations.append(f"Average API response time is {avg_response_time}ms. Consider performance optimization.")
            
            # Если рекомендаций нет, добавляем положительную
            if not recommendations:
                recommendations.append("System is performing optimally. No immediate actions required.")
            
            # Сохраняем рекомендации для dashboard
            await self._save_recommendations(recommendations)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
    
    async def _get_database_uptime(self, db_name: str) -> float:
        """Получить uptime базы данных"""
        try:
            # Здесь должна быть реальная проверка uptime
            # Для демонстрации возвращаем случайное значение
            import random
            return round(random.uniform(90, 99.9), 1)
        except Exception as e:
            logger.error(f"Error getting {db_name} uptime: {e}")
            return 0.0
    
    async def _get_cache_hit_rate(self) -> float:
        """Получить процент попаданий в кеш"""
        try:
            # Здесь должна быть реальная проверка cache hit rate
            import random
            return round(random.uniform(75, 95), 1)
        except Exception as e:
            logger.error(f"Error getting cache hit rate: {e}")
            return 0.0
    
    async def _get_avg_response_time(self) -> float:
        """Получить среднее время ответа API"""
        try:
            # Здесь должна быть реальная проверка времени ответа
            import random
            return round(random.uniform(100, 1200), 1)
        except Exception as e:
            logger.error(f"Error getting average response time: {e}")
            return 0.0
    
    async def _save_recommendations(self, recommendations: List[str]):
        """Сохранить рекомендации для dashboard"""
        try:
            # Здесь можно сохранить рекомендации в файл или базу данных
            # Для демонстрации просто логируем
            logger.info(f"Generated {len(recommendations)} recommendations")
        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")
    
    async def _send_critical_alert(self, alert: Alert):
        """Отправить критический алерт"""
        alert_key = f"critical_{alert.message}"
        
        if self._should_send_alert(alert_key):
            subject = "🚨 CRITICAL: Multi-Platform System Alert"
            message = f"""
🚨 CRITICAL SYSTEM ALERT

Message: {alert.message}
Action Required: {alert.action}
Platform Impact: {alert.platform_impact or 'Unknown'}
Time: {datetime.utcnow().isoformat()}

Please investigate immediately.

---
Multi-Platform System Monitor
"""
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"🚨 CRITICAL: {alert.message}")
            self.last_alerts[alert_key] = datetime.now()
            self.stats['critical_alerts'] += 1
    
    async def _send_warning_alert(self, alert: Alert):
        """Отправить предупреждение"""
        alert_key = f"warning_{alert.message}"
        
        if self._should_send_alert(alert_key):
            subject = "⚠️ WARNING: Multi-Platform System Alert"
            message = f"""
⚠️ SYSTEM WARNING

Message: {alert.message}
Action Required: {alert.action}
Platform Impact: {alert.platform_impact or 'Unknown'}
Time: {datetime.utcnow().isoformat()}

Please investigate when convenient.

---
Multi-Platform System Monitor
"""
            await self._send_alert_email(subject, message)
            await self._send_telegram_alert(f"⚠️ WARNING: {alert.message}")
            self.last_alerts[alert_key] = datetime.now()
            self.stats['warning_alerts'] += 1
    
    async def _send_info_alert(self, alert: Alert):
        """Отправить информационное уведомление"""
        alert_key = f"info_{alert.message}"
        
        if self._should_send_alert(alert_key):
            subject = "ℹ️ INFO: Multi-Platform System Update"
            message = f"""
ℹ️ SYSTEM INFORMATION

Message: {alert.message}
Action: {alert.action}
Time: {datetime.utcnow().isoformat()}

---
Multi-Platform System Monitor
"""
            await self._send_alert_email(subject, message)
            self.last_alerts[alert_key] = datetime.now()
            self.stats['info_alerts'] += 1
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Проверить, нужно ли отправлять алерт (защита от спама)"""
        if alert_key not in self.last_alerts:
            return True
        
        last_sent = self.last_alerts[alert_key]
        time_since_last = datetime.now() - last_sent
        
        return time_since_last.total_seconds() > self.alert_cooldown
    
    async def _send_alert_email(self, subject: str, message: str):
        """Отправить алерт по email"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.alert_email]):
            logger.warning("Email alert configuration incomplete, skipping email alert")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_telegram_alert(self, message: str):
        """Отправить алерт в Telegram"""
        if not all([self.telegram_bot_token, self.telegram_chat_id]):
            logger.warning("Telegram alert configuration incomplete, skipping Telegram alert")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info("Telegram alert sent successfully")
                    else:
                        logger.error(f"Failed to send Telegram alert: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    async def _send_daily_report(self):
        """Отправить ежедневный отчет"""
        try:
            report_date = datetime.now().strftime("%Y-%m-%d")
            
            subject = f"📊 Daily System Report - {report_date}"
            message = f"""
📊 DAILY SYSTEM REPORT - {report_date}

=== SYSTEM STATISTICS ===
Total Health Checks: {self.stats['total_checks']}
Critical Alerts: {self.stats['critical_alerts']}
Warning Alerts: {self.stats['warning_alerts']}
Info Alerts: {self.stats['info_alerts']}

=== SYSTEM STATUS ===
PostgreSQL: {'✅ Online' if await self._is_postgresql_online() else '❌ Offline'}
Supabase: {'✅ Online' if await self._is_supabase_online() else '❌ Offline'}
Redis: {'✅ Online' if await self._is_redis_online() else '❌ Offline'}

=== PERFORMANCE METRICS ===
Average Response Time: {await self._get_avg_response_time()}ms
Cache Hit Rate: {await self._get_cache_hit_rate()}%
PostgreSQL Uptime: {await self._get_database_uptime('postgresql')}%
Supabase Uptime: {await self._get_database_uptime('supabase')}%

=== RECOMMENDATIONS ===
{await self._get_current_recommendations()}

---
Multi-Platform System Monitor
Generated at: {datetime.utcnow().isoformat()}
"""
            
            await self._send_alert_email(subject, message)
            self.stats['last_report'] = datetime.now()
            logger.info("Daily report sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")
    
    async def _is_postgresql_online(self) -> bool:
        """Проверить, онлайн ли PostgreSQL"""
        try:
            status = await self.health_checker.check_postgresql()
            return status['status']
        except:
            return False
    
    async def _is_supabase_online(self) -> bool:
        """Проверить, онлайн ли Supabase"""
        try:
            status = await self.health_checker.check_supabase()
            return status['status']
        except:
            return False
    
    async def _is_redis_online(self) -> bool:
        """Проверить, онлайн ли Redis"""
        try:
            status = await self.health_checker.check_redis()
            return status['status']
        except:
            return False
    
    async def _get_current_recommendations(self) -> str:
        """Получить текущие рекомендации"""
        try:
            # Здесь должна быть логика получения рекомендаций
            return "• System is performing optimally\n• No immediate actions required\n• Continue monitoring"
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return "• Unable to generate recommendations"
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Получить статистику мониторинга"""
        return {
            'stats': self.stats,
            'last_alerts': {k: v.isoformat() for k, v in self.last_alerts.items()},
            'alert_cooldown': self.alert_cooldown,
            'monitoring_active': True
        }

# Глобальный экземпляр монитора
system_monitor = SystemMonitor()

async def start_monitoring():
    """Запустить мониторинг системы"""
    logger.info("🚀 Starting system monitoring")
    await system_monitor.run_monitoring_loop()

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск мониторинга
    try:
        asyncio.run(start_monitoring())
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise