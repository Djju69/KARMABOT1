"""
Сервис для работы с Telegram ботом.
Обрабатывает команды бота и взаимодействует с API приложения.
"""
import logging
from typing import Dict, Any, Optional, Tuple

import aiohttp
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.exceptions import TelegramAPIError

from core.config import settings
from core.schemas.auth import UserInDB

logger = logging.getLogger(__name__)

class TelegramBotService:
    """Сервис для работы с Telegram ботом"""
    
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot)
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков команд бота"""
        self.dp.register_message_handler(
            self._start_command, 
            commands=['start'], 
            state='*'
        )
        self.dp.register_message_handler(
            self._help_command, 
            commands=['help'], 
            state='*'
        )
        self.dp.register_message_handler(
            self._link_account, 
            commands=['link'], 
            state='*'
        )
    
    async def _start_command(self, message: types.Message):
        """Обработчик команды /start"""
        welcome_text = (
            "👋 Привет! Я бот KarmaSystem.\n\n"
            "Я помогу тебе управлять твоим аккаунтом и получать уведомления.\n"
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать справку\n"
            "/link - Привязать аккаунт"
        )
        
        await message.answer(welcome_text)
    
    async def _help_command(self, message: types.Message):
        """Обработчик команды /help"""
        help_text = (
            "ℹ️ Справка по командам бота KarmaSystem\n\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/link - Привязать аккаунт к боту\n\n"
            "По всем вопросам обращайтесь в поддержку."
        )
        
        await message.answer(help_text)
    
    async def _link_account(self, message: types.Message):
        """Обработчик команды /link для привязки аккаунта"""
        # Получаем токен для привязки аккаунта
        async with aiohttp.ClientSession() as session:
            try:
                # Отправляем запрос на генерацию токена
                async with session.post(
                    f"{settings.api_url}/api/v1/telegram/auth-token",
                    headers={"Authorization": f"Bearer {message.get('token', '')}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        token = data.get('token')
                        
                        # Создаем кнопку для привязки аккаунта
                        web_app = WebAppInfo(url=f"{settings.frontend_url}/link-telegram?token={token}")
                        keyboard = InlineKeyboardMarkup(row_width=1)
                        keyboard.add(
                            InlineKeyboardButton(
                                text="🔗 Привязать аккаунт", 
                                web_app=web_app
                            )
                        )
                        
                        await message.answer(
                            "Для привязки аккаунта нажмите на кнопку ниже:",
                            reply_markup=keyboard
                        )
                    else:
                        error = await response.json()
                        await message.answer(
                            f"❌ Ошибка: {error.get('detail', 'Неизвестная ошибка')}"
                        )
                        
            except Exception as e:
                logger.error(f"Error in link_account: {str(e)}")
                await message.answer("❌ Произошла ошибка при обработке запроса")
    
    async def send_notification(
        self, 
        user: UserInDB, 
        message: str, 
        **kwargs
    ) -> bool:
        """
        Отправляет уведомление пользователю в Telegram
        
        Args:
            user: Объект пользователя
            message: Текст сообщения
            **kwargs: Дополнительные параметры (например, keyboard)
            
        Returns:
            bool: Успешность отправки
        """
        if not user.telegram_id:
            logger.warning(f"User {user.id} has no Telegram account linked")
            return False
            
        try:
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                **kwargs
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to send Telegram message to user {user.id}: {str(e)}")
            return False
    
    async def process_update(self, update: Dict[str, Any]):
        """
        Обрабатывает обновление от Telegram
        
        Args:
            update: Обновление от Telegram API
        """
        try:
            await self.dp.feed_update(
                bot=self.bot, 
                update=types.Update(**update)
            )
        except Exception as e:
            logger.error(f"Error processing Telegram update: {str(e)}")
            raise
