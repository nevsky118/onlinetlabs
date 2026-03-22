import pytest
from datetime import datetime, timedelta, timezone

from learning_analytics.features import FeatureExtractor
from agents.analytics.models import SessionFeatures
from tests.settings.data.analytics_data import EventData, EventSequenceData
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_true,
    assert_greater,
    assert_greater_equal,
    assert_less_equal,
)

pytestmark = [pytest.mark.unit]


class TestFeatureExtractor:
    @autotest.num("530")
    @autotest.external_id("f9a0b1c2-d3e4-4f5a-8b6c-d7e8f9a0b1c2")
    @autotest.name("FeatureExtractor: пустой список событий")
    def test_f9a0b1c2_extract_from_empty_events(self):
        with autotest.step("Вычисляем фичи из пустого списка"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", [])

        with autotest.step("Проверяем нулевые значения"):
            assert_true(isinstance(features, SessionFeatures), "тип SessionFeatures")
            assert_equal(features.events_total, 0, "0 событий")
            assert_equal(features.avg_inter_action_latency, 0.0, "0 латентность")
            assert_equal(features.error_repeat_count, 0, "0 повторов ошибок")

    @autotest.num("531")
    @autotest.external_id("01a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c")
    @autotest.name("FeatureExtractor: средняя латентность между действиями")
    def test_01a2b3c4_avg_inter_action_latency(self):
        with autotest.step("Создаём 5 событий с интервалом 10с"):
            events = EventSequenceData(5, interval_seconds=10.0).events

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем латентность ~10с"):
            assert_greater_equal(features.avg_inter_action_latency, 9.0, ">= 9")
            assert_less_equal(features.avg_inter_action_latency, 11.0, "<= 11")

    @autotest.num("532")
    @autotest.external_id("12b3c4d5-e6f7-4a8b-9c0d-1e2f3a4b5c6d")
    @autotest.name("FeatureExtractor: обнаружение idle периодов")
    def test_12b3c4d5_idle_periods_detected(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём события с gap > 60с"):
            events = [
                EventData(id="e1", timestamp=now - timedelta(seconds=200)),
                EventData(id="e2", timestamp=now - timedelta(seconds=100)),
                EventData(id="e3", timestamp=now),
            ]

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем idle_periods >= 1"):
            assert_greater_equal(features.idle_periods, 1, "минимум 1 idle период")

    @autotest.num("533")
    @autotest.external_id("23c4d5e6-f7a8-4b9c-8d0e-2f3a4b5c6d7e")
    @autotest.name("FeatureExtractor: подсчёт повторяющихся ошибок")
    def test_23c4d5e6_error_repeat_count(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 3 одинаковые ошибки подряд"):
            events = [
                EventData(id="e1", event_type="error", action="cfg_err", message="bad ip",
                         success=False, timestamp=now - timedelta(seconds=30)),
                EventData(id="e2", event_type="error", action="cfg_err", message="bad ip",
                         success=False, timestamp=now - timedelta(seconds=20)),
                EventData(id="e3", event_type="error", action="cfg_err", message="bad ip",
                         success=False, timestamp=now - timedelta(seconds=10)),
            ]

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем error_repeat_count >= 3"):
            assert_greater_equal(features.error_repeat_count, 3, "минимум 3 повтора")

    @autotest.num("534")
    @autotest.external_id("34d5e6f7-a8b9-4c0d-9e1f-3a4b5c6d7e8f")
    @autotest.name("FeatureExtractor: энтропия 0 при однородных действиях")
    def test_34d5e6f7_action_sequence_entropy_uniform(self):
        with autotest.step("Создаём 10 одинаковых действий"):
            events = EventSequenceData(10, action="start_node").events

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем энтропию = 0"):
            assert_equal(features.action_sequence_entropy, 0.0, "энтропия = 0")

    @autotest.num("535")
    @autotest.external_id("45e6f7a8-b9c0-4d1e-af2a-4b5c6d7e8f9a")
    @autotest.name("FeatureExtractor: высокая энтропия при разнообразных действиях")
    def test_45e6f7a8_action_sequence_entropy_diverse(self):
        actions = ["start_node", "stop_node", "create_link", "delete_link", "reload_node"]
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 10 событий с 5 разными action"):
            events = [
                EventData(id=f"e{i}", action=actions[i % len(actions)],
                         timestamp=now - timedelta(seconds=(10 - i) * 5))
                for i in range(10)
            ]

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем энтропию > 0.5"):
            assert_greater(features.action_sequence_entropy, 0.5, "энтропия > 0.5")

    @autotest.num("536")
    @autotest.external_id("56f7a8b9-c0d1-4e2f-8a3b-5c6d7e8f9a0b")
    @autotest.name("FeatureExtractor: подсчёт уникальных компонентов")
    def test_56f7a8b9_components_touched(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём события на 2 компонентах"):
            events = [
                EventData(id="e1", component_id="n1", timestamp=now - timedelta(seconds=20)),
                EventData(id="e2", component_id="n2", timestamp=now - timedelta(seconds=10)),
                EventData(id="e3", component_id="n1", timestamp=now),
            ]

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем components_touched = 2"):
            assert_equal(features.components_touched, 2, "2 уникальных компонента")

    @autotest.num("537")
    @autotest.external_id("67a8b9c0-d1e2-4f3a-9b4c-6d7e8f9a0b1c")
    @autotest.name("FeatureExtractor: частота ошибок в минуту")
    def test_67a8b9c0_error_frequency(self):
        now = datetime.now(tz=timezone.utc)
        with autotest.step("Создаём 5 ошибок за 5 минут"):
            events = [
                EventData(id=f"e{i}", event_type="error", action="err", success=False,
                         message=f"err-{i}", timestamp=now - timedelta(minutes=5 - i))
                for i in range(5)
            ]

        with autotest.step("Вычисляем фичи"):
            fe = FeatureExtractor()
            features = fe.compute("sess-1", events)

        with autotest.step("Проверяем error_frequency ~1/мин"):
            assert_greater_equal(features.error_frequency, 0.8, "частота >= 0.8/мин")
