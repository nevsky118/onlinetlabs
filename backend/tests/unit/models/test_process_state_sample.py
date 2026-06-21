import pytest
pytestmark = [pytest.mark.unit]


def test_model_columns_present():
    from models.process_state_sample import ProcessStateSample
    cols = set(ProcessStateSample.__table__.columns.keys())
    assert {"id", "session_id", "user_id", "lab_slug", "ts", "regime", "dwell_seconds", "created_at"} <= cols
    assert ProcessStateSample.__tablename__ == "process_state_samples"
