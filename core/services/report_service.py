"""
Сервис генерации отчётов для AI-ассистента
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from core.services.user_service import get_user_role
from core.database.db_v2 import DatabaseServiceV2

logger = logging.getLogger(__name__)


class ReportService:
    """Сервис для генерации отчётов по ролям"""
    
    def __init__(self):
        self.db = DatabaseServiceV2()
    
    async def make_report(self, user_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создаёт отчёт в зависимости от роли пользователя
        """
        try:
            user_role = await get_user_role(user_id)
            
            # Определяем период
            period = self._parse_period(params.get("period", "неделя"))
            
            # Определяем скоуп по роли
            scope = await self._resolve_scope(user_role, user_id, params)
            
            # Получаем данные
            data = await self._fetch_data(scope, period, user_role, user_id)
            
            # Генерируем отчёт
            report = self._generate_report(data, user_role, period)
            
            return {
                "success": True,
                "report": report,
                "scope": scope,
                "period": period
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_period(self, period_str: str) -> Dict[str, datetime]:
        """Парсит период из строки"""
        now = datetime.now()
        period_lower = period_str.lower()
        
        if "вчера" in period_lower or "yesterday" in period_lower:
            start = now - timedelta(days=1)
            end = now
        elif "сегодня" in period_lower or "today" in period_lower:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif "неделя" in period_lower or "week" in period_lower:
            start = now - timedelta(days=7)
            end = now
        elif "месяц" in period_lower or "month" in period_lower:
            start = now - timedelta(days=30)
            end = now
        else:
            # По умолчанию - неделя
            start = now - timedelta(days=7)
            end = now
        
        return {"start": start, "end": end}
    
    async def _resolve_scope(self, user_role: str, user_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Определяет скоуп данных по роли"""
        scope = {"user_id": user_id, "role": user_role}
        
        if user_role == "user":
            scope["type"] = "user_data"
        elif user_role == "partner":
            # Получаем ID партнёра
            partner_data = self.db.execute_query(
                "SELECT id FROM partners WHERE user_telegram_id = ?",
                (user_id,)
            )
            if partner_data:
                scope["partner_id"] = partner_data[0]["id"]
                scope["type"] = "partner_data"
        elif user_role in ["admin", "superadmin"]:
            scope["type"] = "admin_data"
            if "partner_id" in params:
                scope["partner_id"] = params["partner_id"]
            if "city" in params:
                scope["city"] = params["city"]
        
        return scope
    
    async def _fetch_data(self, scope: Dict[str, Any], period: Dict[str, datetime], 
                         user_role: str, user_id: int) -> Dict[str, Any]:
        """Получает данные из БД"""
        data = {}
        
        if scope["type"] == "user_data":
            # Данные пользователя
            data["purchases"] = self._get_user_purchases(user_id, period)
            data["points"] = self._get_user_points(user_id, period)
            
        elif scope["type"] == "partner_data":
            # Данные партнёра
            partner_id = scope["partner_id"]
            data["sales"] = self._get_partner_sales(partner_id, period)
            data["places"] = self._get_partner_places(partner_id)
            
        elif scope["type"] == "admin_data":
            # Админские данные
            data["all_sales"] = self._get_all_sales(period)
            data["partners"] = self._get_partners_stats(period)
            data["cities"] = self._get_cities_stats(period)
        
        return data
    
    def _get_user_purchases(self, user_id: int, period: Dict[str, datetime]) -> List[Dict]:
        """Получает покупки пользователя"""
        query = """
        SELECT ps.*, pp.name as place_name, pp.address
        FROM partner_sales ps
        JOIN partner_places pp ON ps.place_id = pp.id
        WHERE ps.user_telegram_id = ? 
        AND ps.created_at >= ? AND ps.created_at <= ?
        ORDER BY ps.created_at DESC
        """
        return self.db.execute_query(query, (user_id, period["start"], period["end"]))
    
    def _get_user_points(self, user_id: int, period: Dict[str, datetime]) -> List[Dict]:
        """Получает историю баллов пользователя"""
        query = """
        SELECT * FROM points_log 
        WHERE user_telegram_id = ? 
        AND created_at >= ? AND created_at <= ?
        ORDER BY created_at DESC
        """
        return self.db.execute_query(query, (user_id, period["start"], period["end"]))
    
    def _get_partner_sales(self, partner_id: int, period: Dict[str, datetime]) -> List[Dict]:
        """Получает продажи партнёра"""
        query = """
        SELECT ps.*, pp.name as place_name, pp.address
        FROM partner_sales ps
        JOIN partner_places pp ON ps.place_id = pp.id
        WHERE ps.partner_id = ? 
        AND ps.created_at >= ? AND ps.created_at <= ?
        ORDER BY ps.created_at DESC
        """
        return self.db.execute_query(query, (partner_id, period["start"], period["end"]))
    
    def _get_partner_places(self, partner_id: int) -> List[Dict]:
        """Получает заведения партнёра"""
        query = "SELECT * FROM partner_places WHERE partner_id = ?"
        return self.db.execute_query(query, (partner_id,))
    
    def _get_all_sales(self, period: Dict[str, datetime]) -> List[Dict]:
        """Получает все продажи (для админов)"""
        query = """
        SELECT ps.*, pp.name as place_name, pp.address, p.name as partner_name
        FROM partner_sales ps
        JOIN partner_places pp ON ps.place_id = pp.id
        JOIN partners p ON ps.partner_id = p.id
        WHERE ps.created_at >= ? AND ps.created_at <= ?
        ORDER BY ps.created_at DESC
        """
        return self.db.execute_query(query, (period["start"], period["end"]))
    
    def _get_partners_stats(self, period: Dict[str, datetime]) -> List[Dict]:
        """Получает статистику по партнёрам"""
        query = """
        SELECT 
            p.id, p.name,
            COUNT(ps.id) as sales_count,
            SUM(ps.amount_gross) as total_gross,
            SUM(ps.amount_partner_due) as total_due
        FROM partners p
        LEFT JOIN partner_sales ps ON p.id = ps.partner_id 
            AND ps.created_at >= ? AND ps.created_at <= ?
        GROUP BY p.id, p.name
        ORDER BY total_gross DESC
        """
        return self.db.execute_query(query, (period["start"], period["end"]))
    
    def _get_cities_stats(self, period: Dict[str, datetime]) -> List[Dict]:
        """Получает статистику по городам"""
        query = """
        SELECT 
            pp.city,
            COUNT(ps.id) as sales_count,
            SUM(ps.amount_gross) as total_gross
        FROM partner_places pp
        LEFT JOIN partner_sales ps ON pp.id = ps.place_id 
            AND ps.created_at >= ? AND ps.created_at <= ?
        GROUP BY pp.city
        ORDER BY total_gross DESC
        """
        return self.db.execute_query(query, (period["start"], period["end"]))
    
    def _generate_report(self, data: Dict[str, Any], user_role: str, period: Dict[str, datetime]) -> str:
        """Генерирует текстовый отчёт"""
        report_lines = []
        
        if user_role == "user":
            report_lines.append("👤 **Ваш личный отчёт**")
            report_lines.append(f"📅 Период: {period['start'].strftime('%d.%m.%Y')} - {period['end'].strftime('%d.%m.%Y')}")
            
            purchases = data.get("purchases", [])
            points = data.get("points", [])
            
            report_lines.append(f"🛒 Покупок: {len(purchases)}")
            if purchases:
                total_spent = sum(p.get("amount_gross", 0) for p in purchases)
                report_lines.append(f"💰 Потрачено: {total_spent:.2f} ₽")
            
            if points:
                earned = sum(p.get("points_earned", 0) for p in points if p.get("points_earned", 0) > 0)
                spent = sum(abs(p.get("points_earned", 0)) for p in points if p.get("points_earned", 0) < 0)
                report_lines.append(f"⭐ Заработано баллов: {earned}")
                report_lines.append(f"💸 Потрачено баллов: {spent}")
        
        elif user_role == "partner":
            report_lines.append("🤝 **Отчёт партнёра**")
            report_lines.append(f"📅 Период: {period['start'].strftime('%d.%m.%Y')} - {period['end'].strftime('%d.%m.%Y')}")
            
            sales = data.get("sales", [])
            places = data.get("places", [])
            
            report_lines.append(f"🏪 Заведений: {len(places)}")
            report_lines.append(f"🛒 Продаж: {len(sales)}")
            
            if sales:
                total_gross = sum(s.get("amount_gross", 0) for s in sales)
                total_due = sum(s.get("amount_partner_due", 0) for s in sales)
                report_lines.append(f"💰 Общая выручка: {total_gross:.2f} ₽")
                report_lines.append(f"💵 К доплате: {total_due:.2f} ₽")
        
        elif user_role in ["admin", "superadmin"]:
            report_lines.append("🛡️ **Админский отчёт**")
            report_lines.append(f"📅 Период: {period['start'].strftime('%d.%m.%Y')} - {period['end'].strftime('%d.%m.%Y')}")
            
            all_sales = data.get("all_sales", [])
            partners = data.get("partners", [])
            cities = data.get("cities", [])
            
            report_lines.append(f"🛒 Всего продаж: {len(all_sales)}")
            if all_sales:
                total_gross = sum(s.get("amount_gross", 0) for s in all_sales)
                report_lines.append(f"💰 Общая выручка: {total_gross:.2f} ₽")
            
            report_lines.append(f"🤝 Партнёров: {len(partners)}")
            report_lines.append(f"🏙️ Городов: {len(cities)}")
        
        return "\n".join(report_lines)
