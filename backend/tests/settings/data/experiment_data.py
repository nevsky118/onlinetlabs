# Генераторы тестовых данных для experiment.


class ExperimentMetricsData:
    """Генерирует duck-typed ExperimentMetrics."""

    def __init__(self, group: str, time: float, errors: int, repeated: int, interventions: int = 0):
        self.experiment_group = group
        self.total_time_seconds = time
        self.total_errors = errors
        self.repeated_errors = repeated
        self.interventions_received = interventions
        self.steps_completed = 5
        self.final_score = 100.0
        self.completed = True
