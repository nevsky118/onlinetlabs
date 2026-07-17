# Refactoring & Modernization Plan

Analysis date: 2026-07-16. Scope: `backend/`, `gns3/gns3-mcp/`, `gns3/gns3-service/`, `mcp-sdk/`, `backend/tests/` (frontend excluded).
Method: 12 architecture-mapping agents over every subsystem + grep-verification pass + external research of 10 topics against live repo trees (full-stack-fastapi-template, Netflix/dispatch, polarsource/polar, pydantic-ai, MCP python-sdk, onyx, open-webui, and tooling ecosystems), all facts dated and source-verified.

Constraint honored throughout: the 2.3.4/MRT research apparatus (learning analytics, evidence snapshots, regime annotations, cycle latency, grounding comparisons, experiment arms) is **required capability** — proposals simplify implementations, never delete capability.

---

## 1. Baseline facts

| Fact | Value |
|-|-|
| Python LOC | ~44k total: backend 22k src + 14.7k tests; gns3-service 6k; gns3-mcp 2.5k; mcp-sdk 1.3k |
| backend top-level dirs | ~30, several under 100 LOC (escalation 43, middleware 45, analytics 71, llm 88, courses 100) |
| Lint config | backend: **none** (ruff installed, unconfigured); siblings: `E,F,I` only |
| Ruff modern-ruleset violations | backend 3327 (≈915 are Cyrillic-char RUF001-003, 1073 line-length, 210 test asserts, 191 FastAPI `Depends` B008 → real core ≈600–800); gns3-service 338; gns3-mcp 116; mcp-sdk 79 |
| Type checker | none, anywhere |
| CI | deploy-only; no lint/test workflows |
| Cyrillic comments/docstrings | 507 files, ~6.5k lines |
| Stale deps | pydantic-ai `^0.2` (current: **2.11**, 2026-07-15); structlog 24 (current 26.1); python-jose (unmaintained, CVEs; ecosystem moved to PyJWT); python-json-logger (imported **nowhere** — dead dep); uvicorn 0.40 (0.51 has sansio WS + rolling restart) |
| Packaging | 4 independent Poetry roots, no workspace; every inspected top repo is on uv (Poetry absent from all of them) |

## 2. Bugs found during analysis (fix independent of any refactor)

Found by mapping agents while reading code; each backed by concrete file evidence.

### Security / correctness — P0

| # | Where | Problem |
|-|-|-|
| 1 | `backend/sessions/routers/ws.py` (interventions WS) | No ownership check: decodes JWT but never verifies the session belongs to the user. Any authenticated user can attach to any `session_id`; single-slot `_connections` dict means attaching **evicts the real student's socket** — interventions (the control-loop actuator) go to the wrong party. |
| 2 | `backend/sessions/gateway.py` | Reconnect race: `connect()` overwrites the slot; stale socket's `disconnect(session_id)` then pops the **new** socket. On page refresh the student silently stops receiving interventions. Pop only if stored ws is the disconnecting one. |
| 3 | `backend/sessions/routers/sessions.py` | 267-line dead pre-refactor router, imported nowhere, still leaks `session.meta` (encrypted creds) in `list_sessions`. Delete before anyone re-registers it. |
| 4 | `backend/sessions/routers/launch.py` | Redis slot acquired via `try_acquire` is never released when `launch_session` returns an already-active session; `active_sessions_gauge` also double-increments. Repeated launches throttle other students until the 7-day TTL. |
| 5 | `backend/sessions/services/lifecycle.py` `reset_lab` | Template-selection reimplemented with only 2 of launch's 3 branches — resetting an `-frr` lab passes `None` to `reset_project`. Extract one `resolve_template_pid()`. |
| 6 | `backend/auth/dependencies.py:136` | `require_internal_caller` compares the internal token with `!=` instead of `secrets.compare_digest` — timing side channel on the token that mints all backend JWTs. |
| 7 | `backend/auth/router.py:78` | `/login` runs bcrypt `verify_password` (~100–300 ms CPU) directly on the event loop; hashing already has an async executor path — verification doesn't. |
| 8 | `backend/sessions/ws/events.py` | Browser messages forwarded verbatim into the gns3-service socket authenticated with `internal_api_token` — browser inherits internal-token privileges. Events are one-directional in practice; drop client→upstream payloads. Also move the static internal token out of the URL into an `Authorization` header. |
| 9 | `gns3/gns3-mcp` `exec_vtysh` | POSTs to gns3-service without the `Authorization` header its `verify_internal_token` requires → always 403 in prod. Tests mock 200 via respx, hiding it. |
| 10 | `gns3/gns3-mcp/src/server.py` LogBuffer | Process-global buffer keyed to the **first** session's project/JWT — students in other projects read the first project's logs. |

### Research-data integrity — P0 for the dissertation

