"""
Сервис справочной системы для бота
Обеспечивает ролевой доступ к документации и формирует полное сообщение /help
"""

import logging
import os
from typing import Dict, List
from core.security.roles import get_user_role, Role

logger = logging.getLogger(__name__)

class HelpService:
    """Сервис справочной системы"""
    
    def __init__(self):
        # Корневой домен для абсолютных ссылок на статику Railway
        railway_host = os.getenv("RAILWAY_STATIC_URL", "").strip()
        if railway_host and not railway_host.startswith("http"):
            railway_host = f"https://{railway_host}"
        self.web_root = railway_host or ""

        # Быстрые ссылки (внутренние статические страницы)
        def sdoc(name: str) -> str:
            return f"{self.web_root}/static/docs/{name}" if self.web_root else f"/static/docs/{name}"

        # Ссылки для каждой роли (используются в тестах/вспомогательных сценариях)
        self.help_links = {
            Role.USER: [
                {
                    "title": "Инструкция для пользователей",
                    "url": sdoc("help_user.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Частые вопросы (FAQ)",
                    "url": sdoc("help_faq.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем",
                    "url": sdoc("help_troubleshooting.html"),
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
                    "url": sdoc("help_user.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR-кодов",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Партнёрская аналитика",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Управление заведениями",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Часто задаваемые вопросы (FAQ)",
                    "url": sdoc("help_faq.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем и типовые ошибки",
                    "url": sdoc("help_troubleshooting.html"),
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
                    "url": sdoc("help_user.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR-кодов",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Партнёрская аналитика",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Управление заведениями",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Админская панель",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Модерация заявок",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Управление пользователями",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Системные настройки",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Часто задаваемые вопросы (FAQ)",
                    "url": sdoc("help_faq.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем и типовые ошибки",
                    "url": sdoc("help_troubleshooting.html"),
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
                    "url": sdoc("help_user.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Как стать партнёром",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Создание заведений",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Сканирование QR-кодов",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Партнёрская аналитика",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Управление заведениями",
                    "url": sdoc("help_partner.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Админская панель",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Модерация заявок",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Управление пользователями",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Системные настройки",
                    "url": sdoc("help_admin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Супер-админ панель",
                    "url": sdoc("help_superadmin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Управление администраторами",
                    "url": sdoc("help_superadmin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Системная аналитика",
                    "url": sdoc("help_superadmin.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Часто задаваемые вопросы (FAQ)",
                    "url": sdoc("help_faq.html"),
                    "emoji": "🔹"
                },
                {
                    "title": "Решение проблем и типовые ошибки",
                    "url": sdoc("help_troubleshooting.html"),
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
            # Определяем роль пользователя (нормализуем к строке)
            user_role = await get_user_role(user_id)
            role_name = getattr(user_role, 'name', str(user_role)).lower()
            
            # Утилита статических ссылок
            def sdoc(name: str) -> str:
                return f"{self.web_root}/static/docs/{name}" if self.web_root else f"/static/docs/{name}"

            # Формируем сообщение в зависимости от роли пользователя: полноценные разделы
            if role_name == 'user':
                message = (
                    "✨ Привет! Это <b>Справочный центр Karma System</b> 🧭\n\n"
                    "<b>🆘 Быстрая помощь</b>\n"
                    "• /start — главное меню\n"
                    "• /help — справка и инструкции\n"
                    "• /webapp — открыть WebApp\n\n"
                    "<b>🔗 Полезные ссылки</b>\n"
                    f"• 📄 <a href=\"{sdoc('policy.html')}\">Политика конфиденциальности</a>\n"
                    f"• ❓ <a href=\"{sdoc('help_faq.html')}\">FAQ</a>\n"
                    f"• 🛠️ <a href=\"{sdoc('help_troubleshooting.html')}\">Решение проблем</a>\n\n"
                    "<b>📖 Инструкции</b>\n"
                    f"• 👤 <a href=\"{sdoc('help_user.html')}\">Инструкция для пользователей</a>\n\n"
                    "<b>📞 Контакты поддержки</b>\n"
                    "• Telegram: <a href=\"https://t.me/karma_system_official\">@karma_system_official</a>\n\n"
                    "<b>🌐 Смена языка</b>\nИспользуйте меню выбора языка в настройках бота.\n\n"
                    "<i>Мы рядом, если что — пиши. Приятного пользования! ✨</i>"
                )
            
            elif role_name == 'partner':
                message = (
                    "✨ Привет! Это <b>Справочный центр Karma System</b> 🧭\n\n"
                    "<b>🆘 Быстрая помощь</b>\n"
                    "• /start — главное меню\n"
                    "• /help — справка и инструкции\n"
                    "• /webapp — открыть WebApp\n\n"
                    "<b>🔗 Полезные ссылки</b>\n"
                    f"• 📄 <a href=\"{sdoc('policy.html')}\">Политика конфиденциальности</a>\n"
                    f"• ❓ <a href=\"{sdoc('help_faq.html')}\">FAQ</a>\n"
                    f"• 🛠️ <a href=\"{sdoc('help_troubleshooting.html')}\">Решение проблем</a>\n\n"
                    "<b>📖 Инструкции</b>\n"
                    f"• 👤 <a href=\"{sdoc('help_user.html')}\">Для пользователей</a>\n"
                    f"• 🤝 <a href=\"{sdoc('help_partner.html')}\">Как стать партнёром и управление заведениями</a>\n\n"
                    "<b>📞 Контакты поддержки</b>\n"
                    "• Telegram: <a href=\"https://t.me/karma_system_official\">@karma_system_official</a>\n\n"
                    "<b>🌐 Смена языка</b>\nИспользуйте меню выбора языка в настройках бота.\n\n"
                    "<i>Мы рядом, если что — пиши. Приятного пользования! ✨</i>"
                )
            
            elif role_name == 'admin':
                message = (
                    "✨ Привет! Это <b>Справочный центр Karma System</b> 🧭\n\n"
                    "<b>🆘 Быстрая помощь</b>\n"
                    "• /start — главное меню\n"
                    "• /help — справка и инструкции\n"
                    "• /webapp — открыть WebApp\n\n"
                    "<b>🔗 Полезные ссылки</b>\n"
                    f"• 📄 <a href=\"{sdoc('policy.html')}\">Политика конфиденциальности</a>\n"
                    f"• ❓ <a href=\"{sdoc('help_faq.html')}\">FAQ</a>\n"
                    f"• 🛠️ <a href=\"{sdoc('help_troubleshooting.html')}\">Решение проблем</a>\n\n"
                    "<b>📖 Инструкции</b>\n"
                    f"• 👤 <a href=\"{sdoc('help_user.html')}\">Для пользователей</a>\n"
                    f"• 🤝 <a href=\"{sdoc('help_partner.html')}\">Для партнёров</a>\n"
                    f"• 🛡️ <a href=\"{sdoc('help_admin.html')}\">Админская панель и операции</a>\n\n"
                    "<b>📞 Контакты поддержки</b>\n"
                    "• Telegram: <a href=\"https://t.me/karma_system_official\">@karma_system_official</a>\n\n"
                    "<b>🌐 Смена языка</b>\nИспользуйте меню выбора языка в настройках бота.\n\n"
                    "<i>Мы рядом, если что — пиши. Приятного пользования! ✨</i>"
                )
            
            else:  # super_admin
                message = (
                    "✨ Привет! Это <b>Справочный центр Karma System</b> 🧭\n\n"
                    "<b>🆘 Быстрая помощь</b>\n"
                    "• /start — главное меню\n"
                    "• /help — справка и инструкции\n"
                    "• /webapp — открыть WebApp\n\n"
                    "<b>🔗 Полезные ссылки</b>\n"
                    f"• 📄 <a href=\"{sdoc('policy.html')}\">Политика конфиденциальности</a>\n"
                    f"• ❓ <a href=\"{sdoc('help_faq.html')}\">FAQ</a>\n"
                    f"• 🛠️ <a href=\"{sdoc('help_troubleshooting.html')}\">Решение проблем</a>\n\n"
                    "<b>📖 Инструкции</b>\n"
                    f"• 👤 <a href=\"{sdoc('help_user.html')}\">Для пользователей</a>\n"
                    f"• 🤝 <a href=\"{sdoc('help_partner.html')}\">Для партнёров</a>\n"
                    f"• 🛡️ <a href=\"{sdoc('help_admin.html')}\">Админская панель и операции</a>\n"
                    f"• 👑 <a href=\"{sdoc('help_superadmin.html')}\">Супер-админ панель</a>\n\n"
                    "<b>📞 Контакты поддержки</b>\n"
                    "• Telegram: <a href=\"https://t.me/karma_system_official\">@karma_system_official</a>\n\n"
                    "<b>🌐 Смена языка</b>\nИспользуйте меню выбора языка в настройках бота.\n\n"
                    "<i>Мы рядом, если что — пиши. Приятного пользования! ✨</i>"
                )
            
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
        """Обновить базовый URL (не используется для /static/docs, оставлено для совместимости)"""
        self.web_root = new_url
    
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
