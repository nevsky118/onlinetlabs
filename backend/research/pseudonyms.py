"""Study pseudonyms: the only identifiers a research export is allowed to carry."""

from uuid import uuid4

from sqlalchemy import select

from models.session import LearningSession
from models.study_participant import StudyParticipant


async def pseudonym_for(db, user_id: str) -> str:
    """Returns the learner's study pseudonym, enrolling them on first use."""
    existing = (
        await db.execute(
            select(StudyParticipant.pseudonym).where(StudyParticipant.user_id == user_id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    participant = StudyParticipant(id=str(uuid4()), user_id=user_id, pseudonym=str(uuid4()))
    db.add(participant)
    await db.commit()
    return participant.pseudonym


async def pseudonym_map(db, user_ids) -> dict[str, str]:
    """user_id -> pseudonym for the given learners, enrolling any that are missing."""
    wanted = {u for u in user_ids if u}
    if not wanted:
        return {}
    rows = (
        await db.execute(
            select(StudyParticipant.user_id, StudyParticipant.pseudonym).where(
                StudyParticipant.user_id.in_(wanted)
            )
        )
    ).all()
    mapping = {user_id: pseudonym for user_id, pseudonym in rows}
    for user_id in wanted - set(mapping):
        mapping[user_id] = await pseudonym_for(db, user_id)
    return mapping


async def research_id_map(db, session_ids) -> dict[str, str]:
    """session_id -> research_id for the given sessions."""
    wanted = {s for s in session_ids if s}
    if not wanted:
        return {}
    rows = (
        await db.execute(
            select(LearningSession.id, LearningSession.research_id).where(
                LearningSession.id.in_(wanted)
            )
        )
    ).all()
    return {session_id: research_id for session_id, research_id in rows if research_id}
