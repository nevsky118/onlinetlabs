"""Integrity-guard: production-код не зависит от seeded/.e2e артефактов (tripwire)."""

import re
from pathlib import Path

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]

# Production-каталоги backend'а (без tests/, .e2e/, migrations/, scripts/).
_PROD_DIRS = [
    "learning_analytics", "control", "agents", "experiment", "sessions",
    "evaluation", "cohort", "admin", "escalation", "control_interface",
]
# Засеянный A/B живёт только в .e2e/ab_run.py (l2_pass). Ни один анализ/production
# путь не должен его тянуть — иначе seeded-данные утекают в сабмит-артефакты.
_BANNED = re.compile(r"(\.e2e\b|\bab_run\b|\bl2_pass\b)")


class TestIntegrityGuard:
    @autotest.num("1987")
    @autotest.external_id("c1d81b0c-70e7-43ea-8177-714b34e525fc")
    @autotest.name("Integrity guard: production-код не зависит от seeded/.e2e/l2_pass")
    def test_c1d81b0c_no_seeded_dependency_in_production(self):
        with autotest.step("Act: сканировать production-модули на seeded-зависимости"):
            backend = Path(__file__).parents[2]
            offenders = []
            for d in _PROD_DIRS:
                for py in (backend / d).rglob("*.py"):
                    if _BANNED.search(py.read_text(encoding="utf-8")):
                        offenders.append(str(py.relative_to(backend)))

        with autotest.step("Assert: ни один production-модуль не тянет seeded-данные"):
            assert_equal(offenders, [], f"seeded-зависимости в production: {offenders}")
