"""
Модуль для двухфакторной аутентификации (2FA) администраторов.
"""
import pyotp
import qrcode
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import base64
import io

from ..security.roles import Role

logger = logging.getLogger(__name__)

class TwoFactorAuth:
    """Класс для работы с двухфакторной аутентификацией."""
    
    def __init__(self, issuer_name: str = "KarmaBot"):
        self.issuer_name = issuer_name
    
    def generate_secret_key(self) -> str:
        """Генерирует новый секретный ключ для 2FA."""
        return pyotp.random_base32()
    
    def get_totp_uri(self, username: str, secret_key: str) -> str:
        """
        Генерирует URI для настройки 2FA в аутентификаторе.
        
        Args:
            username: Имя пользователя
            secret_key: Секретный ключ
            
        Returns:
            str: URI для настройки 2FA
        """
        return pyotp.totp.TOTP(secret_key).provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )
    
    def generate_qr_code(self, uri: str) -> bytes:
        """
        Генерирует QR-код для настройки 2FA.
        
        Args:
            uri: URI для настройки 2FA
            
        Returns:
            bytes: Изображение QR-кода в формате PNG
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем изображение в байты
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    async def verify_code(self, user_id: int, code: str) -> bool:
        """
        Проверяет код подтверждения и обновляет время последнего использования.
        
        Args:
            user_id: ID пользователя
            code: Код подтверждения от пользователя
            
        Returns:
            bool: True если код верный, иначе False
        """
        try:
            # Получаем настройки 2FA пользователя
            # Lazy import to avoid circular import during module initialization
            from ..database import role_repository  # noqa: WPS433
            settings = await role_repository.get_2fa_settings(user_id)
            if not settings or not settings['is_enabled'] or not settings['secret_key']:
                return False
                
            # Проверяем код
            totp = pyotp.TOTP(settings['secret_key'])
            is_valid = totp.verify(code, valid_window=1)  # Допускаем отклонение в 1 интервал (30 сек)
            
            if is_valid:
                # Обновляем время последнего успешного использования
                from ..database import role_repository  # noqa: WPS433
                await role_repository.update_2fa_last_used(user_id)
                
                # Логируем успешную аутентификацию
                from ..database import role_repository  # noqa: WPS433
                await role_repository.log_audit_event(
                    user_id=user_id,
                    action="2FA_VERIFIED",
                    entity_type="user",
                    entity_id=user_id,
                    metadata={"method": "verify_code"}
                )
            else:
                # Логируем неудачную попытку аутентификации
                from ..database import role_repository  # noqa: WPS433
                await role_repository.log_audit_event(
                    user_id=user_id,
                    action="2FA_VERIFICATION_FAILED",
                    entity_type="user",
                    entity_id=user_id,
                    metadata={"method": "verify_code"}
                )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying 2FA code: {e}")
            
            # Логируем ошибку
            from ..database import role_repository  # noqa: WPS433
            await role_repository.log_audit_event(
                user_id=user_id,
                action="2FA_VERIFICATION_ERROR",
                entity_type="user",
                entity_id=user_id,
                metadata={"error": str(e)}
            )
            
            return False
    
    async def is_2fa_required(self, user_id: int) -> bool:
        """
        Проверяет, требуется ли для пользователя 2FA.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если требуется 2FA, иначе False
        """
        # Получаем роль пользователя
        from ..database import role_repository  # noqa: WPS433
        user_role = await role_repository.get_user_role(user_id)
        
        # 2FA требуется только для админов и суперадминов
        return user_role in [Role.ADMIN, Role.SUPER_ADMIN]
    
    async def is_2fa_enabled(self, user_id: int) -> bool:
        """
        Проверяет, включена ли 2FA для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если 2FA включена, иначе False
        """
        try:
            from ..database import role_repository  # noqa: WPS433
            settings = await role_repository.get_2fa_settings(user_id)
            return settings['is_enabled'] if settings else False
        except Exception as e:
            logger.error(f"Error checking 2FA status: {e}")
            return False
    
    async def enable_2fa(self, user_id: int, secret_key: str) -> bool:
        """
        Включает 2FA для пользователя.
        
        Args:
            user_id: ID пользователя
            secret_key: Секретный ключ
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            # Обновляем настройки 2FA
            from ..database import role_repository  # noqa: WPS433
            result = await role_repository.update_2fa_settings(
                user_id=user_id,
                secret_key=secret_key,
                is_enabled=True
            )
            
            if result:
                # Обновляем время последнего использования
                from ..database import role_repository  # noqa: WPS433
                await role_repository.update_2fa_last_used(user_id)
                
                # Логируем событие
                from ..database import role_repository  # noqa: WPS433
                await role_repository.log_audit_event(
                    user_id=user_id,
                    action="2FA_ENABLED",
                    entity_type="user",
                    entity_id=user_id,
                    metadata={"method": "enable_2fa"}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enabling 2FA: {e}")
            
            # Логируем ошибку
            from ..database import role_repository  # noqa: WPS433
            await role_repository.log_audit_event(
                user_id=user_id,
                action="2FA_ENABLE_ERROR",
                entity_type="user",
                entity_id=user_id,
                metadata={"error": str(e)}
            )
            
            return False
    
    async def disable_2fa(self, user_id: int) -> bool:
        """
        Отключает 2FA для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            # Отключаем 2FA, сохраняя секретный ключ (на случай повторного включения)
            from ..database import role_repository  # noqa: WPS433
            settings = await role_repository.get_2fa_settings(user_id)
            if not settings:
                return True  # Уже отключено
                
            from ..database import role_repository  # noqa: WPS433
            result = await role_repository.update_2fa_settings(
                user_id=user_id,
                secret_key=settings['secret_key'],
                is_enabled=False
            )
            
            if result:
                # Логируем событие
                from ..database import role_repository  # noqa: WPS433
                await role_repository.log_audit_event(
                    user_id=user_id,
                    action="2FA_DISABLED",
                    entity_type="user",
                    entity_id=user_id,
                    metadata={"method": "disable_2fa"}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error disabling 2FA: {e}")
            
            # Логируем ошибку
            from ..database import role_repository  # noqa: WPS433
            await role_repository.log_audit_event(
                user_id=user_id,
                action="2FA_DISABLE_ERROR",
                entity_type="user",
                entity_id=user_id,
                metadata={"error": str(e)}
            )
            
            return False

# Создаем экземпляр для использования в других модулях
two_factor_auth = TwoFactorAuth()
