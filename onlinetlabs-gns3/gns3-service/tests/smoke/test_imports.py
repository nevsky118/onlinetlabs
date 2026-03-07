import pytest

from tests.report import autotests

pytestmark = [pytest.mark.smoke]


class TestImports:
    @autotests.num("400")
    @autotests.external_id("e1f2a3b4-0001-4eee-ffff-000000000001")
    @autotests.name("GNS3 Service: config импортируем")
    def test_config_importable(self):
        with autotests.step("Импортируем config"):
            from src.config.config_model import GNS3ServiceConfigModel  # noqa: F401
            from src.config.env_config_loader import EnvConfigLoader  # noqa: F401

    @autotests.num("401")
    @autotests.external_id("e1f2a3b4-0002-4eee-ffff-000000000002")
    @autotests.name("GNS3 Service: models импортируемы")
    def test_models_importable(self):
        with autotests.step("Импортируем models"):
            from src.models import SessionCreate, SessionResponse, HistoryEvent  # noqa: F401

    @autotests.num("403")
    @autotests.external_id("e1f2a3b4-0004-4eee-ffff-000000000003")
    @autotests.name("GNS3 Service: DB models импортируемы")
    def test_db_models_importable(self):
        with autotests.step("Импортируем DB models"):
            from src.db.models import Session, HistoryEvent, SessionStatus  # noqa: F401

    @autotests.num("404")
    @autotests.external_id("e1f2a3b4-0005-4eee-ffff-000000000004")
    @autotests.name("GNS3 Service: admin client импортируем")
    def test_admin_client_importable(self):
        with autotests.step("Импортируем admin client"):
            from src.gns3_admin_client import GNS3AdminClient  # noqa: F401

    @autotests.num("405")
    @autotests.external_id("e1f2a3b4-0006-4eee-ffff-000000000005")
    @autotests.name("GNS3 Service: session service импортируем")
    def test_service_importable(self):
        with autotests.step("Импортируем service"):
            from src.service import SessionService  # noqa: F401

    @autotests.num("406")
    @autotests.external_id("e1f2a3b4-0007-4eee-ffff-000000000006")
    @autotests.name("GNS3 Service: history listener импортируем")
    def test_history_importable(self):
        with autotests.step("Импортируем history"):
            from src.history import HistoryListener  # noqa: F401
