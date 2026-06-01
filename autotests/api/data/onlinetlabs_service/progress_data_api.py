# Data-генераторы для progress-эндпоинтов.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator


class StepAttemptData(DataAbstractionGenerator):
    """Payload для POST .../steps/{step_slug}/attempt."""

    def __init__(self, result: str = "pass", score: float | None = 1.0,
                 error_details: dict | None = None):
        self.result = result
        self.score = score
        self.error_details = error_details
        self.data = {"result": result, "score": score, "error_details": error_details}
