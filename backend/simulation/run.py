"""CLI: run a sim cohort on the LIVE stack (real GNS3, pool+queue).

Requires the stack to be up: `make up-db` (root) + the gns3 stack (`cd gns3 && docker compose up -d`).
_live_provision assembles live deps the same way the app does (main.py lifespan / deps.py):
mcp_client / gateway / orchestrator / gns3_client / monitor_registry, then
launch_session → build_session_context → monitor_registry.start → GNS3Actor from node_ids.

FIREWALL: all users are is_simulated=True; data is cut off from the reproducibility
bundle. To remove: `rm -rf backend/simulation` + `DELETE FROM users WHERE is_simulated`.

Run: `ENV_FILE=../deployment/local/backend.env poetry run python -m simulation.run --n 3 --concurrency 2`
"""

import argparse
import asyncio
from datetime import UTC

from simulation.ground_truth import record_truth
from simulation.orchestrator import run_cohort

# YandexGPT price (rub/1k tokens) — verify against the current rate; budget 500 rub.
_PRICE_PER_1K_RUB = 1.20
_BUDGET_RUB = 500.0

# Waiting for a queue slot (GLOBAL_CAP=50 concurrent sessions).
_QUEUE_ACQUIRE_TRIES = 90
_QUEUE_ACQUIRE_WAIT_SEC = 2.0

# Pause after starting nodes: VPCS doesn't bring the console up instantly.
_CONSOLE_WARMUP_SEC = 6.0


def _build_deps():
    """Live app dependencies (1:1 with main.py lifespan)."""
    from config import settings

    # MRT-track instruments are off by default (gated-off). The sim exists to
    # exercise them: enable decision-log/evidence/latency on the live loop.
    settings.learning_analytics.mrt_enabled = True
    settings.learning_analytics.evidence_capture_enabled = True
    settings.learning_analytics.latency_capture_enabled = True
    # Time compression: a sim session is ~40s vs minutes for a live student. The idle
    # detector is tuned for real time (idle_gap=60s) → in a compressed run idle
    # periods never accumulate. We scale it for the sim so idle pauses register and
    # struggle gets detected (de-risking the decision-log instrument; NOT detector validation).
    settings.learning_analytics.idle_gap_seconds = 0.5
    settings.learning_analytics.idle_threshold = 2
    settings.learning_analytics.rate_slope_threshold = 1.0
    # LabProgressObserver only emits events from the SECOND cycle onward (the first
    # is the baseline snapshot). At the 25s default a compressed sim session never reaches
    # a second cycle — spec checks never turn into check_failing, and the detector goes blind.
    settings.learning_analytics.progress_poll_interval = 6.0
    from agents.orchestrator.agent import Orchestrator
    from db.session import async_session
    from gns3_service_client import Gns3ServiceClient
    from mcp_client.client import MCPClient
    from observability.activity import AgentActivityLog
    from sessions.monitor_registry import SessionMonitorRegistry
    from sessions.ws import WebSocketGateway

    mcp_client = MCPClient(settings.mcp.server_url)
    gateway = WebSocketGateway()
    orchestrator = Orchestrator(settings, mcp_client=mcp_client)
    gns3_client = Gns3ServiceClient(
        settings.gns3.service_url, internal_token=settings.security.internal_api_token
    )
    activity_log = AgentActivityLog(async_session, settings.observability.retention_per_session)
    monitor_registry = SessionMonitorRegistry(
        config=settings,
        mcp_client=mcp_client,
        db_factory=async_session,
        orchestrator=orchestrator,
        gateway=gateway,
        activity_log=activity_log,
        gns3_client=gns3_client,
    )
    return settings, gns3_client, monitor_registry


def _console_host(node: dict) -> str:
    """Console host: container loopback addresses are unreachable from the host →
    localhost. The gns3-server console range is published (see gns3/docker-compose.yml)."""
    host = (node.get("console_host") or "").strip()
    if not host or host in ("0.0.0.0", "::", "127.0.0.1", "localhost"):
        return "localhost"
    return host


