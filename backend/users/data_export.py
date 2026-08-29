"""Subject access: everything held about one learner, and its erasure."""

from sqlalchemy import delete, select

from admin.data_registry import ADMIN_TABLES, serialize_row
from models.identity import User
from models.learning import LearningSession

# Deleted last: other tables reference them.
_DEFERRED = ("learning_sessions", "study_participants")


def subject_filter(model, user_id: str, session_ids: list[str]):
    """Condition selecting one learner's rows, or None when the table cannot say."""
    if hasattr(model, "user_id"):
        return model.user_id == user_id
    if hasattr(model, "session_id"):
        if not session_ids:
            return None
        return model.session_id.in_(session_ids)
    return None


def unattributable_tables() -> list[str]:
    """Registry tables that neither export nor erasure can reach."""
    return [
        name
        for name, spec in ADMIN_TABLES.items()
        if not hasattr(spec.model, "user_id") and not hasattr(spec.model, "session_id")
    ]


async def _session_ids(db, user_id: str) -> list[str]:
    """The learner's session ids, which key the tables that have no user_id."""
    rows = (
        await db.execute(select(LearningSession.id).where(LearningSession.user_id == user_id))
    ).all()
    return [r[0] for r in rows]


async def collect_subject_data(db, user_id: str) -> dict:
    """Every registry table's rows for this learner, serialized."""
    session_ids = await _session_ids(db, user_id)
    out: dict[str, list[dict]] = {}
    for name, spec in ADMIN_TABLES.items():
        condition = subject_filter(spec.model, user_id, session_ids)
        if condition is None:
            out[name] = []
            continue
        rows = (await db.execute(select(spec.model).where(condition))).scalars().all()
        out[name] = [serialize_row(spec, row) for row in rows]
    return out


async def erase_subject(db, user_id: str, *, delete_account: bool = True) -> dict[str, int]:
    """Deletes every registry row for this learner. Returns rows removed per table."""
    session_ids = await _session_ids(db, user_id)
    removed: dict[str, int] = {}

    for name, spec in ADMIN_TABLES.items():
        if name in _DEFERRED:
            continue
        condition = subject_filter(spec.model, user_id, session_ids)
        if condition is None:
            removed[name] = 0
            continue
        result = await db.execute(delete(spec.model).where(condition))
        removed[name] = result.rowcount or 0

    for name in _DEFERRED:
        spec = ADMIN_TABLES[name]
        condition = subject_filter(spec.model, user_id, session_ids)
        if condition is None:
            removed[name] = 0
            continue
        result = await db.execute(delete(spec.model).where(condition))
        removed[name] = result.rowcount or 0

    if delete_account:
        result = await db.execute(delete(User).where(User.id == user_id))
        removed["users"] = result.rowcount or 0

    await db.commit()
    return removed
