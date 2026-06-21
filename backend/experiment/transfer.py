"""Near-transfer: тот же навык, другой экземпляр лабы = L2 для проверки переноса."""


def skill_tag(lab) -> str | None:
    """Тег навыка лабы из meta['skill']. None, если не задан."""
    return (getattr(lab, "meta", None) or {}).get("skill")


def is_l2_pair(l1_lab, l2_lab) -> bool:
    """L2 — near-transfer для L1: тот же навык, разные slug."""
    s1 = skill_tag(l1_lab)
    return s1 is not None and s1 == skill_tag(l2_lab) and l1_lab.slug != l2_lab.slug
