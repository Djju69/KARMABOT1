"""Core handlers package with router exports"""
from importlib import import_module

def _router(module: str, *names: str):
    """Helper to import router from module"""
    try:
        m = import_module(f"{__name__}.{module}")
        for n in names:
            if hasattr(m, n):
                return getattr(m, n)
        print(f"Warning: No router found in {module} (tried: {', '.join(names)})")
        return None
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_msg = f"Error importing {module}: {str(e)}"
        print(error_msg)
        print("\n".join(traceback.format_exc().split('\n')[-4:-1]))
        return None

# Export routers with fallback names
basic_router = _router("basic", "router", "basic_router")
callback_router = _router("callback", "router", "callback_router")
main_menu_router = _router("main_menu_router", "main_menu_router", "router")
user_router = _router("user", "user_router", "router")
partner_router = _router("partner", "partner_router", "router")
profile_router = _router("profile", "profile_router", "router")
cabinet_router = _router("cabinet_router", "get_cabinet_router", "router")

# Collect all available routers
all_routers = [
    router for router in [
        basic_router,
        callback_router,
        main_menu_router,
        user_router,
        partner_router,
        profile_router,
        cabinet_router
    ] if router is not None
]

# For backward compatibility
__all__ = [
    "basic_router",
    "callback_router",
    "main_menu_router",
    "user_router",
    "partner_router",
    "profile_router",
    "cabinet_router",
    "all_routers"
]
