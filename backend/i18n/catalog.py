"""YAML message catalogs, one per locale."""

import string
from functools import cache
from pathlib import Path

import yaml

from i18n.locale import DEFAULT_LOCALE, LOCALES, Locale

_MESSAGES_DIR = Path(__file__).parent / "messages"


def _flatten(node: dict, prefix: str = "") -> dict[str, str]:
    """Nested YAML mappings to flat dotted keys."""
    flat: dict[str, str] = {}
    for key, value in node.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{path}."))
        else:
            flat[path] = str(value)
    return flat


@cache
def _catalog(locale: Locale) -> dict[str, str]:
    """Parsed catalog for a locale. Loaded once; there is no hot reload."""
    with (_MESSAGES_DIR / f"{locale}.yaml").open(encoding="utf-8") as fh:
        return _flatten(yaml.safe_load(fh) or {})


def _placeholders(message: str) -> set[str]:
    """Names of the str.format fields in a message."""
    return {field for _, field, _, _ in string.Formatter().parse(message) if field}


def t(key: str, locale: Locale, **params: object) -> str:
    """Message for a dotted key. Falls back to DEFAULT_LOCALE; raises KeyError if absent in both.

    Messages go through str.format, so a literal brace must be written doubled.
    """
    # `is None`, not `or`: an empty message is a deliberate value, not a missing key.
    message = _catalog(locale).get(key)
    if message is None:
        message = _catalog(DEFAULT_LOCALE).get(key)
    if message is None:
        raise KeyError(f"i18n key not found in any catalog: {key}")
    return message.format(**params)


def validate_catalogs() -> None:
    """Raises ValueError when locales disagree on keys or on a key's placeholders."""
    reference = _catalog(DEFAULT_LOCALE)
    for locale in LOCALES:
        if locale == DEFAULT_LOCALE:
            continue
        catalog = _catalog(locale)
        missing = sorted(set(reference) - set(catalog))
        extra = sorted(set(catalog) - set(reference))
        if missing or extra:
            raise ValueError(f"i18n catalog '{locale}': missing={missing} extra={extra}")
        for key, message in catalog.items():
            expected = _placeholders(reference[key])
            actual = _placeholders(message)
            if expected != actual:
                raise ValueError(
                    f"i18n catalog '{locale}': key '{key}' has placeholders "
                    f"{sorted(actual)}, expected {sorted(expected)}"
                )
