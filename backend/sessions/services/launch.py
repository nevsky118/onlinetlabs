import logging

from sqlalchemy import func, select

from experiment.assignment import assign_experiment_group_if_needed
from models.lab import Lab
from models.session import LearningSession
from security.secrets import decrypt_secret, encrypt_secret
from sessions.services.proxy import existing_gns3_deep_url, existing_gns3_url
from sessions.services.query import get_active_session

logger = logging.getLogger(__name__)

MAX_CONCURRENT_SESSIONS_PER_USER = 2


async def count_active_sessions(db, user_id: str) -> int:
    """Считает активные и провижинящиеся сессии пользователя."""
    result = await db.execute(
        select(func.count(LearningSession.id)).where(
            LearningSession.user_id == user_id,
            LearningSession.status.in_(("active", "provisioning")),
        )
    )
    return int(result.scalar_one() or 0)


async def _create_provisioning_row(db_factory, user_id: str, lab_slug: str):
    """Создаёт строку сессии в статусе provisioning в отдельной транзакции."""
    async with db_factory() as db:
        await assign_experiment_group_if_needed(db, user_id)
        session = LearningSession(user_id=user_id, lab_slug=lab_slug, status="provisioning")
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session


async def _finalize_session_row(db_factory, session_id: str, status: str, meta: dict | None):
    """Обновляет статус и метаданные сессии после провижининга."""
    async with db_factory() as db:
        session = await db.get(LearningSession, session_id)
        session.status = status
        if meta is not None:
            session.meta = meta
        await db.commit()
        await db.refresh(session)
        return session


async def launch_session(
    db, user_id: str, lab_slug: str, gns3_client, db_factory
) -> tuple[LearningSession, dict]:
    """Запускает сессию лабораторной.

    Возвращает существующую активную сессию или создаёт новую через провижининг
    GNS3, проверяя лимит одновременных сессий и наличие шаблона лабораторной.
    """
    existing = await get_active_session(db, user_id, lab_slug)
    if existing:
        meta = existing.meta or {}
        return existing, {
            "gns3_username": meta["gns3_username"],
            "gns3_password": decrypt_secret(meta["enc_password"]),
            "gns3_url": existing_gns3_url(existing),
            "gns3_deep_url": existing_gns3_deep_url(existing),
        }

    active_count = await count_active_sessions(db, user_id)
    if active_count >= MAX_CONCURRENT_SESSIONS_PER_USER:
        raise ValueError(
            f"Достигнут лимит активных сессий ({MAX_CONCURRENT_SESSIONS_PER_USER}). "
            "Заверши одну из текущих перед запуском новой."
        )

    lab = await db.get(Lab, lab_slug)
    if lab is None:
        raise ValueError("Lab не найдена")

    if not lab.enabled:
        raise ValueError("Лаба отключена")

    if lab_slug.endswith("-ccna"):
        template_pid = lab.gns3_template_project_id_iosvl2
        if not template_pid:
            raise ValueError(
                f"Lab '{lab_slug}' требует IOSvL2 template, но он не настроен "
                "(deploy на x86_64 production host)"
            )
    elif lab_slug.endswith("-frr"):
        template_pid = getattr(lab, "gns3_template_project_id_frr", None)
        if not template_pid:
            raise ValueError(f"Lab '{lab_slug}' не имеет настроенного template")
    else:
        template_pid = lab.gns3_template_project_id
        if not template_pid:
            raise ValueError(f"Lab '{lab_slug}' не имеет gns3_template_project_id")

    # Прод-сценарий split-tx. Отпускаем DB-транзакцию на время вызова gns3.
    session = await _create_provisioning_row(db_factory, user_id, lab_slug)
    try:
        result = await gns3_client.create_session(user_id, template_pid)
    except Exception:
        await _finalize_session_row(db_factory, str(session.id), "error", None)
        logger.exception("Провижининг GNS3 упал для сессии %s", session.id)
        raise

    meta = {
        "gns3_service_session_id": result["session_id"],
        "gns3_user_id": result["gns3_user_id"],
        "gns3_username": result["gns3_username"],
        "gns3_project_id": result["project_id"],
        "enc_password": encrypt_secret(result["gns3_password"]),
        "enc_jwt": encrypt_secret(result["gns3_jwt"]),
    }
    session = await _finalize_session_row(db_factory, str(session.id), "active", meta)

    return session, {
        "gns3_username": result["gns3_username"],
        "gns3_password": result["gns3_password"],
        "gns3_url": existing_gns3_url(session),
        "gns3_deep_url": existing_gns3_deep_url(session),
    }
