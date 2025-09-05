# Back-compat import for older code expecting core.utils.i18n
try:
    from .locales import get_text as _  # noqa: F401
except Exception:
    pass
