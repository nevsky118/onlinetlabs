"""Backend localization: locale negotiation, message catalogs, content resolution."""

from i18n.catalog import t, validate_catalogs
from i18n.content import as_locale_map, resolve_localized
from i18n.errors import LocalizedError, localized_error_handler
from i18n.locale import DEFAULT_LOCALE, LOCALES, Locale, negotiate

__all__ = [
    "DEFAULT_LOCALE",
    "LOCALES",
    "Locale",
    "LocalizedError",
    "as_locale_map",
    "localized_error_handler",
    "negotiate",
    "resolve_localized",
    "t",
    "validate_catalogs",
]
