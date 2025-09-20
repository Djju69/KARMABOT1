# Import all route modules here to make them available when importing from api.routes
from . import auth
from . import telegram

# List of all route modules that should be included in the FastAPI app
__all__ = ["auth", "telegram"]
