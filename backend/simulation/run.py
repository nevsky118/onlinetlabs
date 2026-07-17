"""CLI: прогнать сим-когорту на ЖИВОМ стеке (реальный GNS3, пул+очередь).

Требует поднятого стека: `make up-db` (корень) + gns3-стек (`cd gns3 && docker compose up -d`).
_live_provision собирает живые deps как в приложении (main.py lifespan / deps.py):
mcp_client / gateway / orchestrator / gns3_client / monitor_registry, затем
launch_session → build_session_context → monitor_registry.start → GNS3Actor из node_ids.

FIREWALL: все юзеры is_simulated=True; данные отрезаны от reproducibility-bundle.
Удалить: `rm -rf backend/simulation` + `DELETE FROM users WHERE is_simulated`.

Запуск: `ENV_FILE=../deployment/local/backend.env poetry run python -m simulation.run --n 3 --concurrency 2`
"""
import argparse
import asyncio
from datetime import UTC

from simulation.ground_truth import record_truth
from simulation.orchestrator import run_cohort

# Прайс YandexGPT (руб/1k токенов) — уточнить по актуальному тарифу; бюджет 500р.
_PRICE_PER_1K_RUB = 1.20
_BUDGET_RUB = 500.0

# Ожидание слота очереди (GLOBAL_CAP=50 одновременных сессий).
_QUEUE_ACQUIRE_TRIES = 90
_QUEUE_ACQUIRE_WAIT_SEC = 2.0

# Пауза после старта узлов: VPCS поднимает консоль не мгновенно.
_CONSOLE_WARMUP_SEC = 6.0


def _build_deps():
    """Живые зависимости приложения (1:1 с main.py lifespan)."""
    from config import settings
    # Приборы MRT-трека выключены по умолчанию (gated-off). Сим существует, чтобы их
    # прогнать: включаем decision-log/evidence/latency на живом контуре.
    settings.learning_analytics.mrt_enabled = True
    settings.learning_analytics.evidence_capture_enabled = True
    settings.learning_analytics.latency_capture_enabled = True
    # Сжатие времени: сим-сессия ~40с против минут у живого студента. Детектор idle
    # настроен на реальное время (idle_gap=60с) → в сжатом прогоне idle-периоды не
    # набираются. Масштабируем под сим, чтобы idle-паузы регистрировались и struggle
    # детектировался (де-риск прибора decision-log; НЕ валидация детектора).
    settings.learning_analytics.idle_gap_seconds = 0.5
    settings.learning_analytics.idle_threshold = 2
    settings.learning_analytics.rate_slope_threshold = 1.0
    # LabProgressObserver даёт события только со ВТОРОГО цикла (первый — базовый
    # снапшот). При дефолте 25с за сжатую сим-сессию второго цикла не случается —
    # spec-проверки не превращаются в check_failing, и детектор слепнет.
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
        config=settings, mcp_client=mcp_client, db_factory=async_session,
        orchestrator=orchestrator, gateway=gateway, activity_log=activity_log,
        gns3_client=gns3_client,
    )
    return settings, gns3_client, monitor_registry


def _console_host(node: dict) -> str:
    """Хост консоли: контейнерные loopback-адреса недостижимы с хоста → localhost.
    Консольный диапазон gns3-server опубликован (см. gns3/docker-compose.yml)."""
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
        # Сим-юзер должен иметь study-consent, иначе шов режет observe → пустой конвейер.
        async with async_session() as db:
            await grant_consent(db, user_id, scope="study", observe=True, act=True)

        # Занимаем слот очереди, как реальный студент: end_lab на завершении делает
        # release (сырой DECR), поэтому без acquire счётчики ёмкости ушли бы в минус.
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
            await queue.release(lab_slug)  # провижн упал → слот не должен утечь
            raise
        if session.status != "active":
            await queue.release(lab_slug)
            raise RuntimeError(f"сессия не active: {session.status}")
        ctx = build_session_context(session)
        await monitor_registry.start(session.id, session.user_id, session.lab_slug, ctx)

        gsess = (session.meta or {})["gns3_service_session_id"]

        # Узлы должны РАБОТАТЬ: spec-проверки читают конфиг через консоль, а у
        # потушенного узла консоли нет → проверки висят и детектор слепнет.
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
            budget_rub=_BUDGET_RUB, price_per_1k_rub=_PRICE_PER_1K_RUB,
        )
        actor = GNS3Actor(
            node_tasks=node_tasks, consoles=consoles,
            db_factory=async_session, backend_session_id=str(session.id),
            help_gen=help_gen, profile=profile, save_user_message=save_user_message,
            save_assistant_message=save_assistant_message, tutor_reply=tutor_reply,
        )
        return str(session.id), actor

    return provision


