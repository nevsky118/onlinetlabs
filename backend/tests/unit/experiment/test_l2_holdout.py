"""L2-холдаут: effective_arm форсирует OPEN при near-transfer переносе."""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.arm_resolver import effective_arm
from experiment.control_arm import ControlArm
from models.lab import Lab
from models.progress import LabProgress
from models.user import User

pytestmark = [pytest.mark.unit]

_SKILL = "static-ip-addressing"


class TestL2Holdout:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            # только нужные таблицы
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabProgress.__table__.create)

        async with self.session_factory() as db:
            # пользователь в CLOSED-плече
            db.add(User(id="u1", email="u1@test.local", control_arm="closed"))
            # L1: другая лаба того же навыка — уже пройдена
            db.add(Lab(slug="l1", title="L1", meta={"skill": _SKILL}))
            # L2: текущая лаба того же навыка — не пройдена
            db.add(Lab(slug="l2", title="L2", meta={"skill": _SKILL}))
            # лаба без навыка
            db.add(Lab(slug="no-skill", title="No skill", meta={}))
            # лаба другого навыка
            db.add(Lab(slug="other-skill", title="Other", meta={"skill": "routing"}))
            # прогресс: l1 завершена
            db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
            await db.commit()

        yield
        await self.engine.dispose()

    async def test_l2_holdout_forces_open_for_closed_arm_user(self):
        """CLOSED-пользователь получает OPEN на L2-холдауте."""
        async with self.session_factory() as db:
            arm = await effective_arm(db, "u1", "l2")
        assert arm == ControlArm.OPEN

    async def test_no_prior_completion_returns_base_arm(self):
        """Нет завершённой лабы того же навыка → базовое плечо (CLOSED).

        u2 не завершал ни одной лабы — l2 для него не L2-холдаут.
        """
        async with self.session_factory() as db:
            db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
            await db.commit()

        async with self.session_factory() as db:
            arm = await effective_arm(db, "u2", "l2")
        assert arm == ControlArm.CLOSED

    async def test_different_skill_returns_base_arm(self):
        """Другой навык — не L2-холдаут, возвращается базовое плечо."""
        async with self.session_factory() as db:
            arm = await effective_arm(db, "u1", "other-skill")
        assert arm == ControlArm.CLOSED

    async def test_lab_without_skill_returns_base_arm(self):
        """Лаба без skill-тега — не холдаут."""
        async with self.session_factory() as db:
            arm = await effective_arm(db, "u1", "no-skill")
        assert arm == ControlArm.CLOSED

    async def test_unknown_lab_returns_base_arm(self):
        """Несуществующая лаба — не падаем, возвращаем базовое плечо."""
        async with self.session_factory() as db:
            arm = await effective_arm(db, "u1", "ghost-lab")
        assert arm == ControlArm.CLOSED
