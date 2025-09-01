from .db_v2 import DatabaseServiceV2, get_db
from .roles import RoleRepository

# Create a global instance of DatabaseServiceV2
db_v2 = DatabaseServiceV2()
role_repository = RoleRepository(db_v2)

__all__ = [
    'DatabaseServiceV2', 
    'db_v2', 
    'get_db',
    'RoleRepository',
    'role_repository'
]
