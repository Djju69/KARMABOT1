"""
Common exceptions for the KARMABOT application.
"""


class NotFoundError(Exception):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class BusinessLogicError(Exception):
    """Raised when business logic constraints are violated."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(Exception):
    """Raised when external service calls fail."""
    pass
