from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_false,
    assert_in,
    assert_is_none,
    assert_true,
)

from experiment.finalizer import compute_session_metrics
from tests.settings.data.analytics_data import EventData

pytestmark = [pytest.mark.unit]


def _base_events(now: datetime) -> list:
    """2 escalations, 1 would_intervene, 3 intervention."""
    return [
        EventData(
            id="e1", event_type="escalation", action="manual", timestamp=now - timedelta(minutes=20)
        ),
        EventData(
            id="e2",
            event_type="escalation",
            action="objective",
            timestamp=now - timedelta(minutes=18),
        ),
        EventData(
            id="e3",
            event_type="would_intervene",
            action="open",
            timestamp=now - timedelta(minutes=15),
        ),
        EventData(
            id="e4",
            event_type="intervention",
            action="hint",
            success=True,
            timestamp=now - timedelta(minutes=10),
        ),
        EventData(
            id="e5",
            event_type="intervention",
            action="hint",
            success=True,
            timestamp=now - timedelta(minutes=8),
        ),
        EventData(
            id="e6",
            event_type="intervention",
            action="hint",
            success=False,
            timestamp=now - timedelta(minutes=5),
        ),
    ]


class TestFinalizerMetrics:
    @autotest.num("1212")
    @autotest.external_id("fd105d13-88d7-4eb4-8078-025d8f930754")
    @autotest.name(
        "compute_session_metrics: escalations and would_interventions are counted correctly"
    )
    def test_fd105d13_escalations_and_would_interventions(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: build events and call compute_session_metrics"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=3,
                total_steps=5,
                experiment_group="group_b",
                control_arm="closed",
            )
        with autotest.step("Assert: check the new counters"):
            assert_equal(metrics["escalations"], 2, "2 escalations")
            assert_equal(metrics["would_interventions"], 1, "1 would_intervene")
            assert_equal(metrics["l1_interventions"], 3, "3 interventions = l1_interventions")

    @autotest.num("1213")
    @autotest.external_id("67e54f61-352c-42d8-b6b0-c3ccc44269a1")
    @autotest.name("compute_session_metrics: control_arm and base_arm propagate into metrics")
    def test_67e54f61_control_arm_propagated(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: call with control_arm=open, base_arm=closed"):
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
        with autotest.step("Assert: control_arm and base_arm match"):
            assert_equal(metrics["control_arm"], "open", "effective arm = open")
            assert_equal(metrics["base_arm"], "closed", "training arm = closed")
            assert_in("base_arm", metrics, "base_arm present in the metrics dict")

    @autotest.num("1214")
    @autotest.external_id("178b5aee-43e2-4ad2-b1d7-50262dc05ff7")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=None when is_l2=False")
    def test_178b5aee_l2_none_when_not_l2(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: is_l2 not passed (default False)"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=5,
                total_steps=5,
                experiment_group="group_b",
            )
        with autotest.step("Assert: l2_unassisted_pass should be None"):
            assert_is_none(metrics["l2_unassisted_pass"], "None for an L1 session")

    @autotest.num("1215")
    @autotest.external_id("0d357f7e-d514-4c4c-a4a6-1e1f7304e464")
    @autotest.name(
        "compute_session_metrics: l2_unassisted_pass=True when completed and interventions <= cap"
    )
    def test_0d357f7e_l2_pass_within_cap(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: is_l2=True, completed, interventions=3, cap=3"):
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
        with autotest.step("Assert: l2_unassisted_pass=True"):
            assert_true(metrics["l2_unassisted_pass"] is True, "unassisted L2 pass")

    @autotest.num("1216")
    @autotest.external_id("2b2c76fc-3c1a-4840-941f-e4dfa9c7ba24")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=False when interventions > cap")
    def test_2b2c76fc_l2_fail_exceeds_cap(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: is_l2=True, completed, interventions=3, cap=2"):
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
        with autotest.step("Assert: l2_unassisted_pass=False"):
            assert_false(metrics["l2_unassisted_pass"], "not an unassisted pass")

    @autotest.num("1217")
    @autotest.external_id("1a995d42-657a-495b-ae33-b263891b63e4")
    @autotest.name("compute_session_metrics: l2_unassisted_pass=False when not completed")
    def test_1a995d42_l2_fail_not_completed(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: is_l2=True, not completed (2/5 steps), cap=10"):
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
        with autotest.step("Assert: l2_unassisted_pass=False (not completed)"):
            assert_false(metrics["l2_unassisted_pass"], "not completed → not unassisted")

    @autotest.num("1218")
    @autotest.external_id("288327d2-5188-47d6-adf8-a90481b50ba4")
    @autotest.name("compute_session_metrics: existing fields are unchanged")
    def test_288327d2_existing_fields_unchanged(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: standard call without new parameters"):
            metrics = compute_session_metrics(
                events=_base_events(now),
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                steps_completed=3,
                total_steps=5,
                experiment_group="group_b",
                agent_backend="tutor",
            )
        with autotest.step("Assert: old fields are intact"):
            assert_equal(metrics["interventions_received"], 3, "3 interventions")
            assert_equal(metrics["interventions_succeeded"], 2, "2 succeeded")
            assert_equal(metrics["interventions_failed"], 1, "1 failed")
            assert_equal(metrics["interventions_accepted"], 0, "0 accepted")
            assert_equal(metrics["steps_completed"], 3, "3 steps")
            assert_equal(metrics["final_score"], 60.0, "60%")
            assert_equal(metrics["completed"], False, "not completed")
            assert_equal(metrics["experiment_group"], "group_b", "group_b")
            assert_equal(metrics["agent_backend"], "tutor", "backend")

    @autotest.num("1219")
    @autotest.external_id("6df0c600-b76b-4b28-ae1a-967bde85fdc9")
    @autotest.name(
        "compute_session_metrics: base_arm=None by default; completed=False if steps_completed < total_steps"
    )
    def test_6df0c600_base_arm_default_and_incomplete(self):
        now = datetime.now(tz=UTC)
        with autotest.step("Act: base_arm not passed; 1 of 2 steps → not completed"):
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
        with autotest.step("Assert: base_arm=None, completed=False, l2_unassisted_pass=False"):
            assert_is_none(metrics["base_arm"], "base_arm None by default")
            assert_equal(metrics["completed"], False, "not completed")
            assert_false(metrics["l2_unassisted_pass"], "L2 not passed if not completed")
