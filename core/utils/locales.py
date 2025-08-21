# Compatibility shim to support legacy imports
# Re-exports from locales_v2 for modules expecting core.utils.locales

from .locales_v2 import (
    translations_v2 as translations,
    get_text,
    get_all_texts,
    get_supported_languages,
    validate_translations,
    save_translations_to_file,
    load_translations_from_file,
)

__all__ = [
    "translations",
    "get_text",
    "get_all_texts",
    "get_supported_languages",
    "validate_translations",
    "save_translations_to_file",
    "load_translations_from_file",
]
