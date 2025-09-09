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
    
    async def _handle_error_help(self, message: str, user_role: str, lang: str) -> str:
        """Помогает с решением ошибок"""
        message_lower = message.lower()
        
        if "qr" in message_lower:
            return get_text("support_ai_qr_troubleshoot", lang)
        elif "балл" in message_lower:
            return get_text("support_ai_points_troubleshoot", lang)
        else:
            return get_text("support_ai_general_troubleshoot", lang)
