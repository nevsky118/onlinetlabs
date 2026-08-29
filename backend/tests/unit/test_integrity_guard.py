"""Integrity guard: production code does not depend on seeded/.e2e artifacts (tripwire)."""

import re
from pathlib import Path

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]

# Production directories of the backend (excluding tests/, .e2e/, migrations/, scripts/).
_PROD_DIRS = [
    "analytics",
    "agents",
    "experiment",
    "sessions",
    "admin",
    "consent",
]
# The seeded A/B lives only in .e2e/ab_run.py (l2_pass). No analysis/production
# path should pull it in, otherwise seeded data leaks into submission artifacts.
_BANNED = re.compile(r"(\.e2e\b|\bab_run\b|\bl2_pass\b)")


class TestIntegrityGuard:
    @autotest.num("1987")
    @autotest.external_id("c1d81b0c-70e7-43ea-8177-714b34e525fc")
    @autotest.name("Integrity guard: production code does not depend on seeded/.e2e/l2_pass")
    def test_c1d81b0c_no_seeded_dependency_in_production(self):
        with autotest.step("Arrange: locate the backend package root"):
            backend = Path(__file__).parents[2]

        with autotest.step("Act: scan production modules for seeded dependencies"):
            offenders = []
            for directory in _PROD_DIRS:
                for py in (backend / directory).rglob("*.py"):
                    if _BANNED.search(py.read_text(encoding="utf-8")):
                        offenders.append(str(py.relative_to(backend)))

        with autotest.step("Assert: no production module pulls in seeded data"):
            assert_equal(offenders, [], f"seeded dependencies in production: {offenders}")
