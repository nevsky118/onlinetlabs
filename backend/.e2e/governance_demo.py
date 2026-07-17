"""Демо governance Задачи 7: ControlInterface-шов на реальной БД.

MCP замокан (демонстрируем ГЕЙТЫ контура, не GNS3). Согласие/изоляция/аудит — реальная БД.
Показывает: какой вызов проходит, какой отклонён и почему, и журнал аудита.
"""
import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, select

from config.env_config_loader import load_settings
from control_interface.consent import grant
from control_interface.interface import ControlInterface, InterfaceDenied
from db.session import async_session
from experiment.assignment import ControlArm
from models.mcp_audit import MCPAudit
from models.session import LearningSession
from models.user import User

PREFIX = "gov-demo-"


class _FakeMCP:
    """Заглушка MCP: гейты контура реальны, сам вызов — фейк (без GNS3)."""
    async def _call_tool(self, name, arguments):
        return [{"ok": name}]

    async def execute_action(self, ctx, action_name, params):
        return {"ok": action_name}


async def run():
    ci = ControlInterface(_FakeMCP(), async_session, load_settings().learning_analytics)
    u1, s1 = f"{PREFIX}u1", f"{PREFIX}s1"   # согласие есть, владелец s1
    u2, s2 = f"{PREFIX}u2", f"{PREFIX}s2"   # согласия нет, владелец s2

    async with async_session() as db:
        db.add(User(id=u1, name=u1, email=f"{u1}@demo.local", role="student", control_arm="closed"))
        db.add(User(id=u2, name=u2, email=f"{u2}@demo.local", role="student", control_arm="closed"))
        await db.commit()  # юзеры до сессий (FK)
        db.add(LearningSession(id=s1, user_id=u1, lab_slug="lan-static-ip", status="active",
                               started_at=datetime.now(UTC)))
        db.add(LearningSession(id=s2, user_id=u2, lab_slug="lan-static-ip", status="active",
                               started_at=datetime.now(UTC)))
        await db.commit()
        await grant(db, u1, "study", observe=True, act=True)   # study покрывает observe+act

    async def _try(label, coro):
        try:
            await coro
            print(f"  ✓ ПРОПУЩЕН   | {label}")
        except InterfaceDenied as e:
            print(f"  ✗ ОТКЛОНЁН   | {label}  → reason={e.reason}")

    print("\n=== Демонстрация гейтов контура (ControlInterface) ===")
    await _try("observe list_user_actions (u1, своя сессия, согласие)",
               ci.observe("list_user_actions", {}, {}, user_id=u1, session_id=s1, lab_slug="lan-static-ip"))
    await _try("act execute_action (u1, closed-плечо, согласие)",
               ci.act("execute_action", {}, {"action_name": "ping", "params": {}}, user_id=u1, session_id=s1, arm=ControlArm.CLOSED))
    await _try("act execute_action (u1, OPEN-плечо — проактив подавлен)",
               ci.act("execute_action", {}, {"action_name": "ping"}, user_id=u1, session_id=s1, arm=ControlArm.OPEN))
    await _try("act execute_action (u1, повтор сразу — rate-backstop = cooldown)",
               ci.act("execute_action", {}, {"action_name": "ping"}, user_id=u1, session_id=s1, arm=ControlArm.CLOSED))
    await _try("observe (u2, своя сессия, НО без согласия)",
               ci.observe("list_user_actions", {}, {}, user_id=u2, session_id=s2))
    await _try("observe (u1 пытается читать ЧУЖУЮ сессию s2 — изоляция)",
               ci.observe("list_user_actions", {}, {}, user_id=u1, session_id=s2))
    await _try("observe неклассифицированный инструмент rm_rf_all (default-deny)",
               ci.observe("rm_rf_all", {}, {}, user_id=u1, session_id=s1))

    async with async_session() as db:
        rows = (await db.execute(
            select(MCPAudit).where(MCPAudit.user_id.like(f"{PREFIX}%")).order_by(MCPAudit.ts)
        )).scalars().all()
    print(f"\n=== Журнал аудита mcp_audit ({len(rows)} записей; append-only) ===")
    print("| kind | tool | success | reason(error) |")
    print("|-|-|-|-|")
    for r in rows:
        print(f"| {r.kind} | {r.tool} | {r.success} | {r.error or '—'} |")


async def cleanup():
    async with async_session() as db:
        await db.execute(delete(MCPAudit).where(MCPAudit.user_id.like(f"{PREFIX}%")))
        await db.execute(delete(User).where(User.id.like(f"{PREFIX}%")))
        await db.commit()
    print("=== gov-demo удалены ===")


if __name__ == "__main__":
    import sys
    asyncio.run(cleanup() if (len(sys.argv) > 1 and sys.argv[1] == "clean") else run())
