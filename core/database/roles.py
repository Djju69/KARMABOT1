"""
Модуль для работы с ролями пользователей в базе данных.
"""
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
import logging
from ..security.roles import Role as RoleEnum

logger = logging.getLogger(__name__)

class RoleRepository:
    """Репозиторий для работы с ролями пользователей."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_user_role(self, user_id: int) -> Optional[RoleEnum]:
        """Получить роль пользователя по его ID."""
        try:
            query = """
                SELECT role FROM user_roles 
                WHERE user_id = $1
            """
            result = await self.db.fetchval(query, user_id)
            
            if not result and user_id == self.db.admin_id:
                return RoleEnum.SUPER_ADMIN
                
            return RoleEnum[result] if result else RoleEnum.USER
            
        except Exception as e:
            logger.error(f"Error getting user role: {e}")
            return RoleEnum.USER
    
    async def set_user_role(self, user_id: int, role: RoleEnum) -> bool:
        """Установить роль пользователя."""
        try:
            query = """
                INSERT INTO user_roles (user_id, role, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    role = EXCLUDED.role,
                    updated_at = NOW()
                RETURNING id
            """
            await self.db.execute(query, user_id, role.name)
            return True
            
        except Exception as e:
            logger.error(f"Error setting user role: {e}")
            return False
    
    async def get_users_by_role(self, role: RoleEnum) -> List[int]:
        """Получить список ID пользователей с указанной ролью."""
        try:
            query = """
                SELECT user_id FROM user_roles 
                WHERE role = $1
            """
            result = await self.db.fetch(query, role.name)
            return [row['user_id'] for row in result]
            
        except Exception as e:
            logger.error(f"Error getting users by role: {e}")
            return []
    
    async def log_audit_event(
        self,
        user_id: Optional[int],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Записать событие в аудит-лог.
        
        Args:
            user_id: ID пользователя, выполнившего действие
            action: Тип действия (например, 'USER_LOGIN', 'ROLE_UPDATED')
            entity_type: Тип сущности, к которой относится действие (например, 'user', 'role')
            entity_id: ID сущности, к которой относится действие
            old_values: Старые значения (для обновлений)
            new_values: Новые значения (для обновлений)
            ip_address: IP-адрес, с которого выполнено действие
            user_agent: User-Agent пользователя
            metadata: Дополнительные метаданные в формате словаря
            
        Returns:
            bool: True если запись успешно сохранена, иначе False
        """
        try:
            query = """
                INSERT INTO audit_log (
                    user_id, action, entity_type, entity_id,
                    old_values, new_values, ip_address, user_agent, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            await self.db.execute(
                query,
                user_id,
                action,
                entity_type,
                entity_id,
                old_values,
                new_values,
                ip_address,
                user_agent,
                metadata
            )
            return True
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return False
            
    async def get_2fa_settings(self, user_id: int) -> Optional[dict]:
        """
        Получить настройки 2FA пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: Настройки 2FA или None, если не найдены
        """
        try:
            query = """
                SELECT id, user_id, secret_key, is_enabled, 
                       created_at, updated_at, last_used_at
                FROM two_factor_auth
                WHERE user_id = $1
            """
            return await self.db.fetchrow(query, user_id)
        except Exception as e:
            logger.error(f"Error getting 2FA settings: {e}")
            return None
            
    async def update_2fa_settings(
        self, 
        user_id: int, 
        secret_key: str, 
        is_enabled: bool = True
    ) -> bool:
        """
        Обновить настройки 2FA пользователя.
        
        Args:
            user_id: ID пользователя
            secret_key: Секретный ключ
            is_enabled: Включена ли 2FA
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            query = """
                INSERT INTO two_factor_auth (user_id, secret_key, is_enabled)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    secret_key = EXCLUDED.secret_key,
                    is_enabled = EXCLUDED.is_enabled,
                    updated_at = NOW()
                RETURNING id
            """
            result = await self.db.execute(query, user_id, secret_key, is_enabled)
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating 2FA settings: {e}")
            return False
            
    async def update_2fa_last_used(self, user_id: int) -> bool:
        """
        Обновить время последнего успешного использования 2FA.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно, иначе False
        """
        try:
            query = """
                UPDATE two_factor_auth
                SET last_used_at = NOW()
                WHERE user_id = $1
                RETURNING id
            """
            result = await self.db.execute(query, user_id)
            return bool(result)
        except Exception as e:
            logger.error(f"Error updating 2FA last used time: {e}")
            return False
            
    async def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        Получить записи из аудит-лога с фильтрами.
        
        Args:
            user_id: ID пользователя
            action: Тип действия
            entity_type: Тип сущности
            entity_id: ID сущности
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            list: Список записей аудит-лога
        """
        try:
            query = """
                SELECT al.*, u.username, u.first_name, u.last_name
                FROM audit_log al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE 1=1
            """
            params = []
            param_count = 1
            
            if user_id is not None:
                query += f" AND al.user_id = ${param_count}"
                params.append(user_id)
                param_count += 1
                
            if action is not None:
                query += f" AND al.action = ${param_count}"
                params.append(action)
                param_count += 1
                
            if entity_type is not None:
                query += f" AND al.entity_type = ${param_count}"
                params.append(entity_type)
                param_count += 1
                
            if entity_id is not None:
                query += f" AND al.entity_id = ${param_count}"
                params.append(entity_id)
                param_count += 1
                
            if start_date is not None:
                query += f" AND al.created_at >= ${param_count}"
                params.append(start_date)
                param_count += 1
                
            if end_date is not None:
                query += f" AND al.created_at <= ${param_count}"
                params.append(end_date)
                param_count += 1
            
            # Сортировка по дате (новые сверху)
            query += " ORDER BY al.created_at DESC"
            
            # Ограничение и смещение
            query += f" LIMIT ${param_count}"
            params.append(limit)
            param_count += 1
            
            query += f" OFFSET ${param_count}"
            params.append(offset)
            
            return await self.db.fetch(query, *params)
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
