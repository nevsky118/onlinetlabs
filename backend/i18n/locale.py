"""Supported locales and header negotiation."""

from typing import Literal, get_args

Locale = Literal["en", "ru"]
LOCALES: tuple[Locale, ...] = get_args(Locale)
DEFAULT_LOCALE: Locale = "en"


def negotiate(raw: str | None) -> Locale:
    """Maps an X-Locale header value to a supported locale; unknown or absent yields the default."""
    if not raw:
        return DEFAULT_LOCALE
    tag = raw.strip().split(",")[0].split(";")[0].split("-")[0].lower()
    for locale in LOCALES:
        if tag == locale:
            return locale
    return DEFAULT_LOCALE
