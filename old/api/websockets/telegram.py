"""
WebSocket endpoint для обработки обновлений от Telegram бота.
"""
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from typing import Dict, Any

from core.services.telegram_bot_service import TelegramBotService
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class TelegramWebhookManager:
    """Менеджер WebSocket соединений для Telegram бота"""
    
    def __init__(self, bot_token: str):
        self.active_connections: Dict[str, WebSocket] = {}
        self.bot_service = TelegramBotService(token=bot_token)
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Добавляет новое WebSocket соединение"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Удаляет отключенное соединение"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Remaining connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        """Отправляет сообщение всем подключенным клиентам"""
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {str(e)}")
    
    async def handle_telegram_update(self, update: Dict[str, Any]):
        """
        Обрабатывает обновление от Telegram API
        
        Args:
            update: Обновление от Telegram API
        """
        try:
            # Обрабатываем обновление через сервис бота
            await self.bot_service.process_update(update)
            
            # Логируем обновление
            update_id = update.get('update_id')
            logger.info(f"Processed Telegram update {update_id}")
            
            # Отправляем подтверждение об успешной обработке
            return {"status": "ok", "update_id": update_id}
            
        except Exception as e:
            logger.error(f"Error processing Telegram update: {str(e)}")
            return {"status": "error", "detail": str(e)}

# Создаем экземпляр менеджера
manager = TelegramWebhookManager(bot_token=settings.telegram_bot_token)

@router.websocket("/ws/telegram/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint для получения обновлений от Telegram бота.
    
    Args:
        websocket: WebSocket соединение
        client_id: Уникальный идентификатор клиента
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            
            try:
                # Парсим JSON с обновлением
                update = json.loads(data)
                
                # Обрабатываем обновление
                result = await manager.handle_telegram_update(update)
                
                # Отправляем результат обратно клиенту
                await websocket.send_json(result)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "detail": "Invalid JSON format"
                })
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "detail": f"Error processing update: {str(e)}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(client_id)
        await websocket.close()

# Функция для отправки уведомления пользователю
async def send_telegram_notification(user_id: int, message: str, **kwargs):
    """
    Отправляет уведомление пользователю через Telegram бота
    
    Args:
        user_id: ID пользователя в системе
        message: Текст сообщения
        **kwargs: Дополнительные параметры для сообщения
        
    Returns:
        bool: Успешность отправки
    """
    # В реальном приложении здесь должна быть логика получения пользователя из БД
    # и проверка, что у него привязан Telegram аккаунт
    from core.schemas.auth import UserInDB
    
    # Это упрощенный пример, в реальном приложении нужно получать пользователя из БД
    user = UserInDB(id=user_id, telegram_id=user_id)  # Заглушка
    
    return await manager.bot_service.send_notification(user, message, **kwargs)
