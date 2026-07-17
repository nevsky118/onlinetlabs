"""Near-transfer: тот же навык, другой экземпляр лабы = L2 для проверки переноса."""


def skill_tag(lab) -> str | None:
    """Тег навыка лабы из meta['skill']. None, если не задан."""
    return (getattr(lab, "meta", None) or {}).get("skill")
