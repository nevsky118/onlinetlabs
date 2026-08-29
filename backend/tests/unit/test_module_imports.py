"""Every application module imports on its own.

Function-local imports used to hide circular dependencies: the cycle only broke
when the second module was reached, which no test ever did. Importing each
module in isolation surfaces the cycle instead.
"""

import ast
import importlib
import pathlib

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]

_BACKEND = pathlib.Path(__file__).resolve().parents[2]

# Not part of the application: harnesses, generated code and the user's scratch work.
_EXCLUDED = {"tests", "migrations", "measurement", ".e2e", "__pycache__"}


def _module_names() -> list[str]:
    """Dotted names of every application module."""
    names = []
    for path in sorted(_BACKEND.rglob("*.py")):
        rel = path.relative_to(_BACKEND)
        if any(part in _EXCLUDED for part in rel.parts) or path.name == "__init__.py":
            continue
        names.append(".".join(rel.with_suffix("").parts))
    return names


class TestModuleImports:
    @autotest.num("3466")
    @autotest.external_id("f76fd4bb-e404-42ac-ae0b-b0659f347afd")
    @autotest.name("imports: every module imports without a circular dependency")
    def test_f76fd4bb_no_import_cycles(self):
        with autotest.step("Arrange: every application module"):
            names = _module_names()

        with autotest.step("Act: import each one on its own"):
            broken = []
            for name in names:
                try:
                    importlib.import_module(name)
                except ImportError as exc:
                    broken.append(f"{name}: {exc}")

        with autotest.step("Assert: none, and the module list is not empty"):
            assert_equal(len(names) > 100, True, "modules were found")
            assert_equal(broken, [], "no import cycles")

    @autotest.num("3467")
    @autotest.external_id("950255af-f190-40a7-8eb4-7a1fccad0451")
    @autotest.name("imports: no import hides inside a function")
    def test_950255af_imports_are_module_level(self):
        with autotest.step("Act: look for an import statement inside any function"):
            offenders = []
            for path in sorted(_BACKEND.rglob("*.py")):
                rel = path.relative_to(_BACKEND)
                if any(part in _EXCLUDED for part in rel.parts):
                    continue
                tree = ast.parse(path.read_text())
                for fn in ast.walk(tree):
                    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    for node in ast.walk(fn):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            offenders.append(f"{rel}:{node.lineno}")

        with autotest.step("Assert: none, so every dependency is visible at the top of the file"):
            assert_equal(sorted(set(offenders)), [], "imports at module level")
