from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_greater

from experiment.finalizer import compute_session_metrics
from tests.settings.data.analytics_data import EventData

pytestmark = [pytest.mark.unit]


class TestFinalizer:
    @autotest.num("610")
    @autotest.external_id("c3d4e5f6-a7b8-4901-cdef-610000000003")
    @autotest.name("compute_session_metrics: вычисляет метрики из событий")
    def test_c3d4e5f6_compute_metrics(self):
        # Arrange
        with autotest.step("Создаём события сессии"):
            now = datetime.now(tz=UTC)
            events = [
                EventData(
                    id="e1",
                    event_type="action",
                    action="start_node",
                    timestamp=now - timedelta(minutes=30),
                ),
                EventData(
                    id="e2",
                    event_type="error",
                    action="err",
                    message="bad ip",
                    success=False,
                    timestamp=now - timedelta(minutes=25),
                ),
                EventData(
                    id="e3",
                    event_type="error",
                    action="err",
                    message="bad ip",
                    success=False,
                    timestamp=now - timedelta(minutes=20),
                ),
                EventData(
                    id="e4",
                    event_type="error",
                    action="err",
                    message="bad ip",
                    success=False,
                    timestamp=now - timedelta(minutes=15),
                ),
                EventData(
                    id="e5",
                    event_type="action",
                    action="create_link",
                    timestamp=now - timedelta(minutes=10),
                ),
                EventData(
                    id="e6",
                    event_type="intervention",
                    action="intervene_hint",
                    timestamp=now - timedelta(minutes=8),
                    success=True,
                ),
                EventData(
                    id="e7",
                    event_type="intervention",
                    action="intervene_tutor",
                    timestamp=now - timedelta(minutes=7),
                    success=False,
                ),
            ]

        # Act
        with autotest.step("Вычисляем метрики"):
            metrics = compute_session_metrics(
                events=events,
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=3,
                total_steps=5,
                experiment_group="group_b",
                agent_backend="openclaw",
            )

        # Assert
        with autotest.step("Проверяем результат"):
            assert_equal(metrics["total_errors"], 3, "3 ошибки")
            assert_equal(metrics["repeated_errors"], 3, "3 повтора одной ошибки")
            assert_equal(metrics["experiment_group"], "group_b", "group_b")
            assert_equal(metrics["agent_backend"], "openclaw", "backend")
            assert_equal(metrics["interventions_received"], 2, "2 интервенции")
            assert_equal(metrics["interventions_succeeded"], 1, "1 успешная")
            assert_equal(metrics["interventions_failed"], 1, "1 неуспешная")
            assert_equal(metrics["steps_completed"], 3, "3 шага")
            assert_equal(metrics["final_score"], 60.0, "60%")
            assert_greater(metrics["total_time_seconds"], 0, "время > 0")

    @autotest.num("611")
    @autotest.external_id("d4e5f6a7-b8c9-4012-defa-611000000004")
    @autotest.name("compute_session_metrics: пустая сессия")
    def test_d4e5f6a7_empty_session(self):
        # Arrange
        with autotest.step("Готовим границы пустой сессии"):
            now = datetime.now(tz=UTC)

        # Act
        with autotest.step("Вычисляем метрики пустой сессии"):
            metrics = compute_session_metrics(
                events=[],
                started_at=now - timedelta(minutes=5),
                ended_at=now,
                steps_completed=0,
                total_steps=5,
                experiment_group="group_a",
            )

        # Assert
        with autotest.step("Все нули"):
            assert_equal(metrics["total_errors"], 0, "0 ошибок")
            assert_equal(metrics["repeated_errors"], 0, "0 повторов")
            assert_equal(metrics["interventions_succeeded"], 0, "0 успешных")
            assert_equal(metrics["interventions_failed"], 0, "0 неуспешных")
            assert_equal(metrics["final_score"], 0.0, "0%")
