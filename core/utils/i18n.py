from .locales import get_text as _  # Simple alias for back-compat

def get_text(lang: str, key: str) -> str:
	return _(lang, key)