def _make_provision(settings, gns3_client, monitor_registry, lab_slug, tutor_reply):
    from chat.persistence import save_assistant_message, save_user_message
    from control_interface.consent import grant as grant_consent
    from db.session import async_session
    from sessions.context import build_session_context
    from sessions.queue import _get_or_create_singleton as _get_or_create_queue
    from sessions.service import launch_session
    from simulation.env.gns3_actor import GNS3Actor
    from simulation.help_text import HelpTextGen
    from simulation.lab_config import build_node_tasks
    from validation.runner import load_lab_spec

    async def provision(profile, seed, user_id):
        # The sim user must have study-consent, otherwise the seam cuts observe → empty pipeline.
        async with async_session() as db:
            await grant_consent(db, user_id, scope="study", observe=True, act=True)

        # Take a queue slot like a real student: end_lab on completion does a
        # release (raw DECR), so without acquire the capacity counters would go negative.
        queue = _get_or_create_queue()
        acquired = False
        for _ in range(_QUEUE_ACQUIRE_TRIES):
            if await queue.try_acquire(user_id, lab_slug):
                acquired = True
                break
            await asyncio.sleep(_QUEUE_ACQUIRE_WAIT_SEC)
        if not acquired:
            raise RuntimeError(f"слот очереди не получен за {_QUEUE_ACQUIRE_TRIES} попыток")

        try:
            async with async_session() as db:
                session, _creds = await launch_session(
                    db, user_id, lab_slug, gns3_client, db_factory=async_session
                )
        except Exception:
            await queue.release(lab_slug)  # provision failed → the slot must not leak
            raise
        if session.status != "active":
            await queue.release(lab_slug)
            raise RuntimeError(f"сессия не active: {session.status}")
        ctx = build_session_context(session)
        await monitor_registry.start(session.id, session.user_id, session.lab_slug, ctx)

        gsess = (session.meta or {})["gns3_service_session_id"]

        # Nodes must be RUNNING: spec checks read config via the console, and a
        # stopped node has no console → checks hang and the detector goes blind.
        await gns3_client.bulk_node_action(gsess, "start")
        await asyncio.sleep(_CONSOLE_WARMUP_SEC)

        state = await gns3_client.get_state(gsess)
        consoles = {
            n["name"]: (_console_host(n), n["console"])
            for n in state.get("nodes", [])
            if n.get("console")
        }
        node_tasks = build_node_tasks(load_lab_spec(lab_slug) or {})

        help_gen = HelpTextGen(
            llm_enabled=settings.learning_analytics.sim_llm_help_enabled,
            budget_rub=_BUDGET_RUB,
            price_per_1k_rub=_PRICE_PER_1K_RUB,
        )
        actor = GNS3Actor(
            node_tasks=node_tasks,
            consoles=consoles,
            db_factory=async_session,
            backend_session_id=str(session.id),
            help_gen=help_gen,
            profile=profile,
            save_user_message=save_user_message,
            save_assistant_message=save_assistant_message,
            tutor_reply=tutor_reply,
        )
        return str(session.id), actor

    return provision


