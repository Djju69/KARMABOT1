from .db_v2 import DatabaseServiceV2, get_db

# Create a global instance of DatabaseServiceV2
db_v2 = DatabaseServiceV2()

__all__ = ['DatabaseServiceV2', 'db_v2', 'get_db']
