"""
Сервис для работы с пластиковыми картами лояльности.
"""
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.settings import settings
from . import antifraud_service

logger = logging.getLogger(__name__)

class CardService:
    """Сервис для работы с пластиковыми картами лояльности."""
    
    def __init__(self, db_session: AsyncSession = None):
        """Инициализация сервиса."""
        self.db = db_session or get_db_session()
        
    @staticmethod
    def _hash_pin(card_number: str, pin: str) -> str:
        """Хеширование PIN-кода с использованием соли и номера карты."""
        salt = f"{settings.SECRET_KEY}:{card_number}"
        return hmac.new(
            salt.encode('utf-8'),
            pin.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def verify_card(self, card_number: str, pin: str, partner_id: int, ip_address: str = None) -> Dict[str, Any]:
        """
        Верификация карты по номеру и PIN-коду.
        
        Args:
            card_number: Номер карты
            pin: PIN-код
            partner_id: ID партнера, который проверяет карту
            ip_address: IP-адрес партнера для антифрод-проверок
            
        Returns:
            dict: Информация о карте и пользователе
            
        Raises:
            HTTPException: В случае ошибки валидации или превышения лимитов
        """
        # Антифрод-проверки
        action = 'verify_card'
        identifier = f"partner:{partner_id}"  # Используем ID партнера для лимитов
        
        # Проверяем глобальные лимиты
        is_allowed, remaining = await antifraud_service.check_global_limit('total_card_verifications')
        if not is_allowed:
            logger.warning(f"Global card verification limit exceeded (partner: {partner_id}, ip: {ip_address})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "global_rate_limit_exceeded",
                    "message": "Превышен общий лимит операций. Пожалуйста, повторите позже.",
                    "retry_after": remaining
                },
                headers={"Retry-After": str(remaining) if remaining else "60"}
            )
        
        # Проверяем лимиты для партнера
        is_allowed, remaining = await antifraud_service.check_rate_limit(action, identifier)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for partner {partner_id} (action: {action})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limit_exceeded",
                    "message": "Слишком много запросов. Пожалуйста, подождите.",
                    "retry_after": remaining
                },
                headers={"Retry-After": str(remaining) if remaining else "60"}
            )
        
        # Хешируем PIN
        hashed_pin = self._hash_pin(card_number, pin)
        
        try:
            # Ищем карту и пользователя
            result = await self.db.execute(
                text("""
                    SELECT 
                        c.card_number, c.user_id, c.status, c.issued_at, c.expires_at,
                        u.first_name, u.last_name, u.phone, u.email,
                        l.points_balance, l.points_lifetime
                    FROM user_cards c
                    JOIN users u ON c.user_id = u.id
                    LEFT JOIN loyalty_accounts l ON u.id = l.user_id
                    WHERE c.card_number = :card_number 
                    AND c.pin_hash = :pin_hash
                    AND c.status = 'active'
                """),
                {'card_number': card_number, 'pin_hash': hashed_pin}
            )
            
            card_data = result.mappings().first()
            
            if not card_data:
                # Логируем неудачную попытку входа
                await self._log_card_attempt(card_number, partner_id, ip_address, success=False)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "card_not_found", "message": "Карта не найдена или неверный PIN-код"}
                )
            
            # Проверяем срок действия карты
            if card_data['expires_at'] and card_data['expires_at'] < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "card_expired", "message": "Срок действия карты истек"}
                )
            
            # Логируем успешную попытку входа
            await self._log_card_attempt(card_number, partner_id, ip_address, success=True)
            
            # Увеличиваем счетчики антифрода
            await antifraud_service.increment_counter(action, identifier)
            await antifraud_service.increment_global_counter('total_card_verifications')
            
            # Возвращаем информацию о карте и пользователе
            return {
                "status": "success",
                "card": {
                    "number": card_data['card_number'],
                    "status": card_data['status'],
                    "issued_at": card_data['issued_at'].isoformat(),
                    "expires_at": card_data['expires_at'].isoformat() if card_data['expires_at'] else None
                },
                "user": {
                    "id": card_data['user_id'],
                    "first_name": card_data['first_name'],
                    "last_name": card_data['last_name'],
                    "phone": card_data['phone'],
                    "email": card_data['email']
                },
                "loyalty": {
                    "points_balance": card_data['points_balance'] or 0,
                    "points_lifetime": card_data['points_lifetime'] or 0
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying card: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error", "message": "Произошла ошибка при проверке карты"}
            )
    
    async def _log_card_attempt(self, card_number: str, partner_id: int, ip_address: str, success: bool) -> None:
        """Логирование попытки верификации карты."""
        try:
            masked_number = f"****{card_number[-4:]}" if card_number else "****"
            
            await self.db.execute(
                text("""
                    INSERT INTO card_verification_logs 
                    (card_number, partner_id, ip_address, success, created_at)
                    VALUES (:card_number, :partner_id, :ip_address, :success, NOW())
                """),
                {
                    'card_number': masked_number,
                    'partner_id': partner_id,
                    'ip_address': ip_address,
                    'success': success
                }
            )
            
            # Если это была неудачная попытка, увеличиваем счетчик неудачных попыток
            if not success:
                await self._handle_failed_attempt(card_number, ip_address)
                
        except Exception as e:
            logger.error(f"Error logging card attempt: {str(e)}", exc_info=True)
    
    async def _handle_failed_attempt(self, card_number: str, ip_address: str) -> None:
        """Обработка неудачной попытки входа по карте."""
        try:
            # Увеличиваем счетчик неудачных попыток для этого IP
            cache_key = f"card:failed_attempts:ip:{ip_address}"
            attempts = await antifraud_service.cache_service.incr(cache_key)
            
            # Устанавливаем TTL 1 час
            if attempts == 1:  # Только при первом инкременте
                await antifraud_service.cache_service.expire(cache_key, 3600)
            
            # Если превышено количество попыток - блокируем IP на 24 часа
            if attempts >= 5:
                block_key = f"card:ip_blocked:{ip_address}"
                await antifraud_service.cache_service.set(block_key, "1", ex=86400)  # 24 часа
                logger.warning(f"IP {ip_address} blocked for 24 hours due to too many failed card attempts")
            
            # Также отслеживаем неудачные попытки по номеру карты
            if card_number:
                card_attempts_key = f"card:failed_attempts:card:{card_number}"
                card_attempts = await antifraud_service.cache_service.incr(card_attempts_key)
                
                if card_attempts == 1:  # Только при первом инкременте
                    await antifraud_service.cache_service.expire(card_attempts_key, 86400)  # 24 часа
                
                # Если много неудачных попыток по одной карте - блокируем карту
                if card_attempts >= 3:
                    await self._block_card(card_number, "too_many_failed_attempts")
                    
        except Exception as e:
            logger.error(f"Error handling failed card attempt: {str(e)}", exc_info=True)
    
    async def _block_card(self, card_number: str, reason: str) -> None:
        """Блокировка карты по причине подозрительной активности."""
        try:
            async with self.db.begin() as tx:
                await tx.execute(
                    text("""
                        UPDATE user_cards 
                        SET status = 'blocked', 
                            blocked_at = NOW(), 
                            block_reason = :reason
                        WHERE card_number = :card_number
                    """),
                    {'card_number': card_number, 'reason': reason}
                )
                
                # Логируем блокировку
                await tx.execute(
                    text("""
                        INSERT INTO card_security_events 
                        (card_number, event_type, details, created_at)
                        VALUES (:card_number, 'card_blocked', :details, NOW())
                    """),
                    {
                        'card_number': card_number,
                        'details': f"Card blocked due to: {reason}"
                    }
                )
                
            logger.warning(f"Card {card_number} blocked due to: {reason}")
            
        except Exception as e:
            logger.error(f"Error blocking card {card_number}: {str(e)}", exc_info=True)
            
    async def redeem_points(self, card_number: str, points: int, partner_id: int, ip_address: str = None) -> Dict[str, Any]:
        """
        Списание баллов с карты лояльности.
        
        Args:
            card_number: Номер карты
            points: Количество баллов для списания
            partner_id: ID партнера, который списывает баллы
            ip_address: IP-адрес партнера для антифрод-проверок
            
        Returns:
            dict: Результат операции
            
        Raises:
            HTTPException: В случае ошибки валидации или превышения лимитов
        """
        # Антифрод-проверки
        action = 'redeem_points'
        identifier = f"partner:{partner_id}"  # Используем ID партнера для лимитов
        
        # Проверяем глобальные лимиты
        is_allowed, remaining = await antifraud_service.check_global_limit('total_point_redemptions')
        if not is_allowed:
            logger.warning(f"Global point redemption limit exceeded (partner: {partner_id}, ip: {ip_address})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "global_rate_limit_exceeded",
                    "message": "Превышен общий лимит операций. Пожалуйста, повторите позже.",
                    "retry_after": remaining
                },
                headers={"Retry-After": str(remaining) if remaining else "60"}
            )
        
        # Проверяем лимиты для партнера
        is_allowed, remaining = await antifraud_service.check_rate_limit(action, identifier)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for partner {partner_id} (action: {action})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limit_exceeded",
                    "message": "Слишком много запросов. Пожалуйста, подождите.",
                    "retry_after": remaining
                },
                headers={"Retry-After": str(remaining) if remaining else "60"}
            )
        
        # Начинаем транзакцию
        async with self.db.begin() as tx:
            try:
                # Проверяем баланс и блокируем запись
                result = await tx.execute(
                    text("""
                        SELECT user_id, points_balance, points_lifetime
                        FROM loyalty_accounts
                        WHERE user_id = (
                            SELECT user_id FROM user_cards WHERE card_number = :card_number AND status = 'active'
                        )
                        FOR UPDATE
                    """),
                    {'card_number': card_number}
                )
                
                loyalty_data = result.mappings().first()
                
                if not loyalty_data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={"code": "loyalty_account_not_found", "message": "Счет лояльности не найден"}
                    )
                
                current_balance = loyalty_data['points_balance'] or 0
                
                if current_balance < points:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "insufficient_points",
                            "message": "Недостаточно баллов на счете",
                            "current_balance": current_balance,
                            "requested_points": points
                        }
                    )
                
                # Выполняем списание
                new_balance = current_balance - points
                
                await tx.execute(
                    text("""
                        UPDATE loyalty_accounts
                        SET points_balance = :new_balance,
                            updated_at = NOW()
                        WHERE user_id = :user_id
                    """),
                    {
                        'new_balance': new_balance,
                        'user_id': loyalty_data['user_id']
                    }
                )
                
                # Записываем транзакцию
                await tx.execute(
                    text("""
                        INSERT INTO loyalty_transactions
                        (user_id, amount, transaction_type, partner_id, status, created_at)
                        VALUES (:user_id, :amount, 'redemption', :partner_id, 'completed', NOW())
                    """),
                    {
                        'user_id': loyalty_data['user_id'],
                        'amount': -points,  # Отрицательное значение для списания
                        'partner_id': partner_id
                    }
                )
                
                # Увеличиваем счетчики антифрода
                await antifraud_service.increment_counter(action, identifier)
                await antifraud_service.increment_global_counter('total_point_redemptions')
                
                # Логируем операцию
                await tx.execute(
                    text("""
                        INSERT INTO card_operations
                        (card_number, operation_type, points_amount, partner_id, ip_address, status, created_at)
                        VALUES (:card_number, 'points_redemption', :points, :partner_id, :ip_address, 'completed', NOW())
                    """),
                    {
                        'card_number': card_number,
                        'points': points,
                        'partner_id': partner_id,
                        'ip_address': ip_address
                    }
                )
                
                # Фиксируем транзакцию
                await tx.commit()
                
                return {
                    "status": "success",
                    "user_id": loyalty_data['user_id'],
                    "points_redeemed": points,
                    "new_balance": new_balance,
                    "transaction_id": await tx.connection.scalar("SELECT LASTVAL()")
                }
                
            except HTTPException:
                await tx.rollback()
                raise
                
            except Exception as e:
                await tx.rollback()
                logger.error(f"Error redeeming points: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "internal_error", "message": "Произошла ошибка при списании баллов"}
                )


# Глобальный экземпляр сервиса
card_service = CardService()
