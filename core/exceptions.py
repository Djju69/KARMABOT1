"""
Legacy shim for exceptions: re-export from modern modules if present.
"""
try:
    from core.common.exceptions import *  # type: ignore
except Exception:
    try:
        from core.domain.exceptions import *  # type: ignore
    except Exception:
        # Minimal fallbacks
        class NotFoundError(Exception):
            pass
        class ValidationError(Exception):
            pass
        class BusinessLogicError(Exception):
            pass


