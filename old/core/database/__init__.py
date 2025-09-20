from .db_v2 import DatabaseServiceV2, get_db
from .roles import RoleRepository
from .models import Base
from .fault_tolerant_service import fault_tolerant_db
from .enhanced_unified_service import enhanced_unified_db, unified_db
from .platform_adapters import (
    TelegramAdapter, 
    WebsiteAdapter, 
    MobileAppAdapter, 
    DesktopAppAdapter,
    APIAdapter,
    UniversalAdapter
)
from contextlib import contextmanager


# Create a global instance of DatabaseServiceV2
db_v2 = DatabaseServiceV2()
role_repository = RoleRepository(db_v2)

__all__ = [
    'DatabaseServiceV2',
    'db_v2',
    'get_db',
    'RoleRepository',
    'role_repository',
    'Base',
    'fault_tolerant_db',
    'enhanced_unified_db', 
    'unified_db',
    'TelegramAdapter',
    'WebsiteAdapter',
    'MobileAppAdapter',
    'DesktopAppAdapter',
    'APIAdapter',
    'UniversalAdapter',
    'execute_in_transaction'
]


@contextmanager
def execute_in_transaction(db=None):
    """Synchronous transaction context for sqlite connections.

    Usage:
        with execute_in_transaction() as conn:
            conn.execute("...", params)

        with execute_in_transaction(conn) as conn:
            ...
    """
    if db is not None:
        try:
            yield db
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
        except Exception:
            # In case commit failed above, ensure rollback attempted
            try:
                db.rollback()
            except Exception:
                pass
            raise
    else:
        conn = db_v2.get_connection()
        try:
            yield conn
            try:
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
