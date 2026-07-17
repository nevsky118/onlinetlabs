"""Redaction of event detail: strips secrets, truncates long strings/size."""

import json

_SECRET_HINTS = ("api_key", "apikey", "authorization", "token", "secret", "password")


def _is_secret(key: str) -> bool:
    """Checks whether a key looks like a secret."""
    k = key.lower()
    return any(h in k for h in _SECRET_HINTS) or k.endswith("_key")


def redact(detail, *, max_field_len: int = 500, max_total: int = 4096):
    """Masks secrets, truncates strings and the overall size of detail."""
    if detail is None:
        return None
    out = {}
    for key, value in detail.items():
        if _is_secret(str(key)):
            out[key] = "***"
        elif isinstance(value, str) and len(value) > max_field_len:
            out[key] = value[:max_field_len] + "…(truncated)"
        else:
            out[key] = value
    # Overall size cap: drop large fields until it fits.
    while len(json.dumps(out, ensure_ascii=False, default=str)) > max_total and out:
        biggest = max(out, key=lambda k: len(json.dumps(out[k], ensure_ascii=False, default=str)))
        out[biggest] = "…(dropped)"
        if all(v == "…(dropped)" for v in out.values()):
            break
    return out