def _make_finalize(lab_slug, l2_lab, gns3_client, monitor_registry, settle_sec: float = 12.0):
    """Полный протокол исследования: L1 (ассист) → L2 (near-transfer, БЕЗ ассиста).
    l2_lab — пара того же навыка (или None → только L1, если у навыка нет пары).

    L1 закрывается ТЕМ ЖЕ путём, что и у реального студента — `end_lab`: стоп монитора →
    ExperimentMetrics + цензура MRT → teardown GNS3 → освобождение слота очереди.
    L2 — синтетическая сессия переноса (нет GNS3/монитора/слота), поэтому `end_session`:
    снимаются только измерения.

    INTEGRITY: L2-pass моделируется ТОЛЬКО от навыка студента, БЕЗ зашитого эффекта arm
    (иначе это «засеянный A/B»). Плечи выйдут ≈равны по l2_pass — честный null для симуляции.
    Данные is_simulated → отрезаны от reproducibility-бандла."""
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
        """LabProgress пишем ДО финализации: метрики читают из него steps_completed."""
        completed = steps >= total
        async with async_session() as db:
            db.add(LabProgress(
                id=str(uuid4()), user_id=user_id, lab_slug=lab, current_step=steps,
                status="completed" if completed else "in_progress",
                score=round(steps / total * 100.0, 1) if total else 0.0,
                started_at=started, completed_at=completed_at if completed else None,
            ))
            await db.commit()
        return completed

    async def finalize(session_id, user_id, profile, state):
        from datetime import timedelta
        now = datetime.now(UTC)
        # Таймстемпы: L1 раньше L2, положительная длительность в горизонте когорты.
        l1_start, l1_end = now - timedelta(minutes=14), now - timedelta(minutes=9)
        l2_start, l2_end = now - timedelta(minutes=6), now - timedelta(minutes=1)

        # L1 (ассистируется живым монитором): почти все завершают.
        l1_steps = total1 if profile.skill > 0.2 else max(0, total1 - 1)
        l1_done = await _write_progress(
            user_id, lab_slug, l1_steps, total1, l1_start, l1_end)

        # Живой студент не закрывает лабу в ту же миллисекунду, когда перестал
        # действовать: монитор успевает добрать хвост событий (poll_interval=5с) и
        # при необходимости вмешаться. В сжатом прогоне даём ему это время явно —
        # иначе end_lab гасит монитор раньше, чем события доедут из истории GNS3.
        await asyncio.sleep(settle_sec)

        async with async_session() as db:
            await end_lab(db, session_id, user_id, gns3_client, monitor_registry)

        if not l1_done or not l2_lab:
            return  # нет завершённой L1 или у навыка нет near-transfer пары → только L1

        # L2 (near-transfer, БЕЗ ассиста): pass ⇐ навык (порог выше — сложнее без помощи).
        l2_steps = total2 if profile.skill > 0.5 else max(0, total2 - 1)
        async with async_session() as db:
            l2 = LearningSession(
                id=str(uuid4()), user_id=user_id, lab_slug=l2_lab, status="active",
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
    """Ответ тьютора для чат-лога: LLM (короткий таймаут) → прогрессивный шаблон-фолбэк.

    Фолбэк ОБЯЗАН зависеть от номера попытки: раньше шаблон выбирался как
    `len(question) % N`, а вопрос был константным → тьютор дословно повторял один и тот
    же ответ, и диалог зацикливался. Живой тьютор ведёт студента по нарастающей: сначала
    уточняет, потом наводит, и только затем даёт конкретику (как HintAgent с уровнями).
    """
    import asyncio as _asyncio

    from llm.client import build_client, model_uri

    model = settings.agents.chat_model

    def _fallback(context: dict) -> str:
        attempt = int(context.get("attempt", 0))
        node = context.get("node") or "узле"
        tried = context.get("tried")
        tried_part = f"Ты ввёл `{tried}`. " if tried else ""

        stages = [
            # 1. Уточнение — тьютор не выдаёт ответ сразу.
            f"Расскажи, что показывает `show ip` на {node}? "
            "Сверим то, что применилось, с тем, что требует задание.",
            # 2. Наводка на класс ошибки.
            f"{tried_part}Сравни третий октет своего адреса с планом лабы: "
            f"похоже, {node} оказался в другой подсети, поэтому проверка и не проходит.",
            # 3. Конкретная механика.
            f"На {node} задай адрес из нужной подсети командой `ip <адрес>/<маска>` "
            "и проверь результат через `show ip` — маска должна совпасть с заданием.",
            # 4. Прямая подсказка после нескольких неудач.
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
            # max_retries=0: yandex может быть недоступен → мгновенный фолбэк на шаблон.
            client = build_client(model).with_options(max_retries=0, timeout=6)
            resp = await _asyncio.wait_for(client.chat.completions.create(
                model=model_uri(model), stream=False, max_tokens=180, temperature=0.6,
                messages=[
                    {"role": "system", "content": (
                        "Ты — тьютор по компьютерным сетям в лабе GNS3. Отвечай кратко "
                        "(2-3 предложения), по-русски. Веди студента по нарастающей: "
                        "сначала уточняй и наводи, конкретный ответ давай только если "
                        "он уже несколько раз ошибся. Не повторяй прошлые формулировки."
                    )},
                    {"role": "user", "content": (
                        f"Лаба: {lab_slug}. Узел: {node}.{tried_part} "
                        f"Это {attempt + 1}-е обращение студента. Вопрос: {question}"
                    )},
                ],
            ), timeout=8)
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt
        except Exception:
            pass
        return _fallback(context)

    return reply


async def _find_l2_pair(lab_slug):
    """Другая enabled-лаба того же навыка (meta.skill) → near-transfer L2. None если пары нет."""
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
            n=args.n, concurrency=args.concurrency, base_seed=args.seed,
            db_factory=db_factory, provision=provision, record_truth=_record,
            max_steps=args.max_steps, finalize=finalize,
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
        # Дать мониторам добрать хвост событий (poll_interval=5с) перед остановкой:
        # действия сжаты во времени, последние node.updated попадают в историю с лагом.
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
    ap.add_argument("--drain-sec", type=float, default=10.0,
                    help="хвостовое ожидание, чтобы мониторы добрали события")
    ap.add_argument("--settle-sec", type=float, default=12.0,
                    help="пауза перед завершением лабы: монитор добирает хвост и может вмешаться")
    args = ap.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
