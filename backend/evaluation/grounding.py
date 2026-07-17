"""Grounded-vs-ungrounded ablation: генерация пары помощи + запись для оценки."""
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.grounding_comparison import GroundingComparison


def _hint_text(response) -> str:
    """Извлечь текст помощи из OrchestratorResponse."""
    data = response.data or {}
    return data.get("hint") or data.get("text") or ""


async def generate_grounding_pair(orchestrator, grounded_input, ungrounded_input) -> tuple[str, str]:
    """Сгенерировать пару помощи: с живым MCP-контекстом vs только текст задачи.

    Два вызова одного orchestrator на один триггер — метрика заземления, не
    вычислимая из правил (иммунна к тавтологии F1). Дорого → gated в вызывающем коде.
    """
    grounded = await orchestrator.intervene(grounded_input)
    ungrounded = await orchestrator.intervene(ungrounded_input)
    return _hint_text(grounded), _hint_text(ungrounded)


async def record_grounding_comparison(
    db: AsyncSession, session_id: str, grounded_text: str, ungrounded_text: str
) -> None:
    """Сохранить пару для слепой экспертной оценки (перемешивание — на экспорте)."""
    db.add(GroundingComparison(
        session_id=session_id, grounded_text=grounded_text,
        ungrounded_text=ungrounded_text, ts=datetime.now(tz=UTC),
    ))
    await db.commit()
