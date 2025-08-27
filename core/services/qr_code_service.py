"""
Сервис для работы с QR-кодами скидок.
Обрабатывает выпуск, валидацию и погашение QR-кодов.
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

import qrcode
from cryptography.fernet import Fernet
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import settings
from core.database import get_db_session
from core.services.cache import cache_service
from core.utils.telemetry import log_event

logger = logging.getLogger(__name__)

class QRCodeService:
    """Сервис для работы с QR-кодами скидок."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Инициализация сервиса."""
        self.db = db_session or get_db_session()
        self.fernet = Fernet(settings.FERNET_KEY)

    async def create_qr_code(self, user_id: int, listing_id: int) -> Tuple[bytes, str]:
        """
        Создает QR-код для скидки по листингу.
        
        Args:
            user_id: ID пользователя, создающего QR-код
            listing_id: ID листинга, для которого создается скидка
            
        Returns:
            Tuple[bytes, str]: (изображение QR-кода в байтах, токен)
            
        Raises:
            ValueError: если лимит на создание QR-кодов превышен
        """
        # Проверка лимитов на частоту запросов
        rate_limit_key = f"qr_issue_rl:{user_id}:{listing_id}"
        daily_limit_key = f"qr_issue_daily:{user_id}:{listing_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        
        # Проверка лимита: 1 запрос в минуту
        if await cache_service.get(rate_limit_key):
            raise ValueError("rate_limited")
            
        # Проверка дневного лимита (5 кодов в день)
        daily_count = int(await cache_service.get(daily_limit_key) or 0)
        if daily_count >= 5:
            raise ValueError("daily_limit_reached")
        
        # Получение информации о листинге
        listing = await self._get_listing(listing_id)
        if not listing or listing.get('moderation_status') != 'approved' or listing.get('is_hidden'):
            raise ValueError("invalid_listing")
        
        # Создание записи о выпущенном QR-коде
        jti = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        async with self.db.begin() as tx:
            await tx.execute(
                text("""
                    INSERT INTO qr_issues (jti, listing_id, user_id, status, exp_at, created_at)
                    VALUES (:jti, :listing_id, :user_id, 'issued', :exp_at, NOW())
                """),
                {
                    'jti': jti,
                    'listing_id': listing_id,
                    'user_id': user_id,
                    'exp_at': expires_at
                }
            )
        
        # Установка лимитов в кэше
        await cache_service.set(rate_limit_key, "1", ex=60)  # 1 запрос в минуту
        await cache_service.incr(daily_limit_key, ex=86400)  # Счетчик на сутки
        
        # Генерация токена
        token = self.fernet.encrypt(jti.encode()).decode()
        
        # Генерация QR-кода
        qr_data = {
            'type': 'discount',
            'token': token,
            'listing_id': listing_id,
            'expires_at': expires_at.isoformat()
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертация в байты
        import io
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        # Логирование события
        await log_event(
            actor_id=user_id,
            entity_type="qr_code",
            entity_id=jti,
            action="issue",
            details={"listing_id": listing_id}
        )
        
        return img_byte_arr.getvalue(), token
    
    async def _get_listing(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о листинге по ID."""
        result = await self.db.execute(
            text("""
                SELECT id, title, moderation_status, is_hidden, offer_details
                FROM listings
                WHERE id = :listing_id
            """),
            {'listing_id': listing_id}
        )
        return result.fetchone()._asdict() if result.rowcount > 0 else None
    
    async def redeem_qr_code(self, token: str, partner_id: int, bill_amount: int) -> Dict[str, Any]:
        """
        Погашает скидку по QR-коду.
        
        Args:
            token: Токен из QR-кода
            partner_id: ID партнера, который погашает скидку
            bill_amount: Сумма чека в копейках
            
        Returns:
            Dict с информацией о примененной скидке
            
        Raises:
            ValueError: если QR-код невалиден или не может быть погашен
        """
        try:
            # Расшифровка токена
            jti = self.fernet.decrypt(token.encode()).decode()
        except Exception as e:
            logger.warning(f"Invalid QR token: {e}")
            raise ValueError("invalid_token")
        
        async with self.db.begin() as tx:
            # Атомарное обновление статуса QR-кода
            result = await tx.execute(
                text("""
                    WITH updated AS (
                        UPDATE qr_issues
                        SET status = 'redeemed',
                            redeemed_at = NOW(),
                            redeemed_by_partner_id = :partner_id
                        WHERE jti = :jti
                        AND status = 'issued'
                        AND exp_at > NOW()
                        RETURNING *
                    )
                    SELECT * FROM updated
                """),
                {'jti': jti, 'partner_id': partner_id}
            )
            
            qr_data = result.fetchone()
            
            if not qr_data:
                # Проверяем причину неудачи
                result = await tx.execute(
                    text("""
                        SELECT status, exp_at < NOW() as is_expired
                        FROM qr_issues 
                        WHERE jti = :jti
                    """),
                    {'jti': jti}
                )
                row = result.fetchone()
                
                if not row:
                    raise ValueError("not_found")
                elif row.status == 'redeemed':
                    raise ValueError("already_redeemed")
                elif row.is_expired:
                    raise ValueError("expired")
                else:
                    raise ValueError("invalid_status")
            
            qr_data = dict(qr_data)
            
            # Получаем информацию о листинге
            listing = await self._get_listing(qr_data['listing_id'])
            if not listing:
                raise ValueError("listing_not_found")
            
            # Рассчитываем скидку на основе правил в offer_details
            discount_amount = self._calculate_discount(listing['offer_details'], bill_amount)
            final_amount = bill_amount - discount_amount
            
            # Создаем запись о погашении
            receipt_data = {
                'jti': jti,
                'listing_id': qr_data['listing_id'],
                'partner_profile_id': partner_id,
                'user_id': qr_data['user_id'],
                'bill_amount': bill_amount,
                'discount_rule': listing['offer_details'],
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'redemption_method': 'qr'
            }
            
            await tx.execute(
                text("""
                    INSERT INTO redeem_receipts (
                        jti, listing_id, partner_profile_id, user_id,
                        bill_amount, discount_rule, discount_amount,
                        final_amount, redemption_method
                    ) VALUES (
                        :jti, :listing_id, :partner_profile_id, :user_id,
                        :bill_amount, :discount_rule, :discount_amount,
                        :final_amount, :redemption_method
                    )
                """),
                receipt_data
            )
            
            # Логируем событие
            await log_event(
                actor_id=partner_id,
                entity_type="qr_code",
                entity_id=jti,
                action="redeem",
                details={
                    "listing_id": qr_data['listing_id'],
                    "bill_amount": bill_amount,
                    "discount_amount": discount_amount
                }
            )
            
            return {
                'success': True,
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'listing_title': listing['title']
            }
    
    def _calculate_discount(self, offer_details: Dict[str, Any], bill_amount: int) -> int:
        """
        Рассчитывает размер скидки на основе правил в offer_details.
        
        Args:
            offer_details: Детали предложения из таблицы listings
            bill_amount: Сумма чека в копейках
            
        Returns:
            Размер скидки в копейках
        """
        if not offer_details or 'type' not in offer_details:
            return 0
            
        discount_type = offer_details['type']
        value = offer_details.get('value', 0)
        
        if discount_type == 'fixed':
            return min(value * 100, bill_amount)  # value в рублях, переводим в копейки
        elif discount_type == 'percent':
            return int(bill_amount * (value / 100))
        else:
            return 0

# Синглтон для использования в приложении
qr_code_service = QRCodeService()
