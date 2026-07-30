# onlinetlabs — backend refactor & modernization analysis

Scope: backend + gns3/gns3-mcp + gns3/gns3-service + mcp-sdk. Frontend excluded per request.
Method: parallel subsystem mapping (12 groups) → simplification hunt → adversarial grep-verification (191 CONFIRMED / 10 PARTIAL / 1 REFUTED / 7 bonus) → OSS research vs fastapi-template, Netflix/dispatch, polarsource/polar, pydantic-ai, MCP SDK, fastapi-best-practices, plus 2026 tooling/logging/testing/SQLAlchemy/WebSocket surveys.

Ground rule respected throughout: the 2.3.4 / MRT research apparatus (learning_analytics, evaluation, experiment, control) is **required capability**. Every proposal below preserves that capability, behavior, and performance — it simplifies *implementations*, deletes *dead* code, and fixes *bugs*.

Verdicts are grep-verified against the current working tree (WIP included). PARTIAL = claim direction correct, a count or severity nuance differs. Only one claim was REFUTED.

---

## 0. Headline

- **~1,500–2,000 LOC of confirmed dead/duplicated code** is removable with zero behavior change.
- **No lint config on the backend at all**; siblings only `select=["E","F","I"]`. No type checker anywhere. No lint/test CI (deploy-only workflows). This is the single biggest gap vs every studied repo.
- **~10 real bugs** surfaced while hunting simplifications — several security-relevant (encrypted-cred leak on a *live* route, WS session hijack, timing-unsafe internal-token compare, sync bcrypt on the event loop). These are separate from "simplify" but you'll want them.
- **Dependencies are behind**: `python-jose` (unmaintained), `pydantic-ai ^0.2` (2 major versions / ~18 months behind; current 2.11), `structlog ^24` (current 26), and **both** `structlog` and `python-json-logger` shipped (the latter imported nowhere).
- **Comments/docstrings**: ~6,463 Cyrillic lines. Translatable — but a subset are **runtime strings** (LLM prompts, user messages) that must NOT be translated. See §6.

---

## 1. Overengineering / simplification, ranked by value

Ranked by (LOC + cognitive load removed) × (safety). Each is CONFIRMED unless noted.

### 1.1 Collapse the agent layer — the biggest structural win
The `backend/agents/` package carries a five-agent framework where production uses **two paths only**: `Orchestrator.intervene()` (Hint/Tutor) and the rules engine `analyze_session()`. Verified:
- `Orchestrator.run()` (intent routing question/validate/lab/analytics) — **no production caller**; only tests. `deps.get_orchestrator` — imported by no router.
- `LabAgent`, `ValidatorAgent` — inherit `BaseAgent`'s pydantic-ai model cache but their `run()` never touches an LLM; `LabTools.get_component_state/execute_action`, `LabActionInput` — zero production callers. (Validation actually lives in `backend/validation/`.)
- `AnalyticsAgent` is constructed `AnalyticsAgent(config, None)` in `monitor_registry.py:29` — its DB tools would crash if called. It's a rules engine wearing a `BaseAgent` costume. `analytics/tools.py:get_lab_progress` — no callers; `get_attempts` — only via the dead `run()`.
- `agents/base.py:_build_model` re-implements `llm/client.py:build_client`+`model_uri` (Yandex `x-folder-id`, `gpt://folder/model`, `'ollama'` default) inline — provider logic maintained in **two** places.
- `pydantic-ai` is imported in exactly one file and used as a bare `.run(prompt)` completion wrapper — no tools, no structured output, no deps. It currently buys nothing over the raw `AsyncOpenAI` client that `chat/router.py` already uses.