def _make_finalize(lab_slug, l2_lab, gns3_client, monitor_registry, settle_sec: float = 12.0):
    """Full study protocol: L1 (assisted) → L2 (near-transfer, WITHOUT assistance).
    l2_lab is a pair of the same skill (or None → L1 only, if the skill has no pair).

    L1 closes via the SAME path as a real student — `end_lab`: stop the monitor →
    ExperimentMetrics + MRT censoring → teardown GNS3 → release the queue slot.
    L2 is a synthetic transfer session (no GNS3/monitor/slot), so `end_session`:
    only measurements are taken.

    INTEGRITY: L2-pass is modeled ONLY from the student's skill, WITHOUT a baked-in
    arm effect (otherwise it's a "seeded A/B"). Arms should come out ≈equal on l2_pass — an honest null for the simulation.
    is_simulated data is cut off from the reproducibility bundle."""
    from datetime import datetime
    from uuid import uuid4

    from db.session import async_session
    from models.progress import LabProgress
    from models.session import LearningSession
    from sessions.services.lifecycle import end_lab, end_session
    from validation.runner import load_lab_spec

    def _total(slug):
        spec = load_lab_spec(slug)
        return len(spec.get("steps", [])) if spec else 2

    total1 = _total(lab_slug)
    total2 = _total(l2_lab) if l2_lab else 0

    async def _write_progress(user_id, lab, steps, total, started, completed_at) -> bool:
        """We write LabProgress BEFORE finalization: metrics read steps_completed from it."""
        completed = steps >= total
        async with async_session() as db:
            db.add(
                LabProgress(
                    id=str(uuid4()),
                    user_id=user_id,
                    lab_slug=lab,
                    current_step=steps,
                    status="completed" if completed else "in_progress",
                    score=round(steps / total * 100.0, 1) if total else 0.0,
                    started_at=started,
                    completed_at=completed_at if completed else None,
                )
            )
            await db.commit()
        return completed

    async def finalize(session_id, user_id, profile, state):
        from datetime import timedelta

        now = datetime.now(UTC)
        # Timestamps: L1 before L2, positive duration within the cohort's horizon.
        l1_start, l1_end = now - timedelta(minutes=14), now - timedelta(minutes=9)
        l2_start, l2_end = now - timedelta(minutes=6), now - timedelta(minutes=1)

        # L1 (assisted by the live monitor): almost everyone completes.
        l1_steps = total1 if profile.skill > 0.2 else max(0, total1 - 1)
        l1_done = await _write_progress(user_id, lab_slug, l1_steps, total1, l1_start, l1_end)

        # A live student doesn't close the lab the same millisecond they stop
        # acting: the monitor has time to pick up trailing events (poll_interval=5s)
        # and intervene if needed. In a compressed run we give it that time explicitly
        # — otherwise end_lab kills the monitor before events arrive from GNS3 history.
        await asyncio.sleep(settle_sec)

        async with async_session() as db:
            await end_lab(db, session_id, user_id, gns3_client, monitor_registry)

        if not l1_done or not l2_lab:
            return  # no completed L1, or the skill has no near-transfer pair → L1 only

        # L2 (near-transfer, WITHOUT assistance): pass ⇐ skill (higher threshold — harder without help).
        l2_steps = total2 if profile.skill > 0.5 else max(0, total2 - 1)
        async with async_session() as db:
            l2 = LearningSession(
                id=str(uuid4()),
                user_id=user_id,
                lab_slug=l2_lab,
                status="active",
                started_at=l2_start,
            )
            db.add(l2)
            await db.commit()
            l2_id = str(l2.id)
        await _write_progress(user_id, l2_lab, l2_steps, total2, l2_start, l2_end)
        async with async_session() as db:
            await end_session(db, l2_id, user_id, status="completed")

    return finalize


def _make_tutor_reply(settings, lab_slug):
    """Tutor's reply for the chat log: LLM (short timeout) → progressive template fallback.

    The fallback MUST depend on the attempt number: previously the template was chosen
    as `len(question) % N`, and the question was constant → the tutor repeated the exact
    same answer verbatim, and the dialogue looped. A live tutor escalates gradually:
    first clarifying, then hinting, and only then giving specifics (like HintAgent's levels).
    """
    import asyncio as _asyncio

    from core.llm.client import build_client, model_uri

    model = settings.agents.chat_model

    def _fallback(context: dict) -> str:
        attempt = int(context.get("attempt", 0))
        node = context.get("node") or "узле"
        tried = context.get("tried")
        tried_part = f"Ты ввёл `{tried}`. " if tried else ""

        stages = [
            # 1. Clarification — the tutor doesn't give the answer right away.
            f"Расскажи, что показывает `show ip` на {node}? "
            "Сверим то, что применилось, с тем, что требует задание.",
            # 2. Hint toward the error class.
            f"{tried_part}Сравни третий октет своего адреса с планом лабы: "
            f"похоже, {node} оказался в другой подсети, поэтому проверка и не проходит.",
            # 3. Concrete mechanics.
            f"На {node} задай адрес из нужной подсети командой `ip <адрес>/<маска>` "
            "и проверь результат через `show ip` — маска должна совпасть с заданием.",
            # 4. Direct hint after several failures.
            f"{tried_part}Адрес не из той сети. Возьми подсеть из условия шага и "
            f"назначь {node} адрес внутри неё — после этого проверка станет зелёной.",
        ]
        return stages[min(attempt, len(stages) - 1)]

    async def reply(question: str, context: dict) -> str:
        attempt = int(context.get("attempt", 0))
        node = context.get("node") or "узле"
        tried = context.get("tried")
        tried_part = f" Студент ввёл команду `{tried}`." if tried else ""
        try:
            # max_retries=0: yandex may be unreachable → instant fallback to the template.
            client = build_client(model).with_options(max_retries=0, timeout=6)
            resp = await _asyncio.wait_for(
                client.chat.completions.create(
                    model=model_uri(model),
                    stream=False,
                    max_tokens=180,
                    temperature=0.6,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Ты — тьютор по компьютерным сетям в лабе GNS3. Отвечай кратко "
                                "(2-3 предложения), по-русски. Веди студента по нарастающей: "
                                "сначала уточняй и наводи, конкретный ответ давай только если "
                                "он уже несколько раз ошибся. Не повторяй прошлые формулировки."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Лаба: {lab_slug}. Узел: {node}.{tried_part} "
                                f"Это {attempt + 1}-е обращение студента. Вопрос: {question}"
                            ),
                        },
                    ],
                ),
                timeout=8,
            )
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt
        except Exception:
            pass
        return _fallback(context)

    return reply


