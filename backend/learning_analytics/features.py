"""FeatureExtractor — вычисление поведенческих фич из событий сессии."""

import math
from collections import Counter
from datetime import datetime, timezone

from agents.analytics.models import SessionFeatures
from config.config_model import LearningAnalyticsConfig


class FeatureExtractor:
    """Вычисление SessionFeatures из списка событий. Stateless."""

    def __init__(self, learning_analytics_config: LearningAnalyticsConfig | None = None):
        """Принимает LearningAnalyticsConfig для порогов; без него — дефолты."""
        self._config = learning_analytics_config or LearningAnalyticsConfig()

    def compute(self, session_id: str, events: list) -> SessionFeatures:
        """Основной метод: события → вектор фич."""
        now = datetime.now(tz=timezone.utc)
        if not events:
            return self._empty_features(session_id, now)

        sorted_events = sorted(events, key=lambda e: e.timestamp)
        action_events = [e for e in sorted_events if e.event_type == "action"]
        error_events = [e for e in sorted_events if e.event_type == "error"]

        latencies = self._inter_action_latencies(sorted_events)
        idle_gap = self._config.idle_gap_seconds
        max_consec_errors = self._max_consecutive_errors(sorted_events)

        return SessionFeatures(
            avg_inter_action_latency=round(
                sum(latencies) / len(latencies) if latencies else 0.0, 2
            ),
            action_rate_slope=round(self._action_rate_slope(sorted_events), 4),
            idle_periods=sum(1 for delta in latencies if delta > idle_gap),
            total_active_time=round(
                sum(delta for delta in latencies if delta <= idle_gap), 2
            ),
            time_on_current_step=round(
                self._time_on_current_step(sorted_events, now), 2
            ),
            error_repeat_count=max_consec_errors,
            error_repeat_rate=round(
                max_consec_errors / len(error_events)
                if error_events
                else 0.0,
                4,
            ),
            action_sequence_entropy=round(
                self._action_entropy(sorted_events), 4
            ),
            undo_redo_ratio=round(self._undo_redo_ratio(action_events), 4),
            error_frequency=round(
                self._error_frequency(error_events, sorted_events), 4
            ),
            error_frequency_slope=round(
                self._error_frequency_slope(error_events), 4
            ),
            unique_error_types=len(
                {e.message for e in error_events if e.message}
            ),
            dominant_error=self._dominant_error(error_events),
            components_touched=len(
                {e.component_id for e in sorted_events if e.component_id}
            ),
            action_diversity=round(
                len({e.action for e in sorted_events}) / len(sorted_events), 4
            ),
            events_total=len(sorted_events),
            session_id=session_id,
            computed_at=now,
        )

    # Приватные методы

    def _empty_features(self, session_id: str, now: datetime) -> SessionFeatures:
        """Нулевой вектор фич для пустой сессии."""
        return SessionFeatures(
            avg_inter_action_latency=0.0, action_rate_slope=0.0,
            idle_periods=0, total_active_time=0.0, time_on_current_step=0.0,
            error_repeat_count=0, error_repeat_rate=0.0,
            action_sequence_entropy=0.0, undo_redo_ratio=0.0,
            error_frequency=0.0, error_frequency_slope=0.0,
            unique_error_types=0, dominant_error=None,
            components_touched=0, action_diversity=0.0, events_total=0,
            session_id=session_id, computed_at=now,
        )

    @staticmethod
    def _inter_action_latencies(events: list) -> list[float]:
        """Интервалы между соседними событиями (сек)."""
        return [
            abs((events[i].timestamp - events[i - 1].timestamp).total_seconds())
            for i in range(1, len(events))
        ]

    def _action_rate_slope(self, events: list) -> float:
        """Slope линейной регрессии actions-per-window. Растёт = ускоряется."""
        if len(events) < 2:
            return 0.0
        total_span = (events[-1].timestamp - events[0].timestamp).total_seconds()
        window_seconds = self._config.rate_window_seconds
        min_windows = self._config.min_rate_windows
        if total_span < window_seconds * min_windows:
            return 0.0
        start_time = events[0].timestamp
        buckets: list[int] = []
        for event in events:
            bucket_index = int(
                (event.timestamp - start_time).total_seconds() / window_seconds
            )
            while len(buckets) <= bucket_index:
                buckets.append(0)
            buckets[bucket_index] += 1
        if len(buckets) < min_windows:
            return 0.0
        bucket_count = len(buckets)
        indices = list(range(bucket_count))
        index_mean = sum(indices) / bucket_count
        value_mean = sum(buckets) / bucket_count
        numerator = sum(
            (x - index_mean) * (y - value_mean)
            for x, y in zip(indices, buckets)
        )
        denominator = sum((x - index_mean) ** 2 for x in indices)
        return numerator / denominator if denominator else 0.0

    @staticmethod
    def _time_on_current_step(events: list, now: datetime) -> float:
        """Сек с момента последней смены component_id кластера."""
        if not events:
            return 0.0
        last_component = events[-1].component_id
        for i in range(len(events) - 2, -1, -1):
            if events[i].component_id != last_component:
                return (now - events[i + 1].timestamp).total_seconds()
        return (now - events[0].timestamp).total_seconds()

    @staticmethod
    def _max_consecutive_errors(events: list) -> int:
        """Макс. длина серии одинаковых ошибок подряд."""
        best_run = 0
        current_run = 1
        previous_message = None
        for event in events:
            if event.event_type != "error":
                continue
            if event.message == previous_message and previous_message is not None:
                current_run += 1
                best_run = max(best_run, current_run)
            else:
                current_run = 1
            previous_message = event.message
        return best_run

    @staticmethod
    def _action_entropy(events: list) -> float:
        """Нормализованная энтропия Шеннона по action-типам."""
        action_names = [event.action for event in events]
        if not action_names:
            return 0.0
        counts = Counter(action_names)
        total = len(action_names)
        entropy = -sum(
            (count / total) * math.log2(count / total)
            for count in counts.values()
            if count > 0
        )
        max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0

    @staticmethod
    def _undo_redo_ratio(action_events: list) -> float:
        """Доля start/stop/start циклов на одном компоненте."""
        if len(action_events) < 3:
            return 0.0
        cycle_count = sum(
            1
            for i in range(2, len(action_events))
            if action_events[i].component_id == action_events[i - 2].component_id
            and action_events[i].action == action_events[i - 2].action
            and action_events[i].action != action_events[i - 1].action
        )
        return cycle_count / len(action_events)

    def _error_frequency(self, error_events: list, all_events: list) -> float:
        """Ошибок/мин за последние N минут (из конфига)."""
        if not error_events or not all_events:
            return 0.0
        session_end = all_events[-1].timestamp
        session_start = all_events[0].timestamp
        duration_minutes = max(
            (session_end - session_start).total_seconds() / 60.0, 0.1
        )
        window_minutes = min(
            self._config.error_freq_window_minutes, duration_minutes
        )
        window_cutoff = session_end.timestamp() - window_minutes * 60
        recent_error_count = sum(
            1
            for event in error_events
            if event.timestamp.timestamp() >= window_cutoff
        )
        return recent_error_count / window_minutes

    @staticmethod
    def _error_frequency_slope(error_events: list) -> float:
        """Ускорение/замедление ошибок: rate 2й половины − rate 1й."""
        if len(error_events) < 4:
            return 0.0
        midpoint = len(error_events) // 2
        first_half = error_events[:midpoint]
        second_half = error_events[midpoint:]
        first_span = max(
            (first_half[-1].timestamp - first_half[0].timestamp).total_seconds(),
            1.0,
        )
        second_span = max(
            (second_half[-1].timestamp - second_half[0].timestamp).total_seconds(),
            1.0,
        )
        return len(second_half) / second_span - len(first_half) / first_span

    @staticmethod
    def _dominant_error(error_events: list) -> str | None:
        """Самая частая ошибка."""
        messages = [event.message for event in error_events if event.message]
        return Counter(messages).most_common(1)[0][0] if messages else None
