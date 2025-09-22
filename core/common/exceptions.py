"""
Common exceptions for the application
"""

class NotFoundError(Exception):
    """Raised when a resource is not found"""
    pass

class ValidationError(Exception):
    """Raised when validation fails"""
    pass

class DatabaseError(Exception):
    """Raised when database operation fails"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class AuthorizationError(Exception):
    """Raised when authorization fails"""
    pass

class ServiceError(Exception):
    """Raised when service operation fails"""
    pass

class BusinessLogicError(Exception):
    """Raised when business logic validation fails"""
    pass
