from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("telemetry")


def _user_to_dict(user: Any) -> dict:
    try:
        return {
            "id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "language_code": getattr(user, "language_code", None),
        }
    except Exception:
        return {}


def _safe_json(data: dict) -> str:
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        # Fallback to string representation
        return str(data)


async def log_event(event: str, *, user: Optional[Any] = None, **fields: Any) -> None:
    """
    Emit a structured log line to stdout with event name, timestamp, and fields.

    Usage:
        await log_event("policy_accepted", user=callback.from_user, lang=lang)
    """
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    if user is not None:
        payload["user"] = _user_to_dict(user)
    if fields:
        payload.update(fields)
    logger.info(_safe_json(payload))


def telemetry(event_name: str):
    """Decorator to auto-log start/finish of a function. Works for async functions.

    Example:
        @telemetry("some_operation")
        async def handler(...):
            ...
    """
    def decorator(func):
        if hasattr(func, "__call__"):
            if hasattr(func, "__await__") or "async def" in str(func):
                async def wrapper(*args, **kwargs):
                    await log_event(event_name + ":start")
                    try:
                        result = await func(*args, **kwargs)
                        await log_event(event_name + ":ok")
                        return result
                    except Exception as e:
                        await log_event(event_name + ":error", error=str(e))
                        raise
                return wrapper
            else:
                def wrapper_sync(*args, **kwargs):
                    # Synchronous fallback (rare in handlers)
                    logging.getLogger("telemetry").info(_safe_json({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "event": event_name + ":start",
                    }))
                    try:
                        result = func(*args, **kwargs)
                        logging.getLogger("telemetry").info(_safe_json({
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "event": event_name + ":ok",
                        }))
                        return result
                    except Exception as e:
                        logging.getLogger("telemetry").info(_safe_json({
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "event": event_name + ":error",
                            "error": str(e),
                        }))
                        raise
                return wrapper_sync
        return func
    return decorator
