"""
Модуль для работы с ролями пользователей в базе данных.
"""
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Local Role enum to avoid circular imports
class RoleEnum(Enum):
    """Роли пользователей"""
    USER = "user"
    PARTNER = "partner"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class RoleRepository:
    """Репозиторий для работы с ролями пользователей."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_user_role(self, user_id: int) -> Optional[RoleEnum]:
        """Получить роль пользователя по его ID."""
        try:
            # Ensure user_roles table exists
            from core.database.migrations import ensure_user_roles_table
            ensure_user_roles_table()
            
            # For DatabaseServiceV2 (SQLite), use synchronous method
            if hasattr(self.db, 'get_connection'):
                # This is DatabaseServiceV2 - use synchronous SQLite
                conn = self.db.get_connection()
                cursor = conn.execute(
                    "SELECT role FROM user_roles WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                result = result[0] if result else None
                conn.close()
            else:
                # This is async database service (PostgreSQL)
                query = """
                    SELECT role FROM user_roles
                    WHERE user_id = $1
                """
                result = await self.db.fetchval(query, user_id)

            if not result and user_id == getattr(self.db, 'admin_id', None):
                return RoleEnum.SUPER_ADMIN

            return RoleEnum[result] if result else RoleEnum.USER

        except Exception as e:
            logger.error(f"Error getting user role: {e}")
            return RoleEnum.USER
    
    async def set_user_role(self, user_id: int, role: RoleEnum) -> bool:
        """Установить роль пользователя."""
        try:
            # For DatabaseServiceV2 (SQLite), use synchronous method
            if hasattr(self.db, 'get_connection'):
                # This is DatabaseServiceV2 - use synchronous SQLite
                conn = self.db.get_connection()
                conn.execute("""
                    INSERT OR REPLACE INTO user_roles (user_id, role, updated_at)
                    VALUES (?, ?, datetime('now'))
                """, (user_id, role.name))
                conn.commit()
                conn.close()
                return True
            else:
                # This is async database service (PostgreSQL)
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
            # For DatabaseServiceV2 (SQLite), use synchronous method
            if hasattr(self.db, 'get_connection'):
                # This is DatabaseServiceV2 - use synchronous SQLite
                conn = self.db.get_connection()
                cursor = conn.execute(
                    "SELECT user_id FROM user_roles WHERE role = ?",
                    (role.name,)
                )
                result = cursor.fetchall()
                user_ids = [row['user_id'] for row in result]
                conn.close()
                return user_ids
            else:
                # This is async database service (PostgreSQL)
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

        Для SQLite (DatabaseServiceV2) — безопасная заглушка (только лог),
        чтобы не падать без таблицы audit_log.
        """
        try:
            # SQLite: просто логируем и выходим успешно
            if hasattr(self.db, 'get_connection'):
                logger.info(
                    "AUDIT(STUB): user_id=%s action=%s entity=%s#%s meta=%s",
                    user_id, action, entity_type, entity_id, metadata,
                )
                return True

            # Async PG: пишем в таблицу audit_log
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

        Для SQLite — возвращаем выключенную 2FA (без падений).
        """
        try:
            if hasattr(self.db, 'get_connection'):
                # Безопасная заглушка для локальной/SQLite среды
                return {
                    'id': None,
                    'user_id': user_id,
                    'secret_key': None,
                    'is_enabled': False,
                    'created_at': None,
                    'updated_at': None,
                    'last_used_at': None,
                }

            # Async PG: читаем реальные настройки
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
        secret_key: Optional[str],
        is_enabled: bool = True
    ) -> bool:
        """
        Обновить настройки 2FA пользователя.

        Для SQLite — без операций с БД, успешная заглушка.
        """
        try:
            if hasattr(self.db, 'get_connection'):
                logger.info(
                    "2FA(STUB): would update settings for user_id=%s enabled=%s",
                    user_id, is_enabled,
                )
                return True

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

        Для SQLite — без операций с БД, успешная заглушка.
        """
        try:
            if hasattr(self.db, 'get_connection'):
                logger.info("2FA(STUB): would update last_used for user_id=%s", user_id)
                return True

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

        Для SQLite — возвращаем пустой список, чтобы не падать.
        """
        try:
            if hasattr(self.db, 'get_connection'):
                return []

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


# --- SQLite safety helpers (runtime) ---
def ensure_sqlite_user_roles_table(db_service) -> None:
    """
    Ensure minimal user_roles table exists in SQLite runtime.
    No-op for async Postgres adapters (no get_connection attribute).
    """
    try:
        if not hasattr(db_service, "get_connection"):
            return  # Not SQLite service
        conn = db_service.get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL DEFAULT 'USER',
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"ensure_sqlite_user_roles_table failed: {e}")
