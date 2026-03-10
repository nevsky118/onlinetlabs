"""ValidatorAgent — проверка выполнения задач лабы."""

from config.config_model import ConfigModel
from agents.base import BaseAgent
from agents.validator.models import CheckResult, ValidationInput, ValidationResult
from agents.validator.tools import ValidatorTools


class ValidatorAgent(BaseAgent):
    """Агент для валидации выполнения шагов лабы."""

    def __init__(self, config: ConfigModel, mcp_client):
        self.tools = ValidatorTools(mcp_client)
        super().__init__(config)

    def system_prompt(self) -> str:
        return (
            "Ты — ValidatorAgent, агент для проверки выполнения лабораторных задач. "
            "Твоя роль: проверить состояние компонентов среды против ожидаемых критериев, "
            "выставить оценку и дать обратную связь. "
            "Будь объективен и точен."
        )

    async def run(self, input_data: ValidationInput) -> ValidationResult:
        """Запустить проверки по критериям и вернуть результат."""
        checks: list[CheckResult] = []

        for criterion in input_data.criteria:
            component_id = criterion["component_id"]
            expected_status = criterion["expected_status"]
            check = await self.tools.check_component_status(
                input_data, component_id, expected_status
            )
            checks.append(check)

        passed_count = sum(1 for c in checks if c.passed)
        total = len(checks)
        score = (passed_count / total * 100.0) if total > 0 else 0.0
        all_passed = all(c.passed for c in checks)

        feedback = (
            "Все проверки пройдены."
            if all_passed
            else f"Пройдено {passed_count}/{total} проверок."
        )

        return ValidationResult(
            passed=all_passed,
            score=score,
            checks=checks,
            feedback=feedback,
        )
