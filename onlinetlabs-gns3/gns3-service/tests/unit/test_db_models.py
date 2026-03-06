# Юнит-тесты DB-моделей gns3-service.

import uuid

import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit]


class TestDBModels:
    @autotests.num("420")
    @autotests.external_id("d1e2f3a4-0001-4ddd-eeee-420000000001")
    @autotests.name("GNS3 Service DB: Session model создаётся")
    def test_session_model(self):
        from src.db.models import Session, SessionStatus

        with autotests.step("Создаём Session"):
            session = Session(
                gns3_user_id="uid",
                gns3_username="student-abc",
                gns3_password_hash="hash",
                gns3_project_id="pid",
                student_user_id="stud-1",
            )
        with autotests.step("Проверяем defaults"):
            assert session.status == SessionStatus.ACTIVE
            assert session.closed_at is None

    @autotests.num("421")
    @autotests.external_id("d1e2f3a4-0002-4ddd-eeee-421000000001")
    @autotests.name("GNS3 Service DB: HistoryEvent model создаётся")
    def test_history_event_model(self):
        from src.db.models import HistoryEvent

        with autotests.step("Создаём HistoryEvent"):
            event = HistoryEvent(
                session_id=uuid.uuid4(),
                event_type="node.started",
                component_id="node-1",
                data={"name": "PC1"},
            )
        with autotests.step("Проверяем поля"):
            assert event.event_type == "node.started"
            assert event.data["name"] == "PC1"

    @autotests.num("422")
    @autotests.external_id("d1e2f3a4-0003-4ddd-eeee-422000000001")
    @autotests.name("GNS3 Service DB: SessionStatus enum")
    def test_session_status_enum(self):
        from src.db.models import SessionStatus

        with autotests.step("Проверяем значения"):
            assert SessionStatus.ACTIVE == "active"
            assert SessionStatus.CLOSED == "closed"
