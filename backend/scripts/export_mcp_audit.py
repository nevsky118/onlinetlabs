"""Выгрузка сводки mcp_audit по сессиям (observe/act/отказы)."""
import asyncio

from models.mcp_audit import MCPAudit  # проверяем зависимость без env
from sqlalchemy import func, select


async def main():
    # Ленивый импорт: db.session тянет config, который требует env-файл
    from db.session import async_session  # noqa: PLC0415

    async with async_session() as db:
        rows = (await db.execute(
            select(
                MCPAudit.session_id,
                MCPAudit.kind,
                MCPAudit.success,
                func.count().label("n"),
            ).group_by(MCPAudit.session_id, MCPAudit.kind, MCPAudit.success)
            .order_by(MCPAudit.session_id, MCPAudit.kind)
        )).all()

    # Свернуть в session_id → {observe_ok, observe_deny, act_ok, act_deny}
    sessions: dict[str, dict[str, int]] = {}
    for row in rows:
        sid = row.session_id
        if sid not in sessions:
            sessions[sid] = {"observe_ok": 0, "observe_deny": 0, "act_ok": 0, "act_deny": 0}
        key = f"{row.kind}_{'ok' if row.success else 'deny'}"
        sessions[sid][key] = row.n

    print("# MCP Audit — сводка по сессиям\n")
    print("| session_id | observe | observe_deny | act | act_deny |")
    print("|-|-|-|-|-|")
    for sid, c in sessions.items():
        print(f"| {sid[:12]}… | {c['observe_ok']} | {c['observe_deny']} | {c['act_ok']} | {c['act_deny']} |")

    total_act = sum(c["act_ok"] for c in sessions.values())
    total_deny = sum(c["observe_deny"] + c["act_deny"] for c in sessions.values())
    print(f"\n_Итого ACT-воздействий: {total_act}. Итого отказов: {total_deny}._")


if __name__ == "__main__":
    asyncio.run(main())