async def _find_l2_pair(lab_slug):
    """Another enabled lab with the same skill (meta.skill) → near-transfer L2. None if no pair."""
    from sqlalchemy import select

    from db.session import async_session
    from models.lab import Lab

    async with async_session() as db:
        l1 = await db.get(Lab, lab_slug)
        skill = (l1.meta or {}).get("skill") if l1 else None
        if not skill:
            return None
        labs = (await db.execute(select(Lab).where(Lab.enabled.is_(True)))).scalars().all()
        for lab in labs:
            if lab.slug != lab_slug and (lab.meta or {}).get("skill") == skill:
                return lab.slug
    return None


async def _run(args) -> None:
    from db.session import async_session

    def db_factory():
        return async_session()

    settings, gns3_client, monitor_registry = _build_deps()
    l2_lab = await _find_l2_pair(args.lab)
    if l2_lab:
        print(f"lab={args.lab} L2-пара={l2_lab} (near-transfer)")
    else:
        print(f"lab={args.lab} — нет L2-пары того же навыка → только L1")
    tutor_reply = _make_tutor_reply(settings, args.lab)
    provision = _make_provision(settings, gns3_client, monitor_registry, args.lab, tutor_reply)
    finalize = _make_finalize(
        args.lab, l2_lab, gns3_client, monitor_registry, settle_sec=args.settle_sec
    )

    async def _record(session_id: str, window: int, regime: str) -> None:
        async with async_session() as db:
            await record_truth(db, session_id, window, regime)

    try:
        report = await run_cohort(
            n=args.n,
            concurrency=args.concurrency,
            base_seed=args.seed,
            db_factory=db_factory,
            provision=provision,
            record_truth=_record,
            max_steps=args.max_steps,
            finalize=finalize,
        )
        print(
            f"completed={report.completed} peak_concurrency={report.peak_concurrency} "
            f"students={len(report.per_student)} failures={len(report.failures)}"
        )
        for s in report.per_student:
            print(f"  {s['user_id']} session={s['session_id']} windows={s['windows']}")
        for f in report.failures:
            print(f"  FAIL i={f['i']} {f['error']}")
    finally:
        # Give monitors time to pick up trailing events (poll_interval=5s) before stopping:
        # actions are time-compressed, the last node.updated lands in history with a lag.
        await asyncio.sleep(args.drain_sec)
        await monitor_registry.stop_all()
        await gns3_client.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Прогон сим-когорты студентов на живом стеке")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lab", default="lan-static-ip")
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument(
        "--drain-sec",
        type=float,
        default=10.0,
        help="хвостовое ожидание, чтобы мониторы добрали события",
    )
    ap.add_argument(
        "--settle-sec",
        type=float,
        default=12.0,
        help="пауза перед завершением лабы: монитор добирает хвост и может вмешаться",
    )
    args = ap.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