| # | Where | Problem |
|-|-|-|
| 11 | hint-text extraction | Implemented 3 inconsistent ways (`grounding._hint_text`: hint\|text; `monitor._dispatch_intervention`: hint\|answer; `_maybe_grounding_ablation`: hint only) — `grounding_comparisons` rows silently store `''`, corrupting the ablation dataset. |
| 12 | `monitor._log_would_intervene` | Hardcodes `control_arm='open'` even when called from the MRT withhold branch — mislabeled provenance. |
| 13 | `control/criterion.py` vs `control/derive_thresholds.py` | `_BAD_REGIMES`/`_is_bad` duplicated with a "keep in sync" comment; `evaluation/metrics.py` imports the private copy. One drifted set silently corrupts J. Also `compute_J(dwell_thresholds=None)` is a dead parameter still threaded positionally. |
| 14 | `monitor` restart cursor | `start_session` seeds `_last_event_at` from max(ts) over ALL events while `_load_new_events` excludes `intervention` events — events older than the last intervention can be skipped unanalyzed after restart. |
| 15 | two percentile conventions | `latency.percentiles` (nearest-rank, n) vs `metrics._p90`/bootstrap (n-1) — same statistic, different answers at small n. |
| 16 | `experiment/arm_resolver.py` | Missing user row → fresh random arm per call (silent nondeterminism instead of error). |
| 17 | `openclaw/client.py` | HTTP ≥ 400 labeled `openclaw_unreachable` (gateway WAS reached) — failure modes mis-attributed in experiment metadata. |

### Operational — P1

- Double access-log per request: `uvicorn.access` propagates into root JSON handler AND `RequestIDMiddleware` logs `request_handled`. Keep the middleware line (richer), start uvicorn with `--no-access-log`.
- `observability/activity.py:43`: `asyncio.create_task` with no reference kept — task can be GC'd mid-flight, silently losing activity events; `_prune` runs SELECT+DELETE on **every** emit.
- Rate limiting is per-process (no `storage_uri` on Limiter) — multi-worker prod multiplies every limit; the user-key branch only ever activates for one route (and even there slowapi computes the key before the handler sets `request.state.user`, so it never works).
- `main.py:health_deep` builds and tears down a fresh Redis client per readiness probe; lifespan client never lands in `app.state`.
- `gns3-service` publishes every history event **twice** (WS-proxy direct publish + PG NOTIFY listener) — subscribers see duplicates.
- TOCTOU races: `create_lab_endpoint`, `start_lab`, `record_step_attempt` (select-then-insert → 500 on concurrent duplicates).
- `GET /instructor/mcp-audit` unpaginated over a table the control loop appends to on every tool call — first endpoint to degrade as pilot data accrues.
- `tools/env_cipher.decrypt_file` leaves decrypted plaintext `.env` on disk.
- `users/router.py` writes directly into better-auth's Session table — silent coupling to a table owned by the Next.js library.

## 3. Overengineering & simplification (behavior-preserving)

### 3.1 Dead code — delete (~1,500+ LOC)

Grep-verified zero production callers by the mapping agents (verification pass re-confirming; anything it refutes stays):

- `backend/sessions/routers/sessions.py` (267 LOC, also bug #3)
- `backend/utils/` (empty package, zero importers)
- `backend/deps.py`: `get_orchestrator`, `get_gateway` (WS routers read `app.state` directly)
- `backend/llm/prompts.py::HINT_SYSTEM_PROMPT` (diverged live copy in `agents/hint/agent.py`)
- `backend/mcp_client/client.py::call_domain_tool`; `agents/analytics/tools.py::get_lab_progress`
- `backend/models/enums.py` — 5 str-enums with zero consumers; columns are raw strings (UserRole, the one used enum, lives elsewhere)
- CourseProgress write-dead path (model + migration + schema + read; nothing ever constructs it) — keep table, delete the pretense or wire it, but decide once
- `evaluation/real_loader.load_scenario` (zero callers, O(n²)); `scripts/eval_identifier._try_harvest_real` (computes then discards, returns 0) — flags the known "no real pilot data" risk; make loading real sessions an explicit TODO instead of dead code
- `backend/tests/settings/reports/autotest.py` (zero importers; all 139 files import from `mcp_sdk.testing`)
- mcp-sdk: `ConnectionPool.start()`, `testing/utilities.py` (FakeConnectionPool drifted from real interface, zero consumers), `ConformanceTestSuite` (219 LOC, zero subclasses — park it or delete; capability is re-creatable from git)
- mcp-sdk `pyproject`: per-file-ignores for `tests/` files that don't exist (SDK has no tests dir)
- gns3-service: `db/session.create_tables`, `RolesMixin.create_role/delete_role/assign_role_to_user`, dead prometheus metric objects, `GET /history/{id}/actions` (superseded by `/activity`, no consumers)
- gns3-mcp: `LogBufferConfig.inactivity_timeout` threaded env→loader→constructor, stored, never read
- `python-json-logger` dependency (imported nowhere)
- `ExchangeRequest.user_id` — required by schema, never read by handler (422s honest callers)
- `auth/exceptions.AccountMismatchError`; sync `hash_password` (zero callers)

### 3.2 Duplication — single-source (top offenders)

| Concept | Copies | Fix |
|-|-|-|
| LLM provider quirks (Yandex header, gpt:// URI) | `agents/base.py._build_model` + `llm/client.py` | base.py calls `build_client`/`model_uri` |
| Tutor persona prompt | `llm/prompts.py` (rich) vs `agents/tutor/agent.py` (weak, used for interventions) | one prompt module; interventions get the good prompt |
| `load_lab_spec` | `labs/spec.py` (uncached, sync IO in async SSE path) vs `validation/runner.py` (mtime-cached) | keep cached one |
| `require_admin` | auth/dependencies, admin/router, experiment/router | one dependency |