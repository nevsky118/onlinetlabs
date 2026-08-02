"""Localized content stored as a plain string or a locale map."""

from i18n.locale import DEFAULT_LOCALE, Locale


def resolve_localized(value: str | dict | None, locale: Locale) -> str:
    """Text for a locale. A plain string applies to every locale; a map falls back locale, default, any."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    for candidate in (locale, DEFAULT_LOCALE):
        text = value.get(candidate)
        if text:
            return text
    for text in value.values():
        if text:
            return text
    return ""


def as_locale_map(value: str | dict | None) -> dict[str, str] | None:
    """Normalizes API input to a locale map. A bare string is stored under DEFAULT_LOCALE."""
    if value is None:
        return None
    if isinstance(value, str):
        return {DEFAULT_LOCALE: value}
    return {key: text for key, text in value.items() if text}
