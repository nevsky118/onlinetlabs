"""Static audit of every LocalizedError raise site against the message catalogs.

A wrong-but-existing key or a mismatched placeholder only fails when that error path
actually fires, which in production means in front of a user. These tests fail at CI time
instead by walking the source rather than exercising each endpoint.
"""

import ast
import string
from pathlib import Path

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from i18n import DEFAULT_LOCALE, LOCALES
from i18n.catalog import _catalog

pytestmark = [pytest.mark.unit]

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_SKIP_DIRS = {"tests", "migrations", ".venv", "__pycache__", ".e2e"}


def _source_files() -> list[Path]:
    """Every backend source file, excluding tests, migrations and virtualenvs."""
    return [
        path
        for path in _BACKEND_ROOT.rglob("*.py")
        if not _SKIP_DIRS.intersection(path.relative_to(_BACKEND_ROOT).parts)
    ]


def _localized_error_calls() -> list[tuple[str, int, str, set[str]]]:
    """Every LocalizedError(...) call as (file, line, key, kwarg names).

    Calls whose key is not a literal are returned with an empty key for the caller to flag.
    """
    found = []
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name != "LocalizedError":
                continue
            key = ""
            if node.args and isinstance(node.args[0], ast.Constant):
                key = str(node.args[0].value)
            kwargs = {kw.arg for kw in node.keywords if kw.arg and kw.arg != "status_code"}
            found.append((str(path.relative_to(_BACKEND_ROOT)), node.lineno, key, kwargs))
    return found


def _placeholders(message: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(message) if field}


class TestLocalizedErrorCallSites:
    @autotest.num("3146")
    @autotest.external_id("b56e93df-26f4-477b-8826-61576a930be8")
    @autotest.name("LocalizedError: every raise site uses a literal key present in all catalogs")
    def test_b56e93df_keys_exist_in_every_catalog(self):
        with autotest.step("Arrange: collect every LocalizedError call site in the source"):
            calls = _localized_error_calls()

        with autotest.step("Assert: the audit found call sites at all"):
            assert_true(len(calls) > 0, "the AST walk must find LocalizedError raises")

        with autotest.step("Assert: each key is a literal and resolves in every locale"):
            for file, line, key, _ in calls:
                assert_true(
                    key != "", f"{file}:{line} passes a non-literal key, so it is unauditable"
                )
                for locale in LOCALES:
                    assert_true(
                        key in _catalog(locale),
                        f"{file}:{line} uses '{key}', missing from {locale}.yaml",
                    )

    @autotest.num("3147")
    @autotest.external_id("200538bb-8e76-4373-9233-5b87a0589efe")
    @autotest.name("LocalizedError: every raise site supplies exactly its key's placeholders")
    def test_200538bb_params_match_placeholders(self):
        with autotest.step("Arrange: collect call sites and the default catalog"):
            calls = _localized_error_calls()
            catalog = _catalog(DEFAULT_LOCALE)

        with autotest.step("Assert: supplied kwargs match the key's placeholders exactly"):
            for file, line, key, kwargs in calls:
                expected = _placeholders(catalog[key])
                assert_equal(
                    kwargs,
                    expected,
                    f"{file}:{line} key '{key}' passes {sorted(kwargs)}, needs {sorted(expected)}",
                )
