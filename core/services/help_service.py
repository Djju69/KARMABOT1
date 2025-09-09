"""
Сервис справочной системы для бота
Обеспечивает ролевой доступ к документации
"""

import logging
from typing import Dict, List
from core.security.roles import get_user_role, Role

logger = logging.getLogger(__name__)

class HelpService:
    """Сервис справочной системы"""
    
    def __init__(self):
        # Базовый URL документации (постоянный домен)
        self.base_url = "https://docs.karma-system.com"
        
        # Ссылки для каждой роли
        self.help_links = {
            Role.USER: [
                {
                    "title": "Инструкция для пользователей",
                    "url": f"{self.base_url}/user",
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": f"{self.base_url}/partner/become",
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": f"{self.base_url}/partner/create-place",
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR",
                    "url": f"{self.base_url}/partner/qr-scan",
                    "emoji": "🔹"
                },
                {
                    "title": "Частые вопросы (FAQ)",
                    "url": f"{self.base_url}/faq",
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем",
                    "url": f"{self.base_url}/troubleshooting",
                    "emoji": "🔹"
                },
                {
                    "title": "Связаться с поддержкой",
                    "url": "https://t.me/karma_system_official",
                    "emoji": "🔹"
                }
            ],
            Role.PARTNER: [
                {
                    "title": "Инструкция для пользователей",
                    "url": f"{self.base_url}/user",
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": f"{self.base_url}/partner/become",
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": f"{self.base_url}/partner/create-place",
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR-кодов",
                    "url": f"{self.base_url}/partner/qr-scan",
                    "emoji": "🔹"
                },
                {
                    "title": "Партнёрская аналитика",
                    "url": f"{self.base_url}/partner/analytics",
                    "emoji": "🔹"
                },
                {
                    "title": "Управление заведениями",
                    "url": f"{self.base_url}/partner/manage-places",
                    "emoji": "🔹"
                },
                {
                    "title": "Часто задаваемые вопросы (FAQ)",
                    "url": f"{self.base_url}/faq",
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем и типовые ошибки",
                    "url": f"{self.base_url}/troubleshooting",
                    "emoji": "🔹"
                },
                {
                    "title": "Связаться с поддержкой",
                    "url": "https://t.me/karma_system_official",
                    "emoji": "🔹"
                }
            ],
            Role.ADMIN: [
                {
                    "title": "Инструкция для пользователей",
                    "url": f"{self.base_url}/user",
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": f"{self.base_url}/partner/become",
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": f"{self.base_url}/partner/create-place",
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR-кодов",
                    "url": f"{self.base_url}/partner/qr-scan",
                    "emoji": "🔹"
                },
                {
                    "title": "Партнёрская аналитика",
                    "url": f"{self.base_url}/partner/analytics",
                    "emoji": "🔹"
                },
                {
                    "title": "Управление заведениями",
                    "url": f"{self.base_url}/partner/manage-places",
                    "emoji": "🔹"
                },
                {
                    "title": "Админская панель",
                    "url": f"{self.base_url}/admin/dashboard",
                    "emoji": "🔹"
                },
                {
                    "title": "Модерация заявок",
                    "url": f"{self.base_url}/admin/moderation",
                    "emoji": "🔹"
                },
                {
                    "title": "Управление пользователями",
                    "url": f"{self.base_url}/admin/users",
                    "emoji": "🔹"
                },
                {
                    "title": "Системные настройки",
                    "url": f"{self.base_url}/admin/settings",
                    "emoji": "🔹"
                },
                {
                    "title": "Часто задаваемые вопросы (FAQ)",
                    "url": f"{self.base_url}/faq",
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем и типовые ошибки",
                    "url": f"{self.base_url}/troubleshooting",
                    "emoji": "🔹"
                },
                {
                    "title": "Связаться с поддержкой",
                    "url": "https://t.me/karma_system_official",
                    "emoji": "🔹"
                }
            ],
            Role.SUPER_ADMIN: [
                {
                    "title": "Инструкция для пользователей",
                    "url": f"{self.base_url}/user",
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": f"{self.base_url}/partner/become",
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": f"{self.base_url}/partner/create-place",
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR-кодов",
                    "url": f"{self.base_url}/partner/qr-scan",
                    "emoji": "🔹"
                },
                {
                    "title": "Партнёрская аналитика",
                    "url": f"{self.base_url}/partner/analytics",
                    "emoji": "🔹"
                },
                {
                    "title": "Управление заведениями",
                    "url": f"{self.base_url}/partner/manage-places",
                    "emoji": "🔹"
                },
                {
                    "title": "Админская панель",
                    "url": f"{self.base_url}/admin/dashboard",
                    "emoji": "🔹"
                },
                {
                    "title": "Модерация заявок",
                    "url": f"{self.base_url}/admin/moderation",
                    "emoji": "🔹"
                },
                {
                    "title": "Управление пользователями",
                    "url": f"{self.base_url}/admin/users",
                    "emoji": "🔹"
                },
                {
                    "title": "Системные настройки",
                    "url": f"{self.base_url}/admin/settings",
                    "emoji": "🔹"
                },
                {
                    "title": "Супер-админ панель",
                    "url": f"{self.base_url}/superadmin/dashboard",
                    "emoji": "🔹"
                },
                {
                    "title": "Управление администраторами",
                    "url": f"{self.base_url}/superadmin/admins",
                    "emoji": "🔹"
                },
                {
                    "title": "Системная аналитика",
                    "url": f"{self.base_url}/superadmin/analytics",
                    "emoji": "🔹"
                },
                {
                    "title": "Часто задаваемые вопросы (FAQ)",
                    "url": f"{self.base_url}/faq",
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем и типовые ошибки",
                    "url": f"{self.base_url}/troubleshooting",
                    "emoji": "🔹"
                },
                {
                    "title": "Связаться с поддержкой",
                    "url": "https://t.me/karma_system_official",
                    "emoji": "🔹"
                }
            ]
        }
    
    async def get_help_message(self, user_id: int) -> str:
        """Получить справочное сообщение для пользователя"""
        try:
            # Определяем роль пользователя
            user_role = await get_user_role(user_id)
            
            # Получаем ссылки для роли
            links = self.help_links.get(user_role, self.help_links[Role.USER])
            
            # Формируем сообщение в HTML согласно ТЗ
            message = "✨ Привет! Это <b>Справочный центр Karma System</b> 🧭\n\n"
            
            # Добавляем ссылки в HTML
            for link in links:
                message += f"{link['emoji']} <a href=\"{link['url']}\">{link['title']}</a>\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Error getting help message for user {user_id}: {e}")
            return self._get_fallback_message()
    
    def _get_fallback_message(self) -> str:
        """Резервное сообщение при ошибке"""
        return """📚 <b>Справочный центр</b>

К сожалению, произошла ошибка при загрузке справочной информации.

🔹 <a href="https://t.me/karma_system_official">Связаться с поддержкой</a>

Попробуйте позже или обратитесь в поддержку."""
    
    def get_help_links_for_role(self, role: Role) -> List[Dict]:
        """Получить ссылки для конкретной роли"""
        return self.help_links.get(role, self.help_links[Role.USER])
    
    def update_base_url(self, new_url: str):
        """Обновить базовый URL документации"""
        self.base_url = new_url
        # Обновляем все ссылки
        for role_links in self.help_links.values():
            for link in role_links:
                if link['url'].startswith('https://docs.karma-system.com'):
                    link['url'] = link['url'].replace('https://docs.karma-system.com', new_url)
    
    def test_help_message(self) -> str:
        """Тестовая функция для проверки ссылок"""
        try:
            # Тестируем с ролью USER
            links = self.help_links[Role.USER]
            
            # Формируем тестовое сообщение
            message = "🧪 <b>ТЕСТ ССЫЛОК</b>\n\n"
            message += "Проверяем работу ссылок:\n\n"
            
            # Добавляем первые 3 ссылки для теста
            for i, link in enumerate(links[:3]):
                message += f"{link['emoji']} <a href=\"{link['url']}\">{link['title']}</a>\n"
            
            message += "\n<b>Если ссылки кликабельные - тест пройден!</b>"
            
            return message
            
        except Exception as e:
            return f"❌ Ошибка теста: {e}"
