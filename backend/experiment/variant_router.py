"""Маршрутизация интервенций по экспериментальным вариантам."""

from sqlalchemy import select

from agents.orchestrator.models import InterventionInput, OrchestratorResponse
from experiment.assignment import (
    AgentBackend,
    ExperimentGroup,
    assign_group,
    backend_for_group,
    parse_experiment_group,
)
from models.user import User


# TODO: wire the B-arm into monitor_registry (currently only tests construct it)
class ExperimentVariantRouter:
    """Маршрутизирует интервенции в бэкенд, назначенный группе эксперимента."""

    def __init__(self, orchestrator, openclaw_adapter, db_factory=None):
        self._orchestrator = orchestrator
        self._openclaw_adapter = openclaw_adapter
        self._db_factory = db_factory

    async def intervene(self, input_data: InterventionInput) -> OrchestratorResponse:
        """Определить постоянную группу пользователя и выполнить маршрутизацию."""
        group = await self._resolve_group(input_data.user_id)
        return await self.route(input_data, group)

    async def route(
        self, input_data: InterventionInput, group: str | ExperimentGroup
    ) -> OrchestratorResponse:
        """Маршрутизировать интервенцию для известной группы эксперимента."""
        parsed_group = parse_experiment_group(group)
        backend = backend_for_group(parsed_group)

        if backend == AgentBackend.MULTI_AGENT:
            response = await self._orchestrator.intervene(input_data)
            return self._tag_response(response, parsed_group, backend)

        response = await self._openclaw_adapter.generate(input_data)
        return self._tag_response(response, parsed_group, backend)

    async def _resolve_group(self, user_id: str) -> ExperimentGroup:
        """Получить или назначить постоянную группу пользователя."""
        if self._db_factory is None:
            return ExperimentGroup.GROUP_A

        async with self._db_factory() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError(f"User not found for experiment assignment: {user_id}")
            if user.experiment_group in {
                ExperimentGroup.GROUP_A,
                ExperimentGroup.GROUP_B,
            }:
                return parse_experiment_group(user.experiment_group)

            group = assign_group()
            user.experiment_group = group.value
            await session.commit()
            return group

    @staticmethod
    def _tag_response(
        response: OrchestratorResponse,
        group: ExperimentGroup,
        backend: AgentBackend,
    ) -> OrchestratorResponse:
        """Добавить метаданные эксперимента, сохранив ответ бэкенда."""
        metadata = dict(response.metadata)
        metadata["experiment_group"] = group.value
        metadata["agent_backend"] = backend.value
        return response.model_copy(
            update={
                "agent_backend": response.agent_backend or backend.value,
                "metadata": metadata,
            }
        )
