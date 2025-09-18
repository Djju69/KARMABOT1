"""
ИИ помощник для админов на базе Claude API
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class ClaudeAIService:
    """Сервис для работы с Claude API"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 4000
        
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY not set - AI assistant will be disabled")
    
    def is_available(self) -> bool:
        """Проверить доступность Claude API"""
        return bool(self.api_key)
    
    async def analyze_system_logs(self, hours: int = 24) -> Dict[str, Any]:
        """Анализ системных логов за последние N часов"""
        try:
            if not self.is_available():
                return {"error": "Claude API not available"}
            
            # Получить логи за указанный период
            logs_data = await self._get_recent_logs(hours)
            
            # Создать промпт для анализа
            prompt = f"""
            Проанализируй системные логи KARMABOT1 за последние {hours} часов.
            
            Логи:
            {json.dumps(logs_data, ensure_ascii=False, indent=2)}
            
            Предоставь анализ в следующем формате:
            1. 🔍 Критические ошибки (если есть)
            2. ⚠️ Предупреждения
            3. 📊 Статистика активности
            4. 💡 Рекомендации по улучшению
            
            Отвечай на русском языке, будь конкретным и полезным.
            """
            
            response = await self._call_claude_api(prompt)
            return {
                "analysis": response,
                "period_hours": hours,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing system logs: {e}")
            return {"error": str(e)}
    
    async def analyze_user_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Анализ аналитики пользователей за последние N дней"""
        try:
            if not self.is_available():
                return {"error": "Claude API not available"}
            
            # Получить данные аналитики
            analytics_data = await self._get_user_analytics(days)
            
            # Создать промпт для анализа
            prompt = f"""
            Проанализируй аналитику пользователей KARMABOT1 за последние {days} дней.
            
            Данные:
            {json.dumps(analytics_data, ensure_ascii=False, indent=2)}
            
            Предоставь анализ в следующем формате:
            1. 👥 Активность пользователей
            2. 📈 Тренды роста/снижения
            3. 🎯 Ключевые метрики
            4. 💡 Рекомендации по развитию
            
            Отвечай на русском языке, используй эмодзи для структурирования.
            """
            
            response = await self._call_claude_api(prompt)
            return {
                "analysis": response,
                "period_days": days,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user analytics: {e}")
            return {"error": str(e)}
    
    async def search_database(self, query: str, context: str = "general") -> Dict[str, Any]:
        """Интеллектуальный поиск по базе данных"""
        try:
            if not self.is_available():
                return {"error": "Claude API not available"}
            
            # Получить релевантные данные
            search_data = await self._search_db_data(query, context)
            
            # Создать промпт для поиска
            prompt = f"""
            Помоги найти информацию в базе данных KARMABOT1.
            
            Запрос: {query}
            Контекст: {context}
            
            Найденные данные:
            {json.dumps(search_data, ensure_ascii=False, indent=2)}
            
            Предоставь структурированный ответ:
            1. 🔍 Найденные результаты
            2. 📊 Статистика по запросу
            3. 💡 Дополнительные рекомендации
            
            Отвечай на русском языке, будь точным и полезным.
            """
            
            response = await self._call_claude_api(prompt)
            return {
                "query": query,
                "context": context,
                "results": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching database: {e}")
            return {"error": str(e)}
    
    async def get_system_recommendations(self) -> Dict[str, Any]:
        """Получить рекомендации по улучшению системы"""
        try:
            if not self.is_available():
                return {"error": "Claude API not available"}
            
            # Собрать системную информацию
            system_info = await self._get_system_info()
            
            # Создать промпт для рекомендаций
            prompt = f"""
            Проанализируй состояние системы KARMABOT1 и предоставь рекомендации по улучшению.
            
            Системная информация:
            {json.dumps(system_info, ensure_ascii=False, indent=2)}
            
            Предоставь рекомендации в следующем формате:
            1. 🚀 Приоритетные улучшения
            2. 🔧 Технические рекомендации
            3. 📈 Оптимизация производительности
            4. 🛡️ Безопасность и надежность
            
            Отвечай на русском языке, будь конкретным и практичным.
            """
            
            response = await self._call_claude_api(prompt)
            return {
                "recommendations": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system recommendations: {e}")
            return {"error": str(e)}
    
    async def _call_claude_api(self, prompt: str) -> str:
        """Вызов Claude API"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["content"][0]["text"]
                    else:
                        error_text = await response.text()
                        logger.error(f"Claude API error {response.status}: {error_text}")
                        return f"Ошибка API: {response.status}"
                        
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return f"Ошибка подключения к Claude API: {str(e)}"
    
    async def _get_recent_logs(self, hours: int) -> Dict[str, Any]:
        """Получить логи за последние N часов"""
        try:
            # Здесь должна быть логика получения логов из файлов или БД
            # Пока возвращаем заглушку
            return {
                "total_logs": 150,
                "error_count": 3,
                "warning_count": 12,
                "info_count": 135,
                "recent_errors": [
                    "Database connection timeout",
                    "Rate limit exceeded for user 123456",
                    "Invalid QR code format"
                ],
                "active_users": 45,
                "qr_scans": 78,
                "card_creations": 12
            }
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return {"error": str(e)}
    
    async def _get_user_analytics(self, days: int) -> Dict[str, Any]:
        """Получить аналитику пользователей"""
        try:
            # Здесь должна быть логика получения аналитики из БД
            # Пока возвращаем заглушку
            return {
                "total_users": 1250,
                "active_users": 340,
                "new_users": 45,
                "partner_count": 23,
                "qr_scans_total": 1250,
                "cards_created": 89,
                "points_earned": 15600,
                "points_spent": 8900,
                "daily_stats": [
                    {"date": "2024-01-15", "users": 45, "scans": 78, "points": 1200},
                    {"date": "2024-01-14", "users": 52, "scans": 89, "points": 1350},
                    {"date": "2024-01-13", "users": 38, "scans": 65, "points": 980}
                ]
            }
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": str(e)}
    
    async def _search_db_data(self, query: str, context: str) -> Dict[str, Any]:
        """Поиск данных в базе данных"""
        try:
            # Здесь должна быть логика поиска в БД
            # Пока возвращаем заглушку
            return {
                "query": query,
                "context": context,
                "results_count": 15,
                "matches": [
                    {"type": "user", "id": 123456, "name": "Test User", "relevance": 0.95},
                    {"type": "partner", "id": 789, "name": "Test Partner", "relevance": 0.87},
                    {"type": "card", "id": 456, "name": "Test Card", "relevance": 0.82}
                ],
                "suggestions": [
                    "Попробуйте поиск по email",
                    "Используйте фильтр по дате",
                    "Поиск по категории заведений"
                ]
            }
        except Exception as e:
            logger.error(f"Error searching database: {e}")
            return {"error": str(e)}
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Получить системную информацию"""
        try:
            # Здесь должна быть логика получения системной информации
            # Пока возвращаем заглушку
            return {
                "database_status": "healthy",
                "redis_status": "healthy",
                "odoo_connection": "connected",
                "active_connections": 45,
                "memory_usage": "65%",
                "cpu_usage": "23%",
                "disk_usage": "45%",
                "uptime": "15 days",
                "last_backup": "2024-01-15 02:00:00",
                "feature_flags": {
                    "moderation": True,
                    "qr_webapp": False,
                    "ai_assistant": True
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса
ai_assistant = ClaudeAIService()


# Утилитарные функции для удобства
async def analyze_logs(hours: int = 24) -> Dict[str, Any]:
    """Анализ логов системы"""
    return await ai_assistant.analyze_system_logs(hours)

async def analyze_analytics(days: int = 7) -> Dict[str, Any]:
    """Анализ аналитики пользователей"""
    return await ai_assistant.analyze_user_analytics(days)

async def search_data(query: str, context: str = "general") -> Dict[str, Any]:
    """Поиск данных в базе"""
    return await ai_assistant.search_database(query, context)

async def get_recommendations() -> Dict[str, Any]:
    """Получить рекомендации по системе"""
    return await ai_assistant.get_system_recommendations()
