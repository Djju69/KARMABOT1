"""Core handlers package with router exports"""
from importlib import import_module

def _router(module: str, *names: str):
    """Helper to import router from module"""
    m = import_module(f"{__name__}.{module}")
    for n in names:
        if hasattr(m, n):
            return getattr(m, n)
    raise ImportError(f"[{__name__}] {module}: none of {names} found")

# Export routers with fallback names
basic_router = _router("basic", "router", "basic_router")
callback_router = _router("callback", "router", "callback_router")
main_menu_router = _router("main_menu_router", "main_menu_router", "router")

__all__ = ["basic_router", "callback_router", "main_menu_router"]
