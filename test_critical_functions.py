"""
Тестирование критических функций системы
Проверяет основные бизнес-процессы
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


class CriticalFunctionTester:
    """Тестер критических функций"""
    
    def __init__(self):
        self.results = {}
    
    async def test_critical_functions(self) -> Dict[str, Any]:
        """Тестировать критические функции"""
        logger.info("🔍 Тестируем критические функции...")
        
        # Тестируем основные функции
        await self.test_user_registration()
        await self.test_loyalty_points()
        await self.test_partner_registration()
        await self.test_catalog_functionality()
        await self.test_admin_panel()
        await self.test_webapp_cabinets()
        
        return self.results
    
    async def test_user_registration(self):
        """Тест регистрации пользователя"""
        logger.info("👤 Тестируем регистрацию пользователя...")
        
        try:
            from core.database.db_adapter import db_v2
            
            # Тест создания пользователя
            test_user = await db_v2.get_or_create_user(
                telegram_id=999999999,
                username="test_user",
                first_name="Test",
                last_name="User",
                language_code="ru"
            )
            
            success = test_user is not None
            self.results['user_registration'] = {
                'success': success,
                'message': f"Пользователь создан: {test_user.get('is_new_user', False)}",
                'data': test_user
            }
            
            logger.info(f"✅ Регистрация пользователя: {'Успешно' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['user_registration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка регистрации: {e}")
    
    async def test_loyalty_points(self):
        """Тест системы баллов"""
        logger.info("💎 Тестируем систему баллов...")
        
        try:
            from core.services.loyalty_service import loyalty_service
            
            test_user_id = 999999999
            
            # Тест получения баланса
            balance = await loyalty_service.get_user_points_balance(test_user_id)
            
            # Тест истории баллов
            history = await loyalty_service.get_points_history(test_user_id, limit=5)
            
            success = balance is not None
            self.results['loyalty_points'] = {
                'success': success,
                'message': f"Баланс: {balance}, История: {len(history)} записей",
                'data': {'balance': balance, 'history_count': len(history)}
            }
            
            logger.info(f"✅ Система баллов: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['loyalty_points'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка системы баллов: {e}")
    
    async def test_partner_registration(self):
        """Тест регистрации партнера"""
        logger.info("🤝 Тестируем регистрацию партнера...")
        
        try:
            from core.database.db_adapter import db_v2
            from core.database.db_v2 import Partner
            
            # Создаем тестового партнера
            test_partner = Partner(
                id=None,
                tg_user_id=999999998,
                display_name="Test Partner",
                phone="+1234567890",
                email="test@partner.com",
                description="Test partner for testing",
                status="pending",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Тест создания партнера
            created_partner = await db_v2.create_partner(test_partner)
            
            # Тест получения партнеров на модерации
            pending_partners = await db_v2.get_partners_by_status('pending')
            
            success = created_partner is not None
            self.results['partner_registration'] = {
                'success': success,
                'message': f"Партнер создан: {success}, На модерации: {len(pending_partners)}",
                'data': {'created': success, 'pending_count': len(pending_partners)}
            }
            
            logger.info(f"✅ Регистрация партнера: {'Успешно' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['partner_registration'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка регистрации партнера: {e}")
    
    async def test_catalog_functionality(self):
        """Тест функциональности каталога"""
        logger.info("🏪 Тестируем каталог...")
        
        try:
            from core.database.db_adapter import db_v2
            
            # Тест получения категорий
            categories = await db_v2.get_categories()
            
            # Тест получения карт
            cards = await db_v2.get_cards_by_category('restaurants')
            
            success = categories is not None
            self.results['catalog_functionality'] = {
                'success': success,
                'message': f"Категорий: {len(categories)}, Карт в ресторанах: {len(cards)}",
                'data': {'categories_count': len(categories), 'cards_count': len(cards)}
            }
            
            logger.info(f"✅ Каталог: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['catalog_functionality'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка каталога: {e}")
    
    async def test_admin_panel(self):
        """Тест админской панели"""
        logger.info("👑 Тестируем админскую панель...")
        
        try:
            from core.services.user_service import get_user_role
            from core.services.analytics_service import analytics_service
            
            # Тест получения роли
            role = await get_user_role(999999999)
            
            # Тест аналитики
            user_metrics = await analytics_service.get_user_metrics()
            
            success = role is not None
            self.results['admin_panel'] = {
                'success': success,
                'message': f"Роль: {role}, Пользователей: {user_metrics.total_users}",
                'data': {'role': role, 'users_count': user_metrics.total_users}
            }
            
            logger.info(f"✅ Админская панель: {'Работает' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['admin_panel'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка админской панели: {e}")
    
    async def test_webapp_cabinets(self):
        """Тест WebApp кабинетов"""
        logger.info("🌐 Тестируем WebApp кабинеты...")
        
        try:
            from core.services.webapp_integration import WebAppIntegration
            
            webapp = WebAppIntegration()
            
            # Тест создания URL для пользователя
            user_url = webapp.create_webapp_url(
                telegram_id=999999999,
                role="user",
                webapp_path="/user-cabinet.html"
            )
            
            # Тест создания URL для партнера
            partner_url = webapp.create_webapp_url(
                telegram_id=999999998,
                role="partner",
                webapp_path="/partner-cabinet.html"
            )
            
            # Тест создания URL для админа
            admin_url = webapp.create_webapp_url(
                telegram_id=999999997,
                role="admin",
                webapp_path="/admin-cabinet.html"
            )
            
            success = all([user_url, partner_url, admin_url])
            self.results['webapp_cabinets'] = {
                'success': success,
                'message': f"URL созданы: Пользователь: {bool(user_url)}, Партнер: {bool(partner_url)}, Админ: {bool(admin_url)}",
                'data': {'user_url': bool(user_url), 'partner_url': bool(partner_url), 'admin_url': bool(admin_url)}
            }
            
            logger.info(f"✅ WebApp кабинеты: {'Работают' if success else 'Ошибка'}")
            
        except Exception as e:
            self.results['webapp_cabinets'] = {
                'success': False,
                'message': f"Ошибка: {e}",
                'data': None
            }
            logger.error(f"❌ Ошибка WebApp кабинетов: {e}")


async def main():
    """Главная функция тестирования"""
    tester = CriticalFunctionTester()
    results = await tester.test_critical_functions()
    
    # Выводим итоговый отчет
    logger.info("📋 ИТОГОВЫЙ ОТЧЕТ ПО КРИТИЧЕСКИМ ФУНКЦИЯМ:")
    
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
    
    with open('critical_functions_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info("📄 Отчет сохранен в critical_functions_report.json")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
