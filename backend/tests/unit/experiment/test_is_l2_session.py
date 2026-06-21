"""is_l2_session: True при предшествующей завершённой лабе того же навыка."""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.arm_resolver import is_l2_session
from models.lab import Lab
from models.progress import LabProgress
from models.user import User

pytestmark = [pytest.mark.unit]

_SKILL = "static-ip-addressing"


class TestIsL2Session:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabProgress.__table__.create)

        async with self.session_factory() as db:
            db.add(User(id="u1", email="u1@test.local", control_arm="closed"))
            db.add(Lab(slug="l1", title="L1", meta={"skill": _SKILL}))
            db.add(Lab(slug="l2", title="L2", meta={"skill": _SKILL}))
            db.add(Lab(slug="no-skill", title="No skill", meta={}))
            db.add(Lab(slug="other-skill", title="Other", meta={"skill": "routing"}))
            # l1 завершена пользователем
            db.add(LabProgress(id="p1", user_id="u1", lab_slug="l1", status="completed"))
            await db.commit()

        yield
        await self.engine.dispose()

    async def test_returns_true_when_prior_same_skill_completed(self):
        """True: есть пройденная l1 того же навыка для текущей l2."""
        async with self.session_factory() as db:
            result = await is_l2_session(db, "u1", "l2")
        assert result is True

    async def test_returns_false_when_no_prior_completion(self):
        """False: пользователь без завершённых лаб."""
        async with self.session_factory() as db:
            db.add(User(id="u2", email="u2@test.local", control_arm="closed"))
            await db.commit()

        async with self.session_factory() as db:
            result = await is_l2_session(db, "u2", "l2")
        assert result is False

    async def test_returns_false_for_different_skill(self):
        """False: завершённая лаба другого навыка не считается L2-холдаутом."""
        async with self.session_factory() as db:
            result = await is_l2_session(db, "u1", "other-skill")
        assert result is False

    async def test_returns_false_for_lab_without_skill(self):
        """False: лаба без skill-тега не является L2."""
        async with self.session_factory() as db:
            result = await is_l2_session(db, "u1", "no-skill")
        assert result is False

    async def test_returns_false_for_unknown_lab(self):
        """False: несуществующая лаба не падает, возвращает False."""
        async with self.session_factory() as db:
            result = await is_l2_session(db, "u1", "ghost-lab")
        assert result is False
