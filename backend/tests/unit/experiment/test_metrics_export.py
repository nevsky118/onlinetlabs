import os

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from tests.settings.data.experiment_data import ExportMetricData

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

from experiment.service import metric_to_export_row

pytestmark = [pytest.mark.unit]


class TestExperimentRouterHelpers:
    @autotest.num("631")
    @autotest.external_id("efb7a9a1-2b8a-4a4e-9e58-2f0d1c8e5b6a")
    @autotest.name("Experiment Router: export row contains intervention counters")
    def test_efb7a9a1_metric_export_row_backend_metadata(self):
        # Arrange
        with autotest.step("Prepare a metrics row"):
            metric = ExportMetricData()

        # Act
        with autotest.step("Build the export row"):
            row = metric_to_export_row(metric)

        # Assert
        with autotest.step("Check the intervention counters"):
            assert_equal(row["interventions_succeeded"], 1, "succeeded")
            assert_equal(row["interventions_failed"], 1, "failed")
