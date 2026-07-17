"""Grounded-vs-ungrounded ablation: generating a hint pair + recording it for evaluation."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.grounding_comparison import GroundingComparison


def _hint_text(response) -> str:
    """Extract the hint text from OrchestratorResponse."""
    data = response.data or {}
    return data.get("hint") or data.get("text") or ""


async def generate_grounding_pair(
    orchestrator, grounded_input, ungrounded_input
) -> tuple[str, str]:
    """Generate a hint pair: with live MCP context vs task text only.

    Two calls to the same orchestrator for one trigger. A grounding metric
    not computable from rules (immune to the F1 tautology). Expensive -> gated
    in the calling code.
    """
    grounded = await orchestrator.intervene(grounded_input)
    ungrounded = await orchestrator.intervene(ungrounded_input)
    return _hint_text(grounded), _hint_text(ungrounded)


async def record_grounding_comparison(
    db: AsyncSession, session_id: str, grounded_text: str, ungrounded_text: str
) -> None:
    """Save the pair for blind expert evaluation (shuffling happens at export)."""
    db.add(
        GroundingComparison(
            session_id=session_id,
            grounded_text=grounded_text,
            ungrounded_text=ungrounded_text,
            ts=datetime.now(tz=UTC),
        )
    )
    await db.commit()
