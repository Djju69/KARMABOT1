"""
Сервис AI-ассистента "Карма"
"""
import logging
from typing import Dict, Any, Optional
from core.services.user_service import get_user_role
from core.i18n import get_text

logger = logging.getLogger(__name__)


class SupportAIService:
    """AI-ассистент для поддержки пользователей"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Загружает базу знаний из ТЗ, кода и i18n"""
        return {
            "faq": {
                "qr_expired": "QR-код истёк. Сгенерируйте новый в разделе 'Мои QR-коды'",
                "qr_repeat": "QR-код уже использован. Каждый код можно применить только один раз",
                "no_balance": "Недостаточно баллов. Накапливайте баллы, совершая покупки",
                "no_rights": "У вас нет прав для этого действия. Обратитесь к администратору"
            },
            "reports": {
                "user": ["покупки", "баллы", "история"],
                "partner": ["заведения", "продажи", "аналитика"],
                "admin": ["все_данные", "партнёры", "города", "платформа"]
            }
        }
    
    async def answer(self, user_id: int, message: str, lang: str = "ru") -> str:
        """
        Обрабатывает сообщение пользователя и возвращает ответ AI
        """
        try:
            # Получаем роль пользователя
            user_role = await get_user_role(user_id)
            
            # Определяем интент сообщения
            intent = self._classify_intent(message)
            
            # Генерируем ответ в зависимости от интента
            if intent == "qa":
                return await self._handle_qa(message, user_role, lang)
            elif intent == "report_make":
                return await self._handle_report_request(message, user_role, lang)
            elif intent == "report_help":
                return await self._handle_report_help(user_role, lang)
            elif intent == "notification_management":
                return await self._handle_notification_management(user_id, message, user_role, lang)
            elif intent == "error_help":
                return await self._handle_error_help(message, user_role, lang)
            else:
                return get_text("support_ai_general_help", lang)
                
        except Exception as e:
            logger.error(f"Error in AI answer: {e}")
            return get_text("support_ai_error", lang)
    
    def _classify_intent(self, message: str) -> str:
        """Классифицирует интент сообщения"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["отчёт", "отчет", "report", "сделай", "сформируй"]):
            return "report_make"
        elif any(word in message_lower for word in ["какие отчёты", "что входит", "отчёты"]):
            return "report_help"
        elif any(word in message_lower for word in ["уведомления", "notifications", "уведомление", "настройки уведомлений"]):
            return "notification_management"
        elif any(word in message_lower for word in ["ошибка", "не работает", "проблема", "не создаётся"]):
            return "error_help"
        else:
            return "qa"
    
    async def _handle_qa(self, message: str, user_role: str, lang: str) -> str:
        """Обрабатывает вопросы и ответы"""
        message_lower = message.lower()
        
        # Проверяем FAQ
        if "qr" in message_lower and "истёк" in message_lower:
            return get_text("support_ai_qr_expired", lang)
        elif "qr" in message_lower and ("повтор" in message_lower or "уже" in message_lower):
            return get_text("support_ai_qr_repeat", lang)
        elif "балл" in message_lower and ("нет" in message_lower or "недостаточно" in message_lower):
            return get_text("support_ai_no_balance", lang)
        elif "права" in message_lower or "доступ" in message_lower:
            return get_text("support_ai_no_rights", lang)
        else:
            return get_text("support_ai_general_help", lang)
    
    async def _handle_report_request(self, message: str, user_role: str, lang: str) -> str:
        """Обрабатывает запросы на создание отчётов"""
        return get_text("support_ai_report_ask_range", lang)
    
    async def _handle_report_help(self, user_role: str, lang: str) -> str:
        """Показывает доступные отчёты по роли"""
        if user_role == "user":
            return get_text("support_ai_reports_user", lang)
        elif user_role == "partner":
            return get_text("support_ai_reports_partner", lang)
        elif user_role in ["admin", "superadmin"]:
            return get_text("support_ai_reports_admin", lang)
        else:
            return get_text("support_ai_reports_user", lang)
    
    async def _handle_notification_management(self, user_id: int, message: str, user_role: str, lang: str) -> str:
        """Обрабатывает управление уведомлениями согласно системному промту"""
        message_lower = message.lower()
        
        # Определяем категории уведомлений по ролям
        categories = self._get_notification_categories(user_role)
        
        if "отключить все" in message_lower or "выключить все" in message_lower:
            return self._format_notification_response(
                "🔇 Отключение всех уведомлений",
                "Вы уверены, что хотите отключить все уведомления? CRITICAL уведомления останутся активными для безопасности.",
                categories,
                user_role,
                lang
            )
        elif "включить все" in message_lower or "включить уведомления" in message_lower:
            return self._format_notification_response(
                "🔔 Включение всех уведомлений",
                "Восстанавливаю стандартные настройки уведомлений для вашей роли.",
                categories,
                user_role,
                lang
            )
        elif "настроить" in message_lower or "категории" in message_lower:
            return self._format_notification_response(
                "⚙️ Настройка категорий уведомлений",
                "Выберите категории, которые хотите настроить:",
                categories,
                user_role,
                lang
            )
        elif "не беспокоить" in message_lower or "тихие часы" in message_lower:
            return self._format_quiet_hours_response(lang)
        else:
            return self._format_notification_response(
                "📊 Управление уведомлениями",
                "Вот ваши текущие настройки уведомлений:",
                categories,
                user_role,
                lang
            )
    
    def _get_notification_categories(self, user_role: str) -> Dict[str, Dict[str, Any]]:
        """Возвращает категории уведомлений для роли"""
        if user_role == "user":
            return {
                "новые_баллы": {"enabled": True, "priority": "NORMAL", "description": "Начисления и списания баллов"},
                "напоминания_о_визитах": {"enabled": True, "priority": "LOW", "description": "Напоминания посетить заведения"},
                "персональные_предложения": {"enabled": True, "priority": "HIGH", "description": "Индивидуальные акции и скидки"},
                "новости_системы": {"enabled": True, "priority": "LOW", "description": "Обновления функций и общие новости"},
                "достижения": {"enabled": True, "priority": "NORMAL", "description": "Новые статусы и награды"}
            }
        elif user_role == "partner":
            return {
                "новые_заказы": {"enabled": True, "priority": "HIGH", "description": "Поступление заказов через систему"},
                "новые_отзывы": {"enabled": True, "priority": "NORMAL", "description": "Отзывы о заведении"},
                "ежедневные_отчеты": {"enabled": False, "priority": "LOW", "description": "Автоматические сводки продаж"},
                "технические_сбои": {"enabled": True, "priority": "CRITICAL", "description": "Проблемы с оборудованием/интеграцией"},
                "маркетинговые_возможности": {"enabled": True, "priority": "LOW", "description": "Рекомендации по продвижению"}
            }
        elif user_role == "admin":
            return {
                "новые_жалобы": {"enabled": True, "priority": "HIGH", "description": "Жалобы пользователей"},
                "требуется_модерация": {"enabled": True, "priority": "NORMAL", "description": "Контент для проверки"},
                "ошибки_в_зоне_ответственности": {"enabled": True, "priority": "HIGH", "description": "Проблемы в курируемых разделах"},
                "аномальная_активность": {"enabled": True, "priority": "CRITICAL", "description": "Подозрительное поведение пользователей"}
            }
        elif user_role == "superadmin":
            return {
                "критические_сбои": {"enabled": True, "priority": "CRITICAL", "description": "Отказы системы"},
                "безопасность": {"enabled": True, "priority": "CRITICAL", "description": "Угрозы и атаки"},
                "производительность": {"enabled": True, "priority": "HIGH", "description": "Проблемы с нагрузкой"},
                "бизнес_аномалии": {"enabled": True, "priority": "HIGH", "description": "Необычные финансовые операции"}
            }
        else:
            return {}
    
    def _format_notification_response(self, title: str, description: str, categories: Dict[str, Dict[str, Any]], user_role: str, lang: str) -> str:
        """Форматирует ответ для управления уведомлениями"""
        response = f"🤖 **{title}**\n\n{description}\n\n"
        
        # Показываем текущий статус категорий
        for category, settings in categories.items():
            status = "✅" if settings["enabled"] else "❌"
            priority = settings["priority"]
            desc = settings["description"]
            response += f"{status} **{category.replace('_', ' ').title()}** ({priority}) - {desc}\n"
        
        response += f"\n🔧 **Доступные действия:**\n"
        response += f"• `/notifications` - главное меню\n"
        response += f"• `отключить все` - отключить все уведомления\n"
        response += f"• `включить все` - включить все уведомления\n"
        response += f"• `настроить категории` - детальная настройка\n"
        response += f"• `не беспокоить` - тихие часы\n"
        
        return response
    
    def _format_quiet_hours_response(self, lang: str) -> str:
        """Форматирует ответ для настройки тихих часов"""
        return """🌙 **Настройка тихих часов**

⏰ **Текущие настройки:**
• Время: 22:00 - 08:00 (по умолчанию)
• Действие: только CRITICAL уведомления

🔧 **Варианты настройки:**
• `1 час` - не беспокоить 1 час
• `день` - не беспокоить до завтра
• `неделя` - не беспокоить неделю
• `настроить время` - индивидуальные часы

💡 **Совет:** CRITICAL уведомления всегда доставляются для безопасности системы."""

    async def _handle_error_help(self, message: str, user_role: str, lang: str) -> str:
        """Помогает с решением ошибок"""
        message_lower = message.lower()
        
        if "qr" in message_lower:
            return get_text("support_ai_qr_troubleshoot", lang)
        elif "балл" in message_lower:
            return get_text("support_ai_points_troubleshoot", lang)
        else:
            return get_text("support_ai_general_troubleshoot", lang)
