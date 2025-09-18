"""
Common utilities and exceptions for KARMABOT.
"""

from .exceptions import (
    NotFoundError,
    ValidationError,
    BusinessLogicError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ExternalServiceError
)

__all__ = [
    'NotFoundError',
    'ValidationError', 
    'BusinessLogicError',
    'AuthenticationError',
    'AuthorizationError',
    'DatabaseError',
    'ExternalServiceError'
]
