"""
Сервис для работы с QR-кодами (скидки и списание баллов).
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

import qrcode
from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.settings import settings
from . import antifraud_service


class QRService:
    """Сервис для работы с QR-кодами."""

    def __init__(self, db_session: AsyncSession = None):
        """Инициализация сервиса."""
        self.db = db_session or get_db_session()
        self.fernet = Fernet(settings.FERNET_KEY)

    async def create_qr(self, user_id: int, listing_id: int = None, points: int = None, ip_address: str = None) -> Tuple[bytes, str]:
        """
        Создание QR-кода для скидки или списания баллов.
        
        Args:
            user_id: ID пользователя, создающего QR-код
            listing_id: ID листинга (для скидки)
            points: Количество баллов (для списания)
            ip_address: IP-адрес пользователя для антифрод-проверок
            
        Returns:
            Tuple[bytes, str]: (qr_image_bytes, token)
            
        Raises:
            HTTPException: Если превышены лимиты на генерацию QR-кодов
        """
        # Антифрод-проверки
        action = 'generate_qr'
        identifier = str(user_id)  # Используем user_id для лимитов
        
        # Проверяем лимиты для пользователя
        is_allowed, remaining = await antifraud_service.check_rate_limit(action, identifier)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user {user_id} (action: {action})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limit_exceeded",
                    "message": "Слишком много запросов. Пожалуйста, подождите.",
                    "retry_after": remaining
                },
                headers={"Retry-After": str(remaining) if remaining else "60"}
            )
        
        # Генерируем уникальный идентификатор
        jti = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(
            hours=24 if listing_id else 0.25  # 24ч для скидок, 15 минут для баллов
        )
        
        # Сохраняем в базу
        try:
            async with self.db.begin():
                await self.db.execute(
                    text("""
                        INSERT INTO qr_issues 
                        (jti, user_id, listing_id, points, status, created_at, exp_at, ip_address)
                        VALUES (:jti, :user_id, :listing_id, :points, 'issued', NOW(), :exp_at, :ip_address)
                    """),
                    {
                        'jti': jti,
                        'user_id': user_id,
                        'listing_id': listing_id,
                        'points': points,
                        'exp_at': expires_at,
                        'ip_address': ip_address
                    }
                )
            
            # Увеличиваем счетчик использований
            await antifraud_service.increment_counter(action, identifier)
            
            # Генерируем токен
            token = self.fernet.encrypt(jti.encode()).decode()
            
            # Генерируем QR-код
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_data = {
                'type': 'discount' if listing_id else 'points',
                'token': token,
                'expires_at': expires_at.isoformat()
            }
            if listing_id:
                qr_data['listing_id'] = listing_id
            if points:
                qr_data['points'] = points
                
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Конвертируем в байты
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            
            return img_byte_arr.getvalue(), token
            
        except Exception as e:
            logger.error(f"Error creating QR code: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "internal_error",
                    "message": "Произошла ошибка при создании QR-кода"
                }
            )

    async def redeem_qr(self, token: str, partner_id: int, ip_address: str = None) -> Dict[str, Any]:
        """
        Погашение QR-кода.
        
        Args:
            token: Токен из QR-кода
            partner_id: ID партнера, который сканирует QR
            ip_address: IP-адрес партнера для антифрод-проверок
            
        Returns:
            dict: Результат операции
            
        Raises:
            HTTPException: В случае ошибки валидации или превышения лимитов
        """
        # Антифрод-проверки
        action = 'redeem_qr'
        identifier = str(partner_id)  # Используем partner_id для лимитов
        
        # Проверяем глобальные лимиты
        is_allowed, remaining = await antifraud_service.check_global_limit('total_redeems')
        if not is_allowed:
            logger.warning(f"Global redeem limit exceeded (partner: {partner_id}, ip: {ip_address})")
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
        
        try:
            # Декодируем токен
            jti = self.fernet.decrypt(token.encode()).decode()
        except Exception:
            return {'status': 'error', 'code': 'invalid_token'}
        
        async with self.db.begin() as tx:
            # Атомарное обновление
            result = await tx.execute(
                text("""
                    WITH updated AS (
                        UPDATE qr_issues
                        SET status = 'redeemed',
                            redeemed_at = NOW(),
                            redeemed_by_partner_id = :partner_id
                        WHERE jti = :jti
                        AND status = 'issued'
                        AND (exp_at IS NULL OR exp_at > NOW())
                        RETURNING *
                    )
                    SELECT * FROM updated
                """),
                {'jti': jti, 'partner_id': partner_id}
            )
            
            qr_data = result.fetchone()
            
            if not qr_data:
                # Проверяем, что QR-код не был использован
                result = await self.db.execute(
                    text("""
                        SELECT jti, user_id, listing_id, points, status, exp_at < NOW() as is_expired,
                               created_at, ip_address, redeemed_at, redeemed_by
                        FROM qr_issues
                        WHERE jti = :jti
                        FOR UPDATE
                    """),
                    {'jti': jti}
                )
                row = result.mappings().first()
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={"code": "not_found", "message": "QR-код не найден"}
                    )
                    
                if row['status'] == 'redeemed':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "already_redeemed",
                            "message": "Этот QR-код уже был использован",
                            "redeemed_at": row['redeemed_at'].isoformat() if row['redeemed_at'] else None,
                            "redeemed_by": row['redeemed_by']
                        }
                    )
                    
                if row['is_expired']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "expired",
                            "message": "Срок действия QR-кода истек",
                            "expired_at": row['exp_at'].isoformat() if 'exp_at' in row else None
                        }
                    )
                
                # Проверка на повторное использование (дополнительная защита)
                if ip_address and row['ip_address'] and row['ip_address'] == ip_address:
                    logger.warning(f"Possible QR reuse detected: jti={jti}, ip={ip_address}")
                
                # Обновляем статус на использованный
                await self.db.execute(
                    text("""
                        UPDATE qr_issues 
                        SET status = 'redeemed', 
                            redeemed_at = NOW(), 
                            redeemed_by = :partner_id,
                            redeem_ip = :ip_address
                        WHERE jti = :jti
                    """),
                    {'jti': jti, 'partner_id': partner_id, 'ip_address': ip_address}
                )
                
                # Увеличиваем счетчики антифрода
                await antifraud_service.increment_counter(action, identifier)
                await antifraud_service.increment_global_counter('total_redeems')
                
                # Если это QR на списание баллов
                if row['points'] and row['points'] > 0:
                    # Здесь должна быть логика списания баллов
                    # Например, вызов сервиса лояльности
                    return {
                        'status': 'success',
                        'type': 'points',
                        'points': row['points'],
                        'user_id': row['user_id']
                    }
                # Если это QR на скидку
                elif row['listing_id']:
                    return {
                        'status': 'success',
                        'type': 'discount',
                        'listing_id': row['listing_id'],
                        'user_id': row['user_id']
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"code": "invalid_qr_type", "message": "Неверный тип QR-кода"}
                    )
                    
            else:
                # Если QR-код был использован
                return {
                    'status': 'success',
                    'qr_data': dict(qr_data)
                }
                
        except HTTPException as e:
            logger.warning(f"HTTPException in redeem_qr: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error redeeming QR code: {str(e)}", exc_info=True)
            if hasattr(self, 'db'):
                await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error", "message": "Произошла ошибка при обработке QR-кода"}
            )

    async def get_qr_info(self, token: str) -> Optional[dict]:
        """
        Получение информации о QR-коде.
        
        Args:
            token: Токен QR-кода
            
        Returns:
            Optional[dict]: Информация о QR-коде или None, если не найден
        """
        try:
            jti = self.fernet.decrypt(token.encode()).decode()
        except Exception:
            return None
            
        result = await self.db.execute(
            text("""
                SELECT * FROM qr_issues WHERE jti = :jti
            """),
            {'jti': jti}
        )
        
        row = result.fetchone()
        return dict(row) if row else None
