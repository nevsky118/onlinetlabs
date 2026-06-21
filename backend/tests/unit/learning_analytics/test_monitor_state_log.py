import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from agents.analytics.models import StruggleType
from config.config_model import LearningAnalyticsConfig
from learning_analytics.monitor import SessionMonitor
from learning_analytics.process_state import ProcessRegime

pytestmark = [pytest.mark.unit]


class _Cap:
    def __init__(self): self.added = []
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def add(self, obj): self.added.append(obj)
    async def commit(self): pass


async def test_logs_state_every_cycle():
    cap = _Cap()
    monitor = SessionMonitor(
        mcp_client=MagicMock(), db_factory=lambda: cap,
        orchestrator=MagicMock(), learning_analytics_config=LearningAnalyticsConfig(),
    )
    monitor._session_id, monitor._user_id, monitor._lab_slug = "s1", "u1", "lab-1"
    a = SimpleNamespace(struggle_detected=True, struggle_type=StruggleType.IDLE)
    t = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)

    r1, d1 = await monitor._log_process_state(a, t)
    r2, d2 = await monitor._log_process_state(a, t + timedelta(seconds=15))

    assert r1 == ProcessRegime.IDLE and d1 == 0.0 and d2 == 15.0
    assert len(cap.added) == 2
    assert cap.added[0].regime == "idle" and cap.added[0].dwell_seconds == 0.0