**Proposal (capability-preserving):**
- Delete `LabAgent`/`ValidatorAgent`/their tools + `Orchestrator.run()` + `deps.get_orchestrator` + the `_get_agent` class-identity ladder. Keep the intent-routing *capability* documented (it's endorsed as pydantic-ai "level 3 of 5" programmatic hand-off — defensible in the dissertation) but implement it as a dict when a caller actually needs it.
- Extract `analyze_session()` into a pure `identify_regime(features, config)` function (it already is one, trapped in a class). `evaluation/harness._analyze` and `admin` both duplicate its body and poke `AnalyticsAgent._detect_struggle` — both collapse onto the extracted function.
- After the pydantic-ai 2.x bump (§5.4), delete `_agents_by_model` (per-run `model=` override replaces it) and fold `_build_model` to call `llm/client.py`.
- Unify the tutor persona: `llm/prompts.py:TUTOR_SYSTEM_PROMPT` (rich, anti-hallucination) vs `agents/tutor/agent.py:TUTOR_SYSTEM_PROMPT` (thin 5-rule) diverge; interventions get the weaker one. One source. `llm/prompts.py:HINT_SYSTEM_PROMPT` is dead (hint agent has its own copy).
Est. **−350 to −500 LOC**, one LLM-invocation stack instead of two.

### 1.2 De-fragment `sessions/routers/` (7 files → 3) and kill the ordering hack
`sessions/router.py` aggregates 7 split routers with **undocumented order-sensitivity** (`launch`'s `/queue-status` must `routes.extend` before `query`'s `/{session_id}`). Several files are one 3-line pass-through endpoint each (`credentials.py` 22 LOC, `activity.py` 28 LOC). Collapse to `commands.py` / `queries.py` / `ws.py`. Removes both the ordering fragility and the pass-throughs. **−~80 LOC + a latent routing bug class.**

### 1.3 Table-drive `gns3-mcp/domain_tools.py` (244 LOC → ~60)
26 near-identical 5-line closures (parse ctx → get client → call one api method → wrap in success dict). A `{tool_name: (api_method, message_template)}` registration table keeps the exact MCP tool surface. Also fixes the drift in §3 (action surface represented 3×). `get_client`/`get_project_id` are typed `Any` — restore the contract. **−~180 LOC.**

### 1.4 Return ORM rows via `from_attributes`, stop hand-copying fields
Routers hand-copy every model field to response schemas (`courses/router.py` spends 25 of 53 lines on it; labs/progress the same). `instructor/schemas.py:104-177` is ~70 LOC of "mirror" dataclasses + `dataclasses.asdict` converters. Pydantic v2 `ConfigDict(from_attributes=True)` + returning ORM/dataclasses to `response_model` deletes roughly half this code — and `MCPAuditRow` in the same file **already** demonstrates the idiom in-repo. `instructor/service` returns dicts the router re-wraps `StudentOverview(**s)`; return the models. **−200+ LOC across features.**

### 1.5 One error-mapping decorator in `mcp-sdk/server.py` (8 copies → 1)
The identical ~12-line `try/except` ValidationError→SessionContextError / Exception→"Internal server error" block appears **8 times** (lines 78–245). A single decorator around the impl call makes the error contract exist once. **−~90 LOC.** (Bonus: it also lets you stop masking tool-argument errors as "Internal server error" — see §3.)

### 1.6 Collapse the "experiment assignment" concept (4 files → 1)
`control_arm.py`(18) + `group_assigner.py`(39) + `arm_resolver.py`(55) + `transfer.py`(12) = 124 LOC, each an enum + `random.choice()`. Plus **three parallel read-or-assign-persist randomizers on `User`** (`launch.assign_experiment_group_if_needed`, `variant_router._resolve_group` [dead], `arm_resolver.resolve_control_arm`) — same idiom, three encodings, different commit semantics. One `experiment/assignment.py`. **−~60 LOC + removes a nondeterminism bug** (`resolve_control_arm` returns a fresh random arm for a missing user on every call — see §3).

### 1.7 Retire the gns3-service back-compat shims
`src/service.py` and `src/gns3_admin_client.py` are 8-line re-export shims "for back-compat" — but **all** production importers (main.py, ws proxy, templates_bootstrap, services/*) import *through the shims*, so the migration is circular. Repoint imports to `src.services.*` / `src.clients.admin` and delete the shims. Same for the `sessions/service.py` 51-LOC re-export facade (callers already mix `sessions.service` and `sessions.services.query` — pick one).

### 1.8 Deduplicate the identifier/threshold research vocabulary
- `_BAD_REGIMES` + `_is_bad` duplicated between `control/criterion.py:24` and `control/derive_thresholds.py:15` with a "keep in sync" comment; `evaluation/metrics.py:104` imports the *private* copy. One drifted set silently corrupts J. Single source.
- `control/criterion.py:96 compute_J(dwell_thresholds=None)` never uses the param; `derive_thresholds` threads it positionally — misleading signature on the central research function.
- Two percentile conventions in one subsystem: `latency.percentiles` (nearest-rank, base n) vs `evaluation/metrics` (base n−1) — same statistic, different answers at small n. Pick one.
- Synthetic-scenario builders duplicated across `admin/router.py` (~180 LOC harness), `control/derive_thresholds.__main__`, `scripts/eval_identifier.py`, `scripts/export_defense_metrics.py` — "defense numbers" computed by copy-pasted code that can drift. Move to one `evaluation/` home, import from both admin and CLI.

### 1.9 Shallow module cleanups (pattern: interface ≈ implementation)
Thin wrappers that are one insert/one query with a single caller, safe to inline or merge: `learning_analytics/mrt.py` (23 LOC), `evidence.py` (25 LOC, caller already wraps it), `latency.record_stage_latency` (double-wrapped by `monitor._record_latency`), `control_interface/audit.py`, `validation/repository.py`, `validation/stream.py`, `observability/models.py` (14 `event_*()` factories → one constructor + templates), `courses/service.py`, `escalation/`. Individually small; together **−300+ LOC** and fewer files to open per concept.

### 1.10 `analytics/` vs `learning_analytics/` vs `AnalyticsAgent` name collision
`backend/analytics/` is a whole top-level package for **one endpoint + 2 schemas**, colliding with `learning_analytics` and `AnalyticsAgent` — three "analytics" concepts to disambiguate on every read. Fold into `learning_analytics` or an instructor/reporting slice. (Its rate-limit `request.state.user` trick is also a no-op — see §3.)

---

## 2. Dead code — delete outright (verified zero production callers)

| Target | Evidence |
|-|-|
| `backend/sessions/routers/sessions.py` (267 LOC) | pre-split monolith, **no importer**; also leaks encrypted `meta` (security, §3) |
| `backend/agents/lab/*`, `backend/agents/validator/*` | no production caller; only tests + dead `Orchestrator.run` |
| `backend/llm/prompts.py:HINT_SYSTEM_PROMPT` | no importer; hint agent has own copy |
| `backend/mcp_client/client.py:call_domain_tool` | zero callers |
| `backend/agents/analytics/tools.py:get_lab_progress` | zero callers |
| `backend/deps.py:get_gateway, get_orchestrator` | zero callers (WS reads `app.state` directly) |
| `backend/utils/__init__.py` | empty package, imported nowhere |
| `backend/auth/exceptions.py:AccountMismatchError` | never raised/caught |
| `backend/auth/service.py:hash_password` (sync) | zero callers (only `hash_password_async` used) |
| `backend/models/enums.py` (5 enums) | zero consumers; columns are raw `String` with string-literal defaults — the enums validate nothing |
| `backend/simulation/env/actor.py` (Protocol) | **no importer at all**; GNS3Actor duck-types; zero type value today |
| `CourseProgress` model + `CourseProgressResponse` + read path | never constructed; `AllProgressResponse.courses` always `[]` — speculative generality through 4 layers |
| `experiment/transfer.py:is_l2_pair` | no production caller (arm_resolver re-implements inline) |
| `scripts/eval_identifier.py:_try_harvest_real` | queries sessions into an unused var, unconditionally `return 0` — misleads readers that real data is merged |
| `evaluation/real_loader.py:load_scenario` | zero callers + O(n²) |
| gns3-service `db/session.py:create_tables` | referenced nowhere |
| gns3-service `metrics.gns3_provisioning_duration`, `gns3_admin_calls` | never `.observe()`d |
| gns3-service `RolesMixin.create_role/delete_role/assign_role_to_user` | test-only (prod uses only `get_builtin_role`) |
| `mcp-sdk/testing/conformance.py` (219 LOC) | zero subclasses/callers |
| `mcp-sdk/testing/utilities.py` (FakeConnectionPool et al.) | zero consumers + drifted from real interface |
| `mcp-sdk/src/mcp_sdk/connection.py:ConnectionPool.start()` | never called |
| `backend/tests/settings/reports/autotest.py` | **third** copy of the TMS decorators; zero importers (all files use `mcp_sdk.testing`) |
| gns3-mcp `LogBufferConfig.inactivity_timeout` | threaded end-to-end but never read — advertised behavior doesn't exist |
| `python-json-logger` dependency | imported nowhere; drop from pyproject |
| gns3-mcp/mcp-sdk: `pyproject` per-file-ignores for `tests/test_public_api.py`, `tests/test_conformance.py` | files don't exist |

Also drop dead observer bookkeeping in `WebSocketGateway` (`connect_observer/observers()` read only by tests; real delivery is via `activity_log.subscribe`), and the `collector._call_observe` direct-MCP fallback (`monitor_registry` always injects `ControlInterface`; the fallback is a second maintained path for one behavior, plus an unused `InterfaceDenied` import).

---

## 3. Bugs found while hunting (separate from "simplify" — but you'll want these)

Ordered by severity. All CONFIRMED.

1. **Encrypted-credential leak on a LIVE route.** `sessions/routers/lifecycle.py:99` (`update_session_endpoint`, PATCH) returns `meta=session.meta` — the encrypted creds. `query.py:46,70` deliberately returns `meta=None` (comment: "we do not return encrypted credentials in the list"). The dead monolith (§2) has the same leak. The live one is worse.
2. **WebSocket session hijack.** `sessions/routers/ws.py:session_interventions_ws` decodes the JWT but never checks the session belongs to the user (`session_events_ws` does). Since `gateway._connections` is single-slot `dict[str, WebSocket]`, attaching to another user's `session_id` also *evicts* the real student — tutor interventions (the control-loop actuator) go to the attacker.
3. **Gateway reconnect race.** `connect()` overwrites `_connections[session_id]`; the stale socket's later disconnect pops the **new** socket. On page refresh the student silently stops receiving interventions. Pop only if the stored ws is the disconnecting one.
4. **Timing-unsafe internal-token compare.** `auth/dependencies.py:136` uses `!=` on the shared secret that mints all backend JWTs. Use `secrets.compare_digest`.
5. **Sync bcrypt on the event loop.** `auth/router.py:78` calls `verify_password` (`bcrypt.checkpw`, ~100–300 ms CPU) directly in the async `/login` handler — blocks the loop for every login. (Hashing already uses an executor; verify doesn't.)
6. **Redis slot-counter leak.** `launch.py` acquires a queue slot; when `launch_session` returns an already-active session it never releases it, and `active_sessions_gauge.inc()` fires again. Refresh/retry inflates per-lab/global counters until the 7-day TTL, throttling other students.
7. **`end_session` (PATCH) teardown asymmetry.** Marks the session ended but does **not** stop the `SessionMonitor`, release the queue slot, or dec the gauge (`end_lab` does all three). Also writes free-form `status: str` while stamping `ended_at`. Route it through `end_lab` semantics or remove it (frontend doesn't call it).
8. **`create_task` with no reference.** `observability/activity.py:43` — `asyncio.create_task(self._persist(event))` is unreferenced and can be GC'd mid-flight (CPython docs), silently losing activity events. Also `_prune` runs `SELECT ... OFFSET + DELETE` on **every** emit.
9. **`exec_vtysh` can never succeed against the real service.** `gns3-mcp/domain_tools.py:49-70` POSTs `/v1/exec/vtysh` with no `Authorization` header; gns3-service `verify_internal_token` 403s it. Unit tests mock a 200 via respx, so the gap is invisible. (Bonus: if `INTERNAL_API_TOKEN` is empty, `exec.py:35` 403s *everyone* — silent misconfig, not a startup error.)
10. **gns3-mcp `LogBuffer` is process-global** but its data is per-project: `_ensure_log_buffer` builds the WS URL from the **first** session's `project_id`/jwt and then no-ops; students in other projects read the first project's logs.

Nondeterminism/consistency: `arm_resolver.resolve_control_arm` returns a fresh random arm for a missing user each call; monitor cursor can skip events after restart (`start_session` seeds from max(ts) over all events, `_load_new_events` excludes interventions); `_log_would_intervene` hardcodes `control_arm='open'` even on the MRT withhold branch (mislabeled provenance). gns3-service publishes every history event **twice** (direct `_translate` publish + PG NOTIFY trigger republish).

---

## 4. What the top OSS repos do — and what to copy (grounded)

Studied live on 2026-07-16: `fastapi/full-stack-fastapi-template` (44k★), `Netflix/dispatch` (6.5k★, going stale), `polarsource/polar` (10k★, closest stack), `zhanymkanov/fastapi-best-practices` (17.7k★), `pydantic/pydantic-ai` (18.6k★), MCP python-sdk, plus Onyx/open-webui for scale counter-examples.

**Convergence (all agree):**
- **uv** everywhere; Poetry absent from every inspected repo. Multi-package repos use **uv workspaces** (one lock, root-shared tooling) — pydantic-ai and the MCP SDK are both uv workspaces.
- **ruff = linter + formatter** (black gone). Real select sets: template `E,W,F,I,B,C4,UP,ARG001,T201`; polar `I,UP,T20,B039,PT,RUF*`.
- **A type checker is table stakes** — mypy (polar, template) and/or pyright strict (pydantic-ai, MCP SDK). Template runs **both** mypy strict + Astral `ty`.
- **Lint + typecheck + test CI on every PR** against **real Postgres/Redis** service containers, with a coverage gate. This is onlinetlabs' biggest single gap.
- **Domain vertical slices** (dispatch/polar/best-practices), but **central `models/`** at scale (polar keeps all ORM in `polar/models/`, like onlinetlabs already does — keep it) + a **`kit/` shared library** for cross-domain plumbing.
- **Commit-at-request-boundary**: the session dependency commits/rolls back; services never call `session.commit()`.
- **`lazy="raise"` on relationships** + explicit eager loading (asyncpg makes implicit lazy loads crash anyway).
- **`AGENTS.md`** as an executable architecture contract (polar, best-practices, template) — a per-package convention doc agents actually follow.

**What to SKIP for onlinetlabs** (evidence-based, not cargo-culted): dispatch's `scoped_session`+`schema_translate_map` middleware (sync + multi-tenant, neither applies); its generic `search_filter_sort_paginate` engine (unmaintained, string-model magic); polar's read/write `NewType` split (no read replica); single-`models.py` (template's 2-entity shape doesn't scale to 446 files); pydantic-ai v2 `capabilities`/on-demand loading (you run specialized separate agents by design).

---

## 5. Tooling & lint — concrete, staged

### 5.1 Ruff (do first — highest leverage, backend has zero config today)
Add one shared config. Recommended starting set (proven template baseline + `ASYNC` because it would have caught bugs #5 and #8, + `DTZ`):

```toml
# backend/pyproject.toml  (mirror into gns3-mcp, gns3-service, mcp-sdk — or one root config after the uv workspace move)
[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = ["migrations", "alembic"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "C4", "SIM", "ASYNC", "DTZ", "T20", "RUF"]
ignore = ["E501", "B008"]   # E501: formatter owns width; B008: FastAPI Depends() in defaults
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "ARG", "PLR2004"]
"scripts/**" = ["T20"]
[tool.ruff.lint.pyupgrade]
keep-runtime-typing = true
```

Baselines measured on the current tree (ruff 0.14.14): backend has **77** errors under ruff defaults but **3,327** under the wide `E,W,F,I,UP,B,SIM,C4,RUF,PTH,PL,ASYNC,S` set. So **do not** enable the maximalist set on day 1. The config above is the sweet spot; `ruff format` + `--fix` clears the mechanical bulk (imports, quotes, f-strings, ~383 auto-fixable). Then triage `ASYNC`/`B`/`SIM` by hand.

`RUF001/002/003` (ambiguous Cyrillic homoglyphs) fire ~900× — those overlap the translation effort (§6); enable `RUF` but expect to clear them as translation proceeds, not before.

### 5.2 Type checker (introduce, don't strict-gate yet)
Zero type checker over ~22k LOC. mypy strict on day 1 = a wall. Path: add **mypy with the pydantic plugin, non-strict** (`check_untyped_defs = true`), run non-blocking, ratchet. Copy polar's `[tool.mypy]` + `[tool.pydantic-mypy]` blocks. Start on the leaf packages (`mcp-sdk` 1.3k LOC, `gns3-mcp` 2.5k LOC) where it's tractable, then backend. (Astral `ty` is viable as a fast second checker but still 0.0.x — optional.)

### 5.3 CI + pre-commit (currently absent)
- One GitHub Actions workflow: `ruff check` + `ruff format --check` + `pytest` per package (matrix over the 4), backend job with Postgres+Redis service containers + `alembic upgrade head` + a one-line single-head gate (`test $(alembic heads | wc -l) -eq 1`). Start coverage gate low, ratchet.
- `.pre-commit-config.yaml` with **local hooks** running `poetry run ruff …` (survives a later uv migration unchanged) + generic hygiene (typos, end-of-file). SHA-pin the existing deploy workflows and add `permissions: {}` — cheap supply-chain wins.

### 5.4 Dependency currency
- **`python-jose` → PyJWT** (unmaintained, known CVEs; mechanical swap — the template did it in one PR). Optionally `bcrypt` → `pwdlib[argon2,bcrypt]` for argon2 + auto-rehash-on-login + the DUMMY_HASH anti-enumeration trick.
- **`pydantic-ai ^0.2` → 2.x.** ~half a day, grep-verified small: rename `OpenAIModel`→`OpenAIChatModel` in `agents/base.py` (+ its test), change the pin/extras to `pydantic-ai-slim[openai]`. Nothing else in backend imports pydantic_ai. Unlocks per-run `model=` override (delete the agent cache) and, later, `MCPToolset` (native per-user MCP toolsets — the exact problem your in-house SDK solves). Do §1.1 and this together.
- **`structlog ^24` → ^26**; **drop `python-json-logger`**.
- `uvicorn ^0.40 → ^0.51` (websockets-sansio default; your `websockets ^16` pin already satisfies it). `prometheus-fastapi-instrumentator ^7` is fine now but will need `^8` at the next FastAPI/Starlette major.

### 5.5 uv workspace (bigger move, do when you touch tooling next)
4 Poetry roots with no shared lock means `mcp-sdk` consumers can drift. A root `[tool.uv.workspace]` with members `backend, gns3/gns3-mcp, gns3/gns3-service, mcp-sdk` gives one lock, one `uv sync`, `mcp-sdk` as a `{ workspace = true }` source, and one root ruff/mypy/pytest config. Migration is mechanical (Poetry→uv). This is the highest-leverage *structural* tooling change but it's an XL; sequence it after ruff+CI land.

### 5.6 Logging (fix a live double-log bug)
Backend logs **every request twice** in prod: `observability/logging.py:49-52` re-propagates `uvicorn.access` into the root JSON handler **and** `middleware/request_id.py:34` emits its own `request_handled` line (Dockerfile starts uvicorn without `--no-access-log`). Keep the richer middleware line (has request_id + duration), add `--no-access-log`. Also: the `foreign_pre_chain` is missing `add_logger_name` + `ExtraAdder` (stdlib logs lose their name and `extra=` fields); there are two request-id mechanisms (a hand-rolled `request_id_ctx` ContextVar **and** `structlog.contextvars.bind_contextvars`) — keep one. Rewrite `RequestIDMiddleware` as pure-ASGI (BaseHTTPMiddleware breaks contextvar propagation to the final log line). gns3-service's logging is a copy-paste of the same config with the same gaps.

### 5.7 SQLAlchemy/Alembic discipline
- Add `MetaData(naming_convention=…)` (PG-shaped, so existing DB names stay compliant — no rename migration). Without it, autogenerate can't emit `drop_constraint` for anon-named constraints.
- Move scattered `session.commit()` out of services into a commit-at-boundary `get_db` (`try: yield; except: rollback; raise; else: commit`). Biggest consistency win for least code.
- Roll out `lazy="raise"` on relationships per-model (async already forbids implicit lazy loads; makes N+1/greenlet failures deterministic).
- Fix index drift: `ix_learning_sessions_user_lab_status/_user_id`, `ix_accounts_user_id`, `ix_sessions_user_id` exist only in migrations, not model `__table_args__` → autogenerate emits spurious drops each time. `ix_learning_sessions_user_id` is redundant (3 composite indexes already lead with user_id).
- Date-prefix future migration filenames (`file_template` in alembic.ini) — the hand-minted fake-hex ids (`a7b8c9d0e1f2`…) carry no ordering.
- `labs` table has 4 columns for GNS3 image variants (4 migrations, more to come per device type). The table already has a `meta` JSON column — a single JSON mapping holds the same capability without the migration treadmill.

### 5.8 Tests
- Add `asyncio_default_fixture_loop_scope = function` to `pytest.ini` (warns on pytest-asyncio ^1.x otherwise); bump `pytest-asyncio >= 1.4`.
- Drop `--disable-warnings` — it hides exactly the pydantic-ai ^0.2 / pytest-asyncio deprecations you're most exposed to.
- Consolidate the SQLite bootstrap smeared across **36 files** (3 stylistic variants of engine + `__table__.create`) into one parametrizable root `conftest` fixture; move the `_FakeDb`/`_ScalarResult` fakes (redefined in ~10 files) next to the builders. Consider per-xdist-worker real Postgres for an integration tier (polar pattern) + `fakeredis` (kills the "make up-db or analytics 500s" coupling).
- Add a conftest kill-switch: `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` so unit tests never hit a live LLM. Fix the tautology tests (`test_tutor_llm` stubs `_agent_for` then asserts "answer not empty" — tests the stub) — relevant to your F1=1.0 integrity concern.
- TMS hygiene: 11 `external_id` values aren't valid uuid4 (all 7 in the WIP `test_interface.py` are the fabricated `a1b2c3d4-…` sequence); 9 `autotest.num` collisions across files; 8 of 13 `pytest.ini` markers unused. Per your own convention (`external_id` = real uuid4), regenerate these.
- **Zero WebSocket tests exist** despite WS being the core feature. Add `httpx-ws` `ASGIWebSocketTransport` and cover the observer route + the auth/ownership checks from §3.

---

## 6. Russian → English comment/docstring translation plan

~6,463 Cyrillic lines. This is **not** a ruff auto-fix and **not** uniform. The hard constraint:

> **Runtime Russian strings must NOT be translated.** `backend/llm/prompts.py`, `agents/tutor/agent.py`, `agents/hint/agent.py` (verified) contain Russian **LLM prompts / user-facing text** — the tutor speaks Russian to students *by design* (there's a `LANGUAGE_REMINDER`). Translating those changes product behavior. Same risk for any `raise HTTPException(detail="…")`, toast/message strings, and `event_type`/summary text that reaches the UI.

**Classification first (cheap, scriptable):** partition every Cyrillic line into
1. **Comments** (`#…`) → translate.
2. **Docstrings** (`"""…"""` in def/class/module position) → translate.
3. **String literals** in runtime code → **leave by default**; translate only ones proven to be developer-facing (log messages with no user surface). When unsure, leave.

**Execution (safe + verifiable):**
- Do it **module-by-module / subsystem-by-subsystem**, not one giant sweep, so each batch is reviewable and testable.
- Guardrail: after each batch, `git diff` must show **only** comment/docstring lines changed (no code tokens, no string literals in return/raise/prompt positions). `python -c "import …"` + `ruff check` + the package's test suite must stay green — a translation that changes a code line is a bug.
- This is a good **workflow** candidate: one translation agent per subsystem, each with the rule "translate comments + docstrings to English; never touch string literals, identifiers, or code; preserve line count where possible," then a verify pass diffing that only comments/docstrings moved. (Analogous to the analysis workflow that produced this report.)
- Enable ruff `RUF001/002/003` **after** translation, not before — they'll flag residual Cyrillic homoglyphs as a completeness check.
- The 4 packages each have their own Russian (`gns3-service` 66/78 files, `mcp-sdk` 12/12); `autotests/` (70/119) is a separate track (out of the four in-scope if you want, but same method).

Order suggestion: translate a package **right after** you refactor it (§1) so you're not translating code you're about to delete.

---

## 7. Suggested sequencing

1. **Delete dead code** (§2) + fix the **security bugs** (§3 items 1–5). Highest value, lowest risk, shrinks everything downstream.
2. **Ruff + pre-commit + a lint/test CI job** (§5.1, §5.3). Freezes quality before you move code.
3. **Structural simplifications** (§1.1 agents, §1.2 routers, §1.3 domain_tools, §1.5 sdk error decorator) — each is an isolated PR.
4. **Dependency currency** (§5.4): python-jose→PyJWT, structlog bump + drop python-json-logger, then pydantic-ai 2.x paired with the agent-layer collapse.
5. **Logging fix** (§5.6) + **SQLAlchemy discipline** (§5.7).
6. **Translation** (§6), per-package, after each package is refactored.
7. **uv workspace** (§5.5) + **mypy** (§5.2) once the surface is stable.
8. Layout consolidation (fold sub-100-LOC crumbs — `middleware`, `llm`, `escalation`, `analytics` — into a `kit/`/`core/` or their owning domain; keep central `models/`).

---

## Appendix — the one REFUTED claim & notable PARTIALs
- **REFUTED**: gns3-service `/history/{id}/actions` is **not** dead — `gns3-mcp/src/server.py:276` calls it in production (`list_user_actions`), and autotests hit it. (The duplicated query+mapping vs `/activity` is still real; just don't delete the route.)
- **PARTIAL** (direction right, detail off): `observability/models.py` has 14 factories not 13; `custom_assertions.py` removal is TMS-policy-dependent (174 LOC, used in 122 files); node_actions pass-through *does* add one invariant (`invalidate_state_cache`); backend pulls ~8 SDK model symbols not 4; `UserAlreadyExistsError` has **no** catcher at all (register race → 500, worse than "one catcher"). None change the recommendation.
