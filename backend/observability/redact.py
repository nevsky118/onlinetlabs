"""Редакция detail событий: вырезает секреты, обрезает длинные строки/объём."""

import json

_SECRET_HINTS = ("api_key", "apikey", "authorization", "token", "secret", "password")


def _is_secret(key: str) -> bool:
    """Проверяет, выглядит ли ключ как секрет."""
    k = key.lower()
    return any(h in k for h in _SECRET_HINTS) or k.endswith("_key")


def redact(detail, *, max_field_len: int = 500, max_total: int = 4096):
    """Маскирует секреты, обрезает строки и общий размер detail."""
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
    # Ограничение общего размера: drop крупных полей до влезания.
    while len(json.dumps(out, ensure_ascii=False, default=str)) > max_total and out:
        biggest = max(out, key=lambda k: len(json.dumps(out[k], ensure_ascii=False, default=str)))
        out[biggest] = "…(dropped)"
        if all(v == "…(dropped)" for v in out.values()):
            break
    return out
