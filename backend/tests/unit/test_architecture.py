"""The layout rules, enforced. A restructure that nothing checks decays."""

import ast
from pathlib import Path

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]

_BACKEND = Path(__file__).resolve().parents[2]

# Shared plumbing. Must know nothing about any feature.
_INFRA = {"kit", "clients", "config", "i18n", "observability", "models"}

# Everything that owns a slice of the product.
_FEATURES = {
    "admin",
    "agents",
    "analytics",
    "auth",
    "chat",
    "consent",
    "experiment",
    "instructor",
    "labs",
    "progress",
    "sessions",
    "users",
    "validation",
    "worker",
}

# Not part of the application: research harnesses and one-shot CLIs.
_EXCLUDED = {"tests", "migrations", "measurement", "scripts", "simulation", ".e2e", "__pycache__"}


def _modules() -> list[Path]:
    """Every application source file."""
    return [
        path
        for path in _BACKEND.rglob("*.py")
        if not any(part in _EXCLUDED for part in path.relative_to(_BACKEND).parts)
    ]


def _package_of(path: Path) -> str:
    """The top-level package a file belongs to, or an empty string at the root."""
    parts = path.relative_to(_BACKEND).parts
    return parts[0] if len(parts) > 1 else ""


def _imported_roots(path: Path) -> set[str]:
    """Top-level package names this file imports."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return set()
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


class TestLayering:
    @autotest.num("3448")
    @autotest.external_id("dea3c7c5-f004-433b-b19a-a2483aa1bcbe")
    @autotest.name("infrastructure never imports a feature")
    def test_dea3c7c5_infra_does_not_import_features(self):
        with autotest.step("Act: scan every infrastructure module for a feature import"):
            violations = []
            for path in _modules():
                package = _package_of(path)
                if package not in _INFRA:
                    continue
                for root in _imported_roots(path) & _FEATURES:
                    violations.append(f"{path.relative_to(_BACKEND)} -> {root}")

        with autotest.step("Assert: the one dependency rule with a direction holds"):
            assert_equal(sorted(violations), [], "infra stays below features")

    @autotest.num("3449")
    @autotest.external_id("3e54233a-7fed-45bd-b205-db5a97963ab4")
    @autotest.name("only models/ defines ORM tables")
    def test_3e54233a_orm_lives_in_models(self):
        with autotest.step("Act: look for __tablename__ outside models/"):
            offenders = []
            for path in _modules():
                if _package_of(path) == "models":
                    continue
                if "__tablename__" in path.read_text():
                    offenders.append(str(path.relative_to(_BACKEND)))

        with autotest.step("Assert: none"):
            assert_equal(sorted(offenders), [], "ORM only in models/")

    @autotest.num("3450")
    @autotest.external_id("ce78fe1c-a913-418c-8fa3-fde02b3c0b7b")
    @autotest.name("no module called models.py outside models/")
    def test_ce78fe1c_one_meaning_of_model(self):
        with autotest.step("Act: find every models.py"):
            offenders = [
                str(path.relative_to(_BACKEND))
                for path in _modules()
                if path.name == "models.py" and _package_of(path) != "models"
            ]

        with autotest.step("Assert: Pydantic lives in schemas.py"):
            assert_equal(sorted(offenders), [], "one meaning of model")

    @autotest.num("3451")
    @autotest.external_id("61a59a5d-abf5-4517-94ea-7895e26ef038")
    @autotest.name("routes are declared only in a router module")
    def test_61a59a5d_routes_live_in_routers(self):
        with autotest.step("Act: find route decorators outside a router module"):
            offenders = []
            for path in _modules():
                name = path.name
                if name.startswith("router") or name.endswith("_router.py"):
                    continue
                if path.parent.name == "routers" or _package_of(path) == "":
                    continue
                text = path.read_text()
                if "@router.get(" in text or "@router.post(" in text:
                    offenders.append(str(path.relative_to(_BACKEND)))

        with autotest.step("Assert: none"):
            assert_equal(sorted(offenders), [], "routes only in routers")

    @autotest.num("3452")
    @autotest.external_id("59e09461-1ed3-4d00-b430-5b2816caf497")
    @autotest.name("no package survives that holds a single small module")
    def test_59e09461_no_single_module_packages(self):
        with autotest.step("Arrange: every application package"):
            packages = {
                path.parent for path in _modules() if _package_of(path) and path.parent != _BACKEND
            }

        with autotest.step("Act: find packages of one module under 80 lines"):
            offenders = []
            for package in packages:
                modules = [
                    module for module in package.glob("*.py") if module.name != "__init__.py"
                ]
                if len(modules) != 1:
                    continue
                if len(modules[0].read_text().splitlines()) < 80 and not any(
                    child.is_dir() and child.name != "__pycache__" for child in package.iterdir()
                ):
                    offenders.append(str(package.relative_to(_BACKEND)))

        with autotest.step("Assert: a package earns its directory"):
            assert_equal(sorted(offenders), [], "no ceremonial packages")
