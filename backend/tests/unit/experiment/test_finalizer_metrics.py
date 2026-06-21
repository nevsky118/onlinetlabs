import pytest
from datetime import datetime, timedelta, timezone

from experiment.finalizer import compute_session_metrics
from tests.settings.data.analytics_data import EventData
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]


def _base_events(now: datetime) -> list:
    """2 эскалации, 1 would_intervene, 3 intervention."""
    return [
        EventData(id="e1", event_type="escalation", action="manual", timestamp=now - timedelta(minutes=20)),
        EventData(id="e2", event_type="escalation", action="objective", timestamp=now - timedelta(minutes=18)),
        EventData(id="e3", event_type="would_intervene", action="open", timestamp=now - timedelta(minutes=15)),
        EventData(id="e4", event_type="intervention", action="hint", success=True, timestamp=now - timedelta(minutes=10)),
        EventData(id="e5", event_type="intervention", action="hint", success=True, timestamp=now - timedelta(minutes=8)),
        EventData(id="e6", event_type="intervention", action="hint", success=False, timestamp=now - timedelta(minutes=5)),
    ]


class TestFinalizerMetricsTask8:
    @autotest.num("620")
    @autotest.external_id("a1b2c3d4-e5f6-4000-abcd-620000000001")
    @autotest.name("compute_session_metrics: escalations и would_interventions считаются корректно")
    def test_a1b2c3d4_escalations_and_would_interventions(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Формируем события и вызываем compute_session_metrics"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=3,
                total_steps=5,
                experiment_group="group_b",
                control_arm="closed",
            )
        with autotest.step("Проверяем новые счётчики"):
            assert_equal(metrics["escalations"], 2, "2 эскалации")
            assert_equal(metrics["would_interventions"], 1, "1 would_intervene")
            assert_equal(metrics["l1_interventions"], 3, "3 интервенции = l1_interventions")

    @autotest.num("621")
    @autotest.external_id("b2c3d4e5-f6a7-4001-bcde-621000000002")
    @autotest.name("compute_session_metrics: control_arm и base_arm пробрасываются в метрики")
    def test_b2c3d4e5_control_arm_propagated(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Вызываем с control_arm=open, base_arm=closed"):
            metrics = compute_session_metrics(
                events=[],
                started_at=now - timedelta(minutes=5),
                ended_at=now,
                steps_completed=0,
                total_steps=5,
                experiment_group="group_a",
                control_arm="open",
                base_arm="closed",
            )
        with autotest.step("control_arm и base_arm совпадают"):
            assert_equal(metrics["control_arm"], "open", "effective arm = open")
            assert_equal(metrics["base_arm"], "closed", "training arm = closed")
            assert "base_arm" in metrics, "base_arm присутствует в словаре метрик"

    @autotest.num("622")
    @autotest.external_id("c3d4e5f6-a7b8-4002-cdef-622000000003")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=None когда is_l2=False")
    def test_c3d4e5f6_l2_none_when_not_l2(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("is_l2 не передаётся (default False)"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=5,
                total_steps=5,
                experiment_group="group_b",
            )
        with autotest.step("l2_unassisted_pass должен быть None"):
            assert metrics["l2_unassisted_pass"] is None, "None для L1 сессии"

    @autotest.num("623")
    @autotest.external_id("d4e5f6a7-b8c9-4003-defa-623000000004")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=True когда завершено и интервенции <= cap")
    def test_d4e5f6a7_l2_pass_within_cap(self):
        now = datetime.now(tz=timezone.utc)
        # 3 интервенции, cap=3 → pass
        with autotest.step("is_l2=True, completed, interventions=3, cap=3"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=5,
                total_steps=5,
                experiment_group="group_b",
                l2_intervention_cap=3,
                is_l2=True,
            )
        with autotest.step("l2_unassisted_pass=True"):
            assert metrics["l2_unassisted_pass"] is True, "автономная сдача L2"

    @autotest.num("624")
    @autotest.external_id("e5f6a7b8-c9d0-4004-efab-624000000005")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=False когда интервенции > cap")
    def test_e5f6a7b8_l2_fail_exceeds_cap(self):
        now = datetime.now(tz=timezone.utc)
        # 3 интервенции, cap=2 → fail
        with autotest.step("is_l2=True, completed, interventions=3, cap=2"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=5,
                total_steps=5,
                experiment_group="group_b",
                l2_intervention_cap=2,
                is_l2=True,
            )
        with autotest.step("l2_unassisted_pass=False"):
            assert metrics["l2_unassisted_pass"] is False, "не автономная сдача"

    @autotest.num("625")
    @autotest.external_id("f6a7b8c9-d0e1-4005-fabc-625000000006")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=False когда не завершено")
    def test_f6a7b8c9_l2_fail_not_completed(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("is_l2=True, не завершено (2/5 шагов), cap=10"):
            metrics = compute_session_metrics(
                events=[],
                started_at=now - timedelta(minutes=10),
                ended_at=now,
                steps_completed=2,
                total_steps=5,
                experiment_group="group_b",
                l2_intervention_cap=10,
                is_l2=True,
            )
        with autotest.step("l2_unassisted_pass=False (не завершено)"):
            assert metrics["l2_unassisted_pass"] is False, "не завершено → не автономно"

    @autotest.num("627")
    @autotest.external_id("b8c9d0e1-f2a3-4007-bcde-627000000008")
    @autotest.name("compute_session_metrics: base_arm=None по умолчанию; completed=False если steps_completed < total_steps")
    def test_b8c9d0e1_base_arm_default_and_incomplete(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Не передаём base_arm; шагов 1 из 2 → не завершено"):
            metrics = compute_session_metrics(
                events=[],
                started_at=now - timedelta(minutes=5),
                ended_at=now,
                steps_completed=1,
                total_steps=2,
                experiment_group="group_b",
                is_l2=True,
                l2_intervention_cap=10,
            )
        with autotest.step("base_arm=None, completed=False, l2_unassisted_pass=False"):
            assert metrics["base_arm"] is None, "base_arm None по умолчанию"
            assert_equal(metrics["completed"], False, "не завершено")
            assert metrics["l2_unassisted_pass"] is False, "L2 не пройдено если не завершено"

    @autotest.num("626")
    @autotest.external_id("a7b8c9d0-e1f2-4006-abcd-626000000007")
    @autotest.name("compute_session_metrics: существующие поля не изменились")
    def test_a7b8c9d0_existing_fields_unchanged(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Стандартный вызов без новых параметров"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=3,
                total_steps=5,
                experiment_group="group_b",
                agent_backend="openclaw",
            )
        with autotest.step("Старые поля на месте"):
            assert_equal(metrics["interventions_received"], 3, "3 интервенции")
            assert_equal(metrics["interventions_succeeded"], 2, "2 успешные")
            assert_equal(metrics["interventions_failed"], 1, "1 неуспешная")
            assert_equal(metrics["interventions_accepted"], 0, "0 принятых")
            assert_equal(metrics["steps_completed"], 3, "3 шага")
            assert_equal(metrics["final_score"], 60.0, "60%")
            assert_equal(metrics["completed"], False, "не завершено")
            assert_equal(metrics["experiment_group"], "group_b", "group_b")
            assert_equal(metrics["agent_backend"], "openclaw", "openclaw")
