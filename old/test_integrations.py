"""
Тестирование интеграций системы
Проверяет взаимодействие между компонентами
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.getcwd())

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTester:
    """Тестер интеграций"""
    
    def __init__(self):
        self.results = {}
    
    async def test_integrations(self) -> Dict[str, Any]:
        """Тестировать интеграции"""
        logger.info("🔗 Тестируем интеграции...")
        
        # Тестируем интеграции
        await self.test_database_integration()
        await self.test_service_integration()
        await self.test_webapp_integration()
        await self.test_notification_integration()
        await self.test_analytics_integration()
        
        return self.results
    
    async def test_database_integration(self):
        """Тест интеграции с базой данных"""
        logger.info("🗄️ Тестируем интеграцию с БД...")
        
        try:
            from core.database.db_adapter import db_v2
            
            # Тест адаптера БД
            test_user = await db_v2.get_or_create_user(
                telegram_id=888888888,
                username="integration_test",
                first_name="Integration",
                last_name="Test"
            )
            
            # Тест получения данных
            categories = await db_v2.get_categories()
            partners = await db_v2.get_partners_by_status('approved')
            
            success = test_user is not None
            self.results['database_integration'] = {
                'success': success,
                'message': f"Пользователь: {bool(test_user)}, Категорий: {len(categories)}, Партнеров: {len(partners)}",
                'data': {'user_created': bool(test_user), 'categories': len(categories), 'partners': len(partners)}
            }
            
            logger.info(f"✅ Интеграция с БД: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['database_integration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка интеграции с БД: {e}")
    
    async def test_service_integration(self):
        """Тест интеграции сервисов"""
        logger.info("⚙️ Тестируем интеграцию сервисов...")
        
        try:
            from core.services.loyalty_service import loyalty_service
            from core.services.analytics_service import analytics_service
            from core.services.notification_service import notification_service
            
            test_user_id = 888888888
            
            # Тест лояльности
            balance = await loyalty_service.get_user_points_balance(test_user_id)
            
            # Тест аналитики
            user_metrics = await analytics_service.get_user_metrics()
            
            # Тест уведомлений
            notifications = await notification_service.get_user_notifications(test_user_id)
            
            success = all([balance is not None, user_metrics is not None, notifications is not None])
            self.results['service_integration'] = {
                'success': success,
                'message': f"Лояльность: {balance}, Аналитика: {user_metrics.total_users}, Уведомления: {len(notifications)}",
                'data': {'loyalty_balance': balance, 'analytics_users': user_metrics.total_users, 'notifications': len(notifications)}
            }
            
            logger.info(f"✅ Интеграция сервисов: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['service_integration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка интеграции сервисов: {e}")
    
    async def test_webapp_integration(self):
        """Тест интеграции WebApp"""
        logger.info("🌐 Тестируем интеграцию WebApp...")
        
        try:
            from core.services.webapp_integration import WebAppIntegration
            
            webapp = WebAppIntegration()
            
            # Тест создания URL для разных ролей
            user_url = webapp.create_webapp_url(
                telegram_id=888888888,
                role="user",
                webapp_path="/user-cabinet.html"
            )
            
            partner_url = webapp.create_webapp_url(
                telegram_id=888888887,
                role="partner",
                webapp_path="/partner-cabinet.html"
            )
            
            admin_url = webapp.create_webapp_url(
                telegram_id=888888886,
                role="admin",
                webapp_path="/admin-cabinet.html"
            )
            
            success = all([user_url, partner_url, admin_url])
            self.results['webapp_integration'] = {
                'success': success,
                'message': f"URL созданы: Пользователь: {bool(user_url)}, Партнер: {bool(partner_url)}, Админ: {bool(admin_url)}",
                'data': {'user_url': bool(user_url), 'partner_url': bool(partner_url), 'admin_url': bool(admin_url)}
            }
            
            logger.info(f"✅ Интеграция WebApp: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['webapp_integration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка интеграции WebApp: {e}")
    
    async def test_notification_integration(self):
        """Тест интеграции уведомлений"""
        logger.info("📱 Тестируем интеграцию уведомлений...")
        
        try:
            from core.services.notification_service import notification_service, NotificationType, AlertLevel
            
            test_user_id = 888888888
            
            # Тест отправки уведомления
            notification_sent = await notification_service.send_notification(
                user_id=test_user_id,
                title="Тест интеграции",
                message="Тестовое уведомление для проверки интеграции",
                notification_type=NotificationType.INFO
            )
            
            # Тест создания алерта
            alert_id = await notification_service.create_alert(
                title="Тестовый алерт",
                message="Тестовый алерт для проверки интеграции",
                level=AlertLevel.MEDIUM,
                category="integration_test"
            )
            
            # Тест получения уведомлений
            notifications = await notification_service.get_user_notifications(test_user_id)
            
            success = notification_sent and alert_id
            self.results['notification_integration'] = {
                'success': success,
                'message': f"Уведомление: {notification_sent}, Алерт: {bool(alert_id)}, Получено: {len(notifications)}",
                'data': {'notification_sent': notification_sent, 'alert_created': bool(alert_id), 'notifications_count': len(notifications)}
            }
            
            logger.info(f"✅ Интеграция уведомлений: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['notification_integration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка интеграции уведомлений: {e}")
    
    async def test_analytics_integration(self):
        """Тест интеграции аналитики"""
        logger.info("📊 Тестируем интеграцию аналитики...")
        
        try:
            from core.services.analytics_service import analytics_service
            from core.services.performance_service import performance_service
            
            # Тест аналитики
            user_metrics = await analytics_service.get_user_metrics()
            partner_metrics = await analytics_service.get_partner_metrics()
            transaction_metrics = await analytics_service.get_transaction_metrics()
            
            # Тест производительности
            perf_stats = await performance_service.get_performance_stats()
            
            success = all([
                user_metrics is not None,
                partner_metrics is not None,
                transaction_metrics is not None,
                perf_stats is not None
            ])
            
            self.results['analytics_integration'] = {
                'success': success,
                'message': f"Аналитика: Пользователи: {user_metrics.total_users}, Партнеры: {partner_metrics.total_partners}, Транзакции: {transaction_metrics.total_transactions}",
                'data': {
                    'users': user_metrics.total_users,
                    'partners': partner_metrics.total_partners,
                    'transactions': transaction_metrics.total_transactions,
                    'perf_metrics': len(perf_stats.get('metrics', {}))
                }
            }
            
            logger.info(f"✅ Интеграция аналитики: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['analytics_integration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка интеграции аналитики: {e}")


async def main():
    """Главная функция тестирования"""
    tester = IntegrationTester()
    results = await tester.test_integrations()
    
    # Выводим итоговый отчет
    logger.info("📋 ИТОГОВЫЙ ОТЧЕТ ПО ИНТЕГРАЦИЯМ:")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r['success'])
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    logger.info(f"Всего тестов: {total_tests}")
    logger.info(f"Пройдено: {passed_tests}")
    logger.info(f"Провалено: {total_tests - passed_tests}")
    logger.info(f"Успешность: {success_rate:.1f}%")
    
    # Детальные результаты
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        logger.info(f"{status} {test_name}: {result['message']}")
    
    # Сохраняем отчет
    import json
    report = {
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': round(success_rate, 2)
        },
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('integrations_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info("📄 Отчет сохранен в integrations_report.json")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
