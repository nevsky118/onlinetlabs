import os

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

os.environ.setdefault("DB_USER", "u")
os.environ.setdefault("DB_PASSWORD", "p")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "secret")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("AGENTS_API_KEY", "sk-ant-test")

from experiment.router import _build_status_response, _metric_to_export_row

pytestmark = [pytest.mark.unit]


class MetricData:
    def __init__(self):
        self.user_id = "u1"
        self.session_id = "s1"
        self.experiment_group = "group_b"
        self.agent_backend = "openclaw"
        self.total_time_seconds = 120.0
        self.steps_completed = 4
        self.total_errors = 3
        self.repeated_errors = 2
        self.unique_error_types = 1
        self.interventions_received = 2
        self.interventions_succeeded = 1
        self.interventions_failed = 1
        self.final_score = 80.0
        self.completed = False


class TestExperimentRouterHelpers:
    @autotest.num("637")
    @autotest.external_id("58f5e51b-2be8-42ea-ab63-b1bd50453504")
    @autotest.name("Experiment Router: status response использует lettered groups")
    def test_58f5e51b_status_response_lettered_groups(self):
        # Arrange
        with autotest.step("Готовим counts"):
            counts = {"group_a": 3, "group_b": 5, "control": 99}

        # Act
        with autotest.step("Собираем status response"):
            response = _build_status_response(counts, completed=4, in_progress=2)

        # Assert
        with autotest.step("Проверяем lettered groups"):
            assert_equal(response.group_a_count, 3, "group_a_count")
            assert_equal(response.group_b_count, 5, "group_b_count")
            assert_equal(response.total_participants, 8, "total")
            assert_equal(response.completed_count, 4, "completed")

    @autotest.num("638")
    @autotest.external_id("efb7a9a1-6be3-4e1d-8788-0deeff0f00f9")
    @autotest.name("Experiment Router: export row содержит backend metadata")
    def test_efb7a9a1_metric_export_row_backend_metadata(self):
        # Arrange
        with autotest.step("Готовим метрику"):
            metric = MetricData()

        # Act
        with autotest.step("Собираем export row"):
            row = _metric_to_export_row(metric)

        # Assert
        with autotest.step("Проверяем backend metadata"):
            assert_equal(row["experiment_group"], "group_b", "group")
            assert_equal(row["agent_backend"], "openclaw", "backend")
            assert_equal(row["interventions_succeeded"], 1, "succeeded")
            assert_equal(row["interventions_failed"], 1, "failed")
