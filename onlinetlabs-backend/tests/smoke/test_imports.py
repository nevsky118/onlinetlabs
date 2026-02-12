import pytest

from tests.report import autotests

pytestmark = pytest.mark.smoke


class TestImports:
    @autotests.num("70")
    @autotests.external_id("2bc7df0b-6603-4ed4-87d4-8f41a6729471")
    @autotests.name("Smoke: all app modules importable")
    def test_all_app_modules_importable(self):
        with autotests.step("Import all app modules"):
            import app.auth.dependencies  # noqa: F401
            import app.auth.exceptions  # noqa: F401
            import app.auth.router  # noqa: F401
            import app.auth.schemas  # noqa: F401
            import app.auth.service  # noqa: F401
            import app.config  # noqa: F401
            import app.config.config_model  # noqa: F401
            import app.config.encryption  # noqa: F401
            import app.config.env_config_loader  # noqa: F401
            import app.db.session  # noqa: F401
            import app.models  # noqa: F401
            import app.models.base  # noqa: F401
            import app.models.course  # noqa: F401
            import app.models.enums  # noqa: F401
            import app.models.lab  # noqa: F401
            import app.models.progress  # noqa: F401
            import app.models.session  # noqa: F401
            import app.models.user  # noqa: F401
