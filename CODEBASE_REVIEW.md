# onlinetlabs — Python codebase review

**Date:** 2026-08-02
**Scope:** `backend/`, `gns3/gns3-service/`, `gns3/gns3-mcp/`, `mcp-sdk/`. Frontend excluded.
**Method:** three independent surveys → adversarial verification of every claim → this synthesis. Every entry below survived verification; verdicts are marked `CONFIRMED` or `PARTIAL` (PARTIAL = the defect is real, some detail in the original write-up was wrong; the correction is stated inline). Five headline findings were re-checked by hand for this report.

---

## Verdict

The engineering hygiene of this repo is genuinely good: there is a uv workspace (`pyproject.toml:1-5`), a real CI with Postgres+Redis service containers running `ruff format --check`, `ruff check`, `mypy` and `pytest` (`.github/workflows/ci.yml:20-90`), commit-at-request-boundary in `backend/db/session.py:33-41`, `MetaData(naming_convention=…)` at `backend/models/base.py:16`, `lazy="raise"` across the ORM, PyJWT and pydantic-ai 2.x pinned, `secrets.compare_digest` at `backend/auth/dependencies.py:149`, async bcrypt at `backend/auth/service.py:25-31`, WS ownership checks at `backend/sessions/routers/ws.py:37-42`, and the credential leak on PATCH closed at `backend/sessions/routers/commands.py:194`. The research apparatus is unusually complete for a dissertation codebase — a real closed loop, a real criterion J, a real MRT layer, real synthetic evaluation.

What is wrong is a different class of problem, and it is worse than a hygiene problem: **several capabilities that the system claims to have are not wired to anything, and two of them silently corrupt research numbers.** The A/B arm is randomized, persisted, exported to CSV and t-tested — but both arms run identical code. The "J-optimal operating point" that appears on the admin dashboard and in the defense export is computed from ground-truth labels rather than from the identifier, so it is a constant 0.0 regardless of detector quality. The entire `LearningAnalyticsConfig` — every T_k, every cost, `mrt_enabled` — is unreachable from the environment, so no deployment can ever have run with derived thresholds. Operationally, only one of five session-termination paths releases the Redis slot, so the global cap is a slow-motion outage. None of this is sloppy code; it is a wiring gap between well-built parts, which is the failure mode you get when a system is assembled bottom-up under time pressure. Roughly 2,000–2,300 LOC is removable with no behavior change, and about 230 LOC of good research code needs a *surface*, not a delete.

---

## Headline

- **The A/B contrast is a null contrast.** `experiment/variant_router.py:17` carries its own TODO; `SessionMonitorRegistry` never passes `intervention_router` (`sessions/monitor_registry.py:79-89`), so `monitor.py:377` always calls the orchestrator. Both `group_a` and `group_b` get identical treatment, while `experiment/router.py:218` serves a Welch t-test on them with a `significant` boolean. **CONFIRMED, re-verified.**
- **The headline "J-optimal T_k" is an oracle result.** `evaluation/metrics.py:123-135` builds the sessions fed to `total_J` from `scn.truth_regime`/`scn.onset_ts`, not from `run_identifier`. Executed against the admin fixture, `j_optimal(...).t_k == 0.0` on every grid and every cost vector; `c_false` is inert. **CONFIRMED, re-verified.**
- **No research knob is reachable from the environment.** `config/env_config_loader.py:193-204` omits `learning_analytics=`, and no `LA_*` env var name exists anywhere in the tree. Every deployment runs `dwell_thresholds = {0,0,0,0}`, `mrt_enabled=False`, evidence/latency/grounding capture off. **CONFIRMED, re-verified.**
- **Redis session slots leak on 4 of 5 exits.** Only `end_lab` (`sessions/services/lifecycle.py:208`) and launch-failure (`routers/commands.py:93/97`) release. `active_sessions_total` climbs to `GLOBAL_CAP=50` and then every launch returns "queued" forever. **CONFIRMED, re-verified.**
- **gns3-service's front door is half-locked.** `/v1/exec` and `/v1/templates` are token-gated; `/sessions`, `/projects` and `/history` are not, on a published port (`docker-compose.yml:79-80`). `POST /sessions/{id}/reset-password` returns a plaintext GNS3 password. **CONFIRMED, re-verified.**
- **One process-wide `LogBuffer` serves every student** (`gns3-mcp/src/main.py:24-29`, `log_buffer.py:40-42`): the first session's project logs are returned to all others, and they feed the tutor context and the LA feature vector.
- **Every rate limit is IP-keyed**, because `request.state.user` is only written inside an endpoint body (`analytics/router.py:26`) after slowapi has already computed the key. All dashboard traffic arrives from one BFF origin.
- **~2,000–2,300 LOC is removable with no behavior change**, concentrated in: gns3 dead build scripts (~530), openclaw + variant router (~370 if retired), the triple-encoded GNS3 action surface (~170), mcp-sdk protocol discovery (~160), triplicated env-cipher (~150) and config/observability bootstrap (~180), the cohort schema mirror (~110), and a long tail of dead enums/metrics/knobs.

---

## Broken and buggy

Ranked by consequence. All CONFIRMED unless noted.

### 1. Redis slots and the active-sessions gauge leak on every exit but one — CRITICAL

`sessions/routers/commands.py:72` acquires; only `sessions/services/lifecycle.py:208` and the launch-failure path at `commands.py:93/97` release. Sessions also end via `PATCH /users/me/sessions/{id}` → `end_session` (`lifecycle.py:123`), via `get_session_state`'s 404 auto-end (`sessions/services/query.py:72-74`), by tab abandonment, and via `idle_reclaim_loop` (`sessions/idle_reclaim.py`) which stops nodes but leaves `status='active'` forever. `try_acquire` re-EXPIREs both counters to 7d on every acquire (`queue.py:45-48`), so they never age out under traffic.

**Breaks:** `active_sessions_total` grows monotonically; at `GLOBAL_CAP=50` the Lua script returns 0 for everyone and `POST /sessions` permanently answers 202 "queued". `active_sessions_gauge` drifts identically and is never re-incremented by `_restore_session_monitors` on restart.

**Fix:** move release + gauge decrement into `_mark_ended_and_finalize` (`lifecycle.py:100`), the one function both `end_session` and `end_lab` already share; make it idempotent on `session.ended_at`. Do the same for the 404 auto-end in `query.py:72`. Have `idle_reclaim` call the same finalization. Change `release` to a Lua `max(0, n-1)`. Note `simulation/run.py:111/124` is a fourth acquire/release site and must stay consistent.

### 2. The group_a/group_b experiment is randomized but never applied — CRITICAL (data integrity)

`experiment/variant_router.py:17` (`# TODO: wire the B-arm into monitor_registry (currently only tests construct it)`). `SessionMonitor` takes `intervention_router=None` (`learning_analytics/monitor.py:62`) and no caller ever passes it — both constructions (`main.py:107`, `simulation/run.py:68`) omit it, so `monitor.py:377` and `:459` always take the orchestrator path. `OpenClawClient`/`OpenClawInterventionAdapter` are never instantiated outside tests. Meanwhile `assign_experiment_group_if_needed` runs on every provisioning row (`sessions/services/launch.py:31`), `experiment_group` is written into every `ExperimentMetrics` (`lifecycle.py:80`), and `compute_experiment_analysis` (`experiment/analysis.py:61`) splits on it for H1/H2 and is served at `GET /experiment/analysis` (`experiment/router.py:218-227`).

**Breaks:** H1 and H2 are t-tests on two identically-treated groups. The API reports `significant` on a treatment that does not exist.

**Fix — pick one, do not leave it as is:**
(a) *Wire it.* Build `OpenClawClient` → `OpenClawInterventionAdapter` → `ExperimentVariantRouter` in `lifespan` when `settings.openclaw.enabled` (`OpenClawConfig` is already env-built at `env_config_loader.py:170-175`), pass through `SessionMonitorRegistry` into `SessionMonitor(intervention_router=…)`. ~15 LOC; makes the existing analysis honest.
(b) *Retire it.* Stop assigning `experiment_group` at launch, delete `backend/openclaw/` (257 LOC), `experiment/variant_router.py` (80), `AgentBackend`/`GROUP_TO_BACKEND`/`backend_for_group`/`parse_experiment_group`, `OpenClawConfig`, and `compute_experiment_analysis` + its route. Keeps the open/closed `ControlArm` contrast, which *is* implemented. ~−370 LOC.

### 3. `operating_curve` computes J from ground truth, not from detections — CRITICAL (research validity)

`evaluation/metrics.py:123-135` builds `sessions` for `total_J` as `regime = scn.truth_regime.value; dwell = snap.ts - scn.onset_ts`. `run_identifier` is called separately at `:141` and its detections feed only `evaluate()`. So `total_J` → `simulate_interventions` fires on an oracle; misses and false alarms never enter J.

**Verified by execution** on the admin fixture (12 struggle + 5 normal): `J = [32, 208, 384, 740, 1092, 1388, 1440, 1440, 1440, 1440]`, monotone increasing, `j_optimal.t_k == 0.0` for the admin 10-point grid, `cfg.eval_t_k_grid`, and both cost vectors. `c_false` has no effect (no false fires). Recall is already 0.0 at `t_k=60` while J keeps rising.

**Breaks:** `j_optimal_t_k` is surfaced on `GET /admin/overview`, `GET /admin/identifier-eval` and §3a of the defense export as the empirically chosen operating point. It is a constant independent of detector quality. `recall_at_opt` is therefore always the `T_k=0` recall of 1.0 — exactly the tautological number flagged as an integrity hazard. The confusion matrix is then computed at that oracle-chosen T_k.

**Fix:** build the `sessions` from the identifier's output — run the `DwellTracker`/`identify_regime` loop per snapshot and emit `{ts, regime: detected, dwell: detected}`. Keep the truth samples only as a `bad_duration` reference. If both are wanted, name them `J_oracle` and `J_realized` and select on the realized curve. **Capability preserved:** the criterion J, the grid, the cost model and the surfaced endpoints all stay; only the input to `total_J` changes from labels to detections, which is what the definition of J requires.

### 4. `LearningAnalyticsConfig` is unreachable from the environment — HIGH (PARTIAL: field is `config_model.py:356`, not `:293`)

`env_config_loader._build()` (`:138-204`) constructs `ConfigModel(database=…, redis=…, api=…, log=…, agents=…, openclaw=…, gns3=…, mcp=…, security=…, observability=…)` — `learning_analytics=` is absent, so the `default_factory` fires. Repo-wide search for `DWELL_THRESHOLD|MRT_ENABLED|COST_STUCK|COOLDOWN_PERIOD|EVIDENCE_CAPTURE|GROUNDING_ABLATION|SINGLE_AGENT|LATENCY_CAPTURE|L2_INTERVENTION` returns zero hits including deploy files and Makefile. The only mutation is in-process, at `backend/simulation/run.py:39-52`.

**Breaks:** every deployment runs `dwell_thresholds = {0,0,0,0}` (fire immediately), `cost_stuck = cost_intervention = 1.0`, `cost_false = 0.5`, cooldown 60s, `mrt_enabled=False`, evidence/latency/grounding capture off, `single_agent_mode=False`. `control/derive_thresholds.py` — the tool whose entire purpose is producing production T_k by minimizing J — has no way to deliver its answer short of editing `config_model.py`. Any claim that a run used derived T_k or had MRT on is unsupportable from the code.

**Fix:** add `learning_analytics=_build_learning_analytics(values)` reading `LA_ENABLED`, `LA_MRT_ENABLED`, `LA_MRT_HOLD_PROBABILITY`, `LA_COOLDOWN_PERIOD`, `LA_ANALYSIS_INTERVAL`, `LA_COST_{STUCK,INTERVENTION,FALSE}`, `LA_DWELL_THRESHOLDS` (JSON), `LA_EVIDENCE_CAPTURE_ENABLED`, `LA_LATENCY_CAPTURE_ENABLED`, `LA_GROUNDING_ABLATION_ENABLED`, `LA_SINGLE_AGENT_MODE`, `LA_ESCALATION_MAX_DWELL`, `LA_COHORT_HORIZON_DAYS`, `LA_L2_INTERVENTION_CAP`. Keep the Pydantic defaults as fallback, so behavior with nothing set is byte-identical to today. Then replace `simulation/run.py:39-52`'s in-process mutation with a sim env file.

### 5. gns3-service leaves `/sessions`, `/projects`, `/history` unauthenticated — HIGH

`main.py:144-150` includes seven routers. Only `exec_router` (`routers/exec.py:88`) and `templates_router` declare `dependencies=[Depends(verify_internal_token)]`; only `routers/ws.py:33-38` checks `?token=`. `routers/sessions.py:21`, `routers/projects.py:9` and `routers/history.py:13` are bare `APIRouter()` and there is no app-level dependency or auth middleware. Port 8101 is published (`docker-compose.yml:79-80`) and the prod overlay does not remove it.

**Breaks:** anyone reaching the port can call `POST /sessions/{id}/reset-password` (`routers/sessions.py:105-125`), which returns the plaintext `gns3_password` plus a fresh GNS3 JWT; read any session's history; and `DELETE /projects/{project_id}`. The per-user RBAC/ACL work inside GNS3 is unenforced at the service's own door.

**Fix:** move `verify_internal_token` into `routers/_deps.py` and attach at include time in `main.py` for sessions/projects/history (health stays open for the healthcheck; WS keeps its query-param variant). Use `secrets.compare_digest` in `exec.py:35` and `ws.py:35`.

### 6. One process-global `LogBuffer` serves every student — HIGH (cross-tenant)

`gns3-mcp/src/main.py:24-29` builds exactly one `LogBuffer` and one `GNS3Server` at module scope. `GNS3Server._ensure_log_buffer` (`server.py:247-263`) builds a ws_url from the caller's ctx and calls `ensure_connected`, which short-circuits when already connected (`log_buffer.py:40-42`) — so only the *first* caller's project and JWT are ever listened to. `get_errors`/`get_logs` (`log_buffer.py:79,96`) read one shared deque. Consumers: `backend/chat/router.py:122`, `backend/learning_analytics/context.py:99`, `collector.py:189`.

**Breaks:** student B's `list_errors` returns student A's project logs, which are then injected into B's tutoring context *and* into the LA feature vector — corrupting the exact signal the closed loop depends on.

**Fix:** key log buffers per `(user_id, project_id)`, mirroring the connection pool — a `dict[Key, LogBuffer]` in `GNS3Server` resolved in `_ensure_log_buffer`. While there, either implement `inactivity_timeout` (threaded from `config_model.py:34` to `log_buffer.py:20`, `_last_activity` written once at `:24` and never read) as the idle-close policy, or delete the knob.

### 7. Every rate limit falls back to the IP key — HIGH (PARTIAL: 6 of 7 limits; `/auth/exchange` has its own key_func)

`rate_limit.py:8-15` reads `request.state.user`; the only writer is `analytics/router.py:26`, inside the endpoint body. slowapi runs `_check_request_limit(request, func, False)` at `extension.py:735` *before* `await func(...)` at `:737`, so the key is computed first and the assignment never affects any request. `/auth/exchange` works only because `auth/router.py:96` uses a dedicated key fed by a stashing dependency — the codebase already knows the fix.

**Breaks:** `@limiter.limit("2000/minute")` on launch and `"5/second"` on node actions collapse into shared per-IP buckets; all dashboard traffic arrives through the Next BFF from one origin address. One noisy client rate-limits everyone; per-user abuse is unbounded until the shared bucket trips.

**Fix:** have `get_current_user`/`get_current_user_optional` take `request: Request` and set `request.state.user` — two lines that fix every decorated endpoint at once — then delete the misleading line at `analytics/router.py:26`. Separately decide whether `get_remote_address` should honour `X-Forwarded-For` given the BFF topology.

### 8. MRT bypasses the arm gate and corrupts the L2 holdout — MEDIUM (PARTIAL: latent — `mrt_enabled` is False outside `simulation/run.py:39`)

`learning_analytics/monitor.py:203-211`: `if self._learning_analytics_config.mrt_enabled: await self._mrt_step(...); return` — returning *before* the `ControlArm.OPEN` gate at `:217`. `_mrt_step` (`:587-628`) never reads `self._control_arm` and dispatches unconditionally on `assignment == 'intervene'`. `effective_arm` (`experiment/assignment.py:123-133`) returns OPEN for an L2 holdout session ("proactivity suppressed for everyone") and is the *only* mechanism enforcing it, since `_dispatch_intervention` never goes through `ControlInterface.act` (see #10). `l2_unassisted_pass` (`experiment/finalizer.py:43`) is `completed and interventions_received <= l2_intervention_cap`, cap defaulting to 0.

**Breaks (once MRT is turned on, which finding #4 is a prerequisite for):** every L2 near-transfer session receives real interventions with probability `1 - mrt_hold_probability`; one intervention flips `l2_unassisted_pass` to False; `l2_pass_rate_open/closed` and the cohort `reached_l2` criterion collapse toward zero, destroying the primary causal contrast and violating the stated unassisted-transfer protocol.

**Fix:** hoist the arm gate above the MRT branch — `if self._control_arm == ControlArm.OPEN: await self._log_would_intervene(...); return` (guarded by `_should_trigger_intervention`), then dispatch to `_mrt_step` or the closed path. Equivalently pass the arm into `_mrt_step` and force `assignment='withhold'` when OPEN, so the decision point is still logged for the hazard model but nothing is delivered. **Capability preserved:** the MRT randomization, its logging and the hazard model all survive; only delivery is suppressed in the arm that is defined as non-delivering.

### 9. `PATCH /users/me/sessions/{id}` accepts any status and appends a duplicate metrics row per call — HIGH

`LearningSessionUpdate.status` is a bare `str` (`sessions/schemas.py:13-16`). `update_session_endpoint` (`routers/commands.py:177-185`) calls `end_session` → `_mark_ended_and_finalize` (`lifecycle.py:101-102`), which unconditionally stamps status/`ended_at` and runs `_finalize_experiment_metrics` → `db.add(ExperimentMetrics(id=uuid4(), …))`. `models/experiment.py:18-20` and migrations 003/004/005 declare no unique constraint on `session_id`. The route stops no monitor, releases no slot, tears down no GNS3.

**Breaks:** any authenticated owner can inject N duplicate metric rows for one session, biasing `compute_arm_analysis`, cohort metrics and every defense export. The session also leaves a live `SessionMonitor` polling MCP and an orphaned GNS3 project.

**Fix:** delete the route (nothing calls it) or: constrain `status` to `Literal["ended","abandoned"]`, make `_mark_ended_and_finalize` a no-op when `ended_at` is set, add a unique index on `experiment_metrics.session_id`, and route through `end_lab`.

### 10. `ControlInterface.act()` has zero production callers — HIGH

`control_interface/interface.py:56` — grep across backend/gns3/mcp-sdk finds `.act(` only in `tests/unit/control_interface/test_interface.py`. The sole production construction is `sessions/monitor_registry.py:76`, and the monitor passes it only to `BehavioralCollector` for `observe` (`collector.py:107-110`). `_dispatch_intervention` (`monitor.py:375-380`) calls the orchestrator directly, and `monitor.py:235` writes `MCPAudit(kind='act', tool='intervention')` via `audit_record`, bypassing the seam that would have enforced the gates. The other real act path, `mcp_client.execute_action` at `lifecycle.py:145,155,156`, also bypasses it.

**Breaks:** `has_consent(…, ToolKind.ACT)` (only referenced inside `act()`), the open-arm suppression gate (`interface.py:71-73`) and the in-process rate backstop (`:74-79`) never run. The `MCPAudit` table contains `act` rows that passed no governance gate — the audit trail overstates what is enforced. A user who granted observe-only consent still receives LLM interventions.

**Fix:** route `_dispatch_intervention` through `ControlInterface.act` so consent/arm/rate are checked and the audit row is written by the seam that enforced them; and call `control_interface.act('execute_action', …)` from `lifecycle.py:145-156`. If neither is wanted, delete `act`, `ToolKind.ACT`, the `execute_action` registry entry, and stop claiming an act gate. **Capability preserved either way** — the gates are currently no-ops, so wiring them is the only change that adds enforcement; deleting them removes only documentation of enforcement that never happened.

### 11. The IDLE regime cannot fire online — HIGH (research validity)

`learning_analytics/monitor.py:167-168`: `events = await self._load_new_events(db); if not events: return`. With no new events the cycle produces no `ProcessStateSample` and no dwell, so a genuinely idle student advances nothing. `features._inter_action_latencies` uses only adjacent-event gaps — there is no now-minus-last term — and `idle_periods` (`features.py:38`) counts gaps > `idle_gap_seconds = 60`. When `LabProgressObserver` is attached (which `monitor_registry.py:61` does for every GNS3 session) `diff_snapshots` emits `check_failing` every cycle while any check stays failing-unchanged (`progress_observer.py:84-96`) at a 25s poll interval, so gaps never exceed 60s and `idle_periods` stays 0. `simulation/run.py:44-47` has to override three knobs just to make it fire, with the comment "in a compressed run idle periods never accumulate".

**Breaks:** one of four regimes of the controlled process is effectively unobservable in production. `ProcessStateSample` will contain almost no `idle` rows, starving `derive_thresholds` of data for `T_k['idle']`; `dwell_thresholds['idle']`, `_STRUGGLE_QUESTIONS['idle']` and the IDLE row/column of the 5×5 confusion matrix describe a branch real sessions never reach.

**Fix:** make the analysis cycle time-driven — when `_load_new_events` is empty, still call `identify_regime` on the previous feature vector with an updated `now` so `_log_process_state` advances dwell. Compute `idle_periods` from student-originated events only, excluding the observer's `check_*` heartbeat. **Capability preserved:** the rule list, the dwell tracker and the control law are untouched; only the trigger for a cycle and the event filter for one feature change, which makes an already-declared regime reachable rather than adding a new one.

### 12. `reset_lab` picks the wrong GNS3 template column for `-frr` labs — MEDIUM

`sessions/services/launch.py:84/91/96` branches three ways (`-ccna` → `gns3_template_project_id_iosvl2`, `-frr` → `…_frr`, else `…`). `sessions/services/lifecycle.py:166-169` branches only two (`-ccna` → iosvl2, else default). An `-frr` lab therefore resets against a column that is typically NULL. **Caveat:** no `-frr` slug exists in-repo (labs come from the DB), so triggering depends on prod data.

**Fix:** extract the three-way selection into one `template_project_id_for(lab)` helper in `labs/service.py` and call it from both, raising the same explicit `ValueError` when the column is unset.

### 13. `exec_vtysh` MCP tool always 403s — MEDIUM

`gns3-mcp/src/domain_tools.py:255-256` posts `/v1/exec/vtysh` with no headers; `gns3-service/src/routers/exec.py:88` attaches `verify_internal_token`, which 403s a missing bearer (`:31-36`). `rg INTERNAL_API_TOKEN gns3/gns3-mcp/` returns nothing and `docker-compose.yml:124-128` passes only `MCP_*`/`GNS3_SERVICE_URL`. The unit test mocks a 200 and asserts no header, so it passes. **Smaller blast radius than first reported:** no in-repo caller invokes the MCP tool — the backend uses its own authenticated `gns3_service_client.py:90`, and `control_interface/registry.py`'s allowlist omits it. So the tool is dead-on-arrival rather than breaking live traffic; the docstring's claim that agents observe device state "through MCP instead of a telnet bypass" is contradicted by `backend/chat/tools.py:61`, which does the telnet bypass.

**Fix:** add `internal_api_token` to `GNS3MCPConfigModel`/`EnvConfigLoader`, pass `INTERNAL_API_TOKEN` to the container, send the bearer, reuse one module-level httpx client, and assert the header in the test.

### 14. History events are published twice — MEDIUM

`gns3_ws_proxy.py:202` persists to `history_events` and `:206` publishes `_translate(action, …)`, which returns a `history.event` envelope for `link.created|link.deleted|node.created|node.deleted` (`:245-253`). Migration `e5bb89c9af4d:38-45` installs an `AFTER INSERT` trigger that pg_notifys the same row, and `history_listener_pg.py:106-115` publishes a second identical envelope to the same stream. Both run in prod (`main.py:102`; `alembic upgrade head` in the container CMD). The only consumer is the passthrough relay `backend/sessions/ws/events.py`, so the impact is duplicate UI events (not double-counted analytics). Envelopes carry no id to dedupe on.

**Fix:** make `_translate` return `None` for the four history actions and let the PG listener be the sole publisher — it carries the persisted row, so replay and live stream agree. −12 LOC.

### 15. `WebSocketGateway` orphans displaced sockets — MEDIUM

`sessions/ws/gateway.py:52-53` overwrites `_connections[sid]` and registers into the module-level `_active_connections`; `disconnect` early-returns at `:60-61` when `current is not websocket`, never unregistering the displaced socket. `routers/ws.py:44-49` disconnects only inside `except WebSocketDisconnect` — no `finally` — so a cancelled task leaks both entries. With two tabs open, the first tab silently stops receiving interventions.

**Fix:** make `_connections` a `dict[str, set[WebSocket]]` and fan out (mirroring `_observers`, which already does), or close+unregister the displaced socket in `connect`. Wrap the receive loop in `try/finally`.

### 16. gns3-service's WS handler never notices an idle disconnect — MEDIUM

`routers/ws.py:97-99` checks `recv_task.done()` only inside the `async for` body; `events_broker.py:45-62` loops on `xread(block=5000)` and `continue`s without yielding when empty. On an idle session the check never runs, `send_pings` (`ws.py:79-91`) swallows its send failure and returns, and nothing cancels the coroutine — so the `finally` at `:105` is unreachable until an event arrives. Every abandoned tab on a quiet session leaves a handler plus a 5s Redis poll, forever.

**Fix:** race the two with `asyncio.wait([recv_task, forward_task], return_when=FIRST_COMPLETED)` and cancel the loser, or have `subscribe` yield `None` on block-timeout so the existing check is evaluated.

### 17. `build_client()` creates a fresh `AsyncOpenAI` per request and never closes any — MEDIUM

`core/llm/client.py:18-30` — no cache. Called per chat request at `chat/router.py:401` and per model build at `agents/base.py:28`, with `_agent_for` building a new pydantic-ai `Agent` per run (`tutor/agent.py:49`, `hint/agent.py:53`). No `aclose` anywhere for these. **Nit from verification:** nothing retains them, so they are GC-eligible; the real cost is a fresh httpx pool and TLS handshake per LLM call, not unbounded growth.

**Fix:** `@lru_cache` a `_client_for(model_id)` helper (creds are static after config load), or build one per `provider_ref` in `lifespan` and close on shutdown.

### 18. Public `/auth/register` self-activates while GitHub sign-up does not — MEDIUM

`auth/router.py:36` has only `@limiter.limit("3/minute")` — no `require_internal_caller`, no admin guard. `auth/service.py:56` hardcodes `is_active=True`; `models/user.py:40` defaults False, which is the path `upsert_github_user` takes. `require_active_user` (`auth/dependencies.py:132`) gates `POST /sessions` (`commands.py:52`) and `POST /chat/stream` (`chat/router.py:363`). A comment at `service.py:53-55` calls this the "tests/internal path" but nothing enforces that.

**Fix:** default `create_user` to `is_active=False` and let the already-internal `/auth/activate` be the single activation path — or delete the gate. Two contradictory policies is the one option that should not survive.

### 19. `AgentActivityLog.emit` spawns an unreferenced task per event that runs a full retention scan — MEDIUM

`observability/activity.py:43` — `asyncio.create_task(self._persist(event))` with no reference kept (RUF006 is in the ignore list, `pyproject.toml:60`), and `_persist` awaits `_prune` at `:65` on *every* event, which runs `SELECT id … ORDER BY ts DESC OFFSET 2000` plus a conditional DELETE. A chat turn with 3 tool calls emits ~9 events (`chat/router.py:321,331,387,404,421`).

**Fix:** push onto an `asyncio.Queue` drained by one background writer owned by `lifespan` (which also gives a place to await outstanding writes on shutdown); run `_prune` every Nth insert or on session end.

### 20. The MCP pool serves a stale GNS3 JWT after a re-launch — MEDIUM

`gns3-mcp/src/connection.py:13-22` bakes `ctx.metadata['gns3_jwt']` into the cached client's static headers; `mcp_sdk/connection.py:82-84` keys on `(environment_url, user_id)` only; `_is_alive` (`:133-137`) short-circuits to True for `health_check_interval` (60s). `launch.py:14` allows 2 sessions/user and `session_lifecycle.py:85-99` deletes and re-creates the deterministic student user (`gns3_identity.py:9`), rotating the JWT.

**Fix:** include a hash of the JWT in the pool key, or stop baking the token in and pass `Authorization` per request from ctx. Window is bounded and self-heals, but it hits the tutor's grounding path.

### 21. `users.default_model_id` is write-only — MEDIUM

Column at `models/user.py:39`, migration `482644690a75`, read/written only in `users/router.py:16/20/28/40-52`. `resolve_chat_model` (`chat/router.py:88`) consults body → `session.model_id` → `cfg.chat_model` and never loads the User row; `models/session.py:30` `model_id` defaults to None and is never seeded from the user. `chat/router.py:79` returns the global default.

**Fix:** insert the preference into the precedence chain (request > `user.default_model_id` > `session.model_id` > config) and return it from `/chat/models` — or delete the column and the endpoints.

### 22. WS proxy locks orphan for an hour after an unclean shutdown — MEDIUM

`gns3_ws_proxy.py:43` `_LOCK_TTL_SECONDS = 3600`; `SET nx` at `:82-88`; "already owned … skip" returns early at `:94`; only `stop_project` (`:145`) deletes the key, reached solely from the lifespan shutdown (`main.py:125`). On SIGKILL/OOM the key survives, and `main.py:89-90`'s re-attach loop then skips every active session (also affecting `routers/ws.py:62` and `session_lifecycle.py:142,229`). Live sessions stop receiving GNS3 events and stop persisting history for up to an hour, with one INFO log.

**Fix:** put an instance id in the lock value and allow takeover from a dead/older instance — or drop the Redis lock while the deployment is single-replica and rely on the in-process `_tasks` guard at `:79`, which also removes ~25 LOC of heartbeat machinery.

### 23. `GET /labs` returns disabled labs — LOW (PARTIAL: proposal corrected)

`labs/service.py:8-15` has no `enabled` filter; `LabResponse` (`labs/schemas.py:45-57`) omits the field, so the client cannot filter either; `launch.py:81` then raises "Лаба отключена" → 400 (`routers/commands.py:94`). **Correction to the original proposal:** `admin/router.py:391/418/437` calls the *same* `get_all_labs`/`get_lab_by_slug`, so filtering inside those functions would hide disabled labs from the admin list and 404 the re-enable PATCH. Put the filter in `labs/router.py` or behind an explicit flag parameter.

### 24. Simulated ground truth is written into the human annotation table — LOW (PARTIAL: latent)

`simulation/ground_truth.py:16-22` inserts `RegimeAnnotation(coder_id='sim-truth', is_gold=True, …)` — the same table and flag as human adjudicated labels — and it is live (`simulation/run.py:379`). `gold_label_count` (`evaluation/annotation.py:41`) filters only on `is_gold`; `inter_rater_kappa` (`:31`) would treat `sim-truth` as a coder. **Not currently triggerable:** both have zero production callers, and the one production gold count (`reproducibility.py:38`) uses its own session→user→`is_simulated` firewall. Fix before those get surfaces (see Dead code / "wire, don't delete").

**Fix:** hoist `SIM_TRUTH_CODER` into `evaluation/annotation.py` and exclude it in the three queries; longer term add an explicit `source` column rather than overloading `coder_id`.

---

## Dead code

Verified zero production callers. "Tests-only" means the only importers are `tests/` or `autotests/`.

| Symbol / module | Location | Proof | LOC |
|-|-|-|-|
| `backend/openclaw/` (client + adapter) | `openclaw/client.py:1`, `openclaw/adapter.py:1` | never instantiated outside tests; only importer is the dead `variant_router` | 257 |
| `ExperimentVariantRouter` + `AgentBackend`/`GROUP_TO_BACKEND`/`backend_for_group`/`parse_experiment_group` | `experiment/variant_router.py:17` | only `tests/unit/experiment/test_variant_router.py`; carries its own TODO | ~110 |
| Two dead lab build scripts + appliance importer | `gns3-service/scripts/build_lab_template.py:1`, `build_iosvl2_lab_template.py:1`, `import_appliance.py:1` | `_BUILD_SCRIPTS` (`routers/templates.py:26-31`) maps 4 slugs to 3 *other* scripts; no reference in any .py/.md/Makefile/Dockerfile/.sh/.yml | 448 |
| `topology_builder.configure_switch_vlans` / `resolve_port` / `get_node` | `gns3-service/scripts/lib/topology_builder.py:177,135,129` | used only by the two dead scripts above | ~80 |
| `routers/projects.py` + `admin.create_project`/`list_projects` + `ProjectCreate`/`ProjectResponse` | `gns3-service/src/routers/projects.py:1`, `clients/admin/projects.py:13,23` | only autotests + gns3-service's own unit tests; `backend/gns3_service_client.py` never calls `/projects` | ~90 |
| `POST /sessions/{id}/reset-password` + `PasswordResetResponse`; `GET /sessions/{id}` + `models.SessionStatus` | `gns3-service/src/routers/sessions.py:105`, `:46`, `src/models.py:56` | only `autotests/api/api_methods/gns3_service/gns3_sessions_api.py:60-66`; state endpoint already returns status. **Note:** `src/models.py:56 SessionStatus` is a *different* symbol from the heavily used `src/db/models.py:14` enum | ~60 |
| `models/enums.py` (all 5 enums) + re-exports | `backend/models/enums.py:1`, `models/__init__.py:8` | zero importers; `SessionStatus` = active/completed/abandoned contradicts the real vocabulary written at `launch.py:32,113`, `query.py:72` and declared at `sessions/schemas.py:116` | 51 |
| `TutorTools`, `AnalyticsTools` | `agents/tutor/tools.py:4`, `agents/analytics/tools.py:10` | `self.tools` assigned at `tutor/agent.py:30` and never read (`run()` at `:42-63` uses only `_agent_for`); `AnalyticsTools` not even imported by its own agent | 98 |
| `session_launches_counter`, `provisioning_duration_histogram`, `queue_depth_gauge` | `observability/metrics.py:11,16,22` | no `.inc()`/`.observe()`/`.set()` anywhere, incl. by metric-name string. (Contrast `active_sessions_gauge` at `commands.py:105`) | ~20 |
| `ActivityKind.ANALYSIS_CYCLE`, `.CONTEXT_BUILT` | `observability/models.py:22,26` | neither the members nor their string values appear elsewhere; none of the 12 `event_*` helpers emit them | ~5 |
| `AGENTS_TEMPERATURE` / `AGENTS_MAX_TOKENS` / `AGENTS_REQUEST_TIMEOUT`; `ApiConfig.api_port`, `.debug` | `config_model.py:115-117,47,48`; loaded at `env_config_loader.py:69-71,132-134,163-164` | `chat/router.py:244` builds `create_kwargs` = model/messages/stream(+tools); `agents/base.py:19` and `core/llm/client.py:26` pass no settings/timeout. Effect: no client-side timeout on any LLM call | ~14 |
| `ControlInterface.act` + `ToolKind.ACT` + `execute_action` registry entry | `control_interface/interface.py:56`, `registry.py:22` | `.act(` only in `tests/unit/control_interface/test_interface.py` | ~45 |
| `ConnectionPool.start/close`, `ConnectionPool.release`, `LogBuffer.close` | `mcp_sdk/connection.py:73,124,118`; `gns3-mcp/src/log_buffer.py:104` | `start`/`close` have zero callers incl. tests; `release`/`LogBuffer.close` tests only. `gns3-mcp/src/main.py:17-55` has no lifespan/atexit. `start()` only re-inits the dicts `__init__` already set | ~30 |
| `StateCache` dict-compat shims (`keys/items/pop/__getitem__/__contains__/__setitem__`, `ttl`) | `gns3-service/src/services/state_cache.py:23-24,51-68` | no `src/` caller; only `tests/test_service_actions.py:25,36` | ~25 |
| `harvest_open_arm_sessions`; `labeled_real_count`; `LabeledScenario.source='real'` | `evaluation/real_loader.py:26,21`; `evaluation/scenarios.py:26` | `harvest_…` has zero callers incl. tests; `source='real'` is passed only in `tests/unit/evaluation/test_real_loader.py`; `scripts/eval_identifier.py:94` hardcodes `labeled_real_n = 0`, making the `< 10` branch at `:154` constant | ~40 |
| Sim command-generation seam: `_CMD`, `_default_command_for`, the `command_for` param, `cmd=` arg; `Actor` Protocol | `simulation/orchestrator.py:16-25,44,81`; `simulation/env/actor.py:8` | no caller passes `command_for` (`run.py:381-390` omits it); `GNS3Actor.execute` (`gns3_actor.py:56-80`) ignores `cmd` and takes commands from `task.correct_cmd`/`wrong_cmd`; `Actor` has zero importers | ~40 |
| `.aes` decrypt branch in both gns3 config loaders | `gns3-service/src/config/__init__.py:35`, `gns3-mcp/src/config/__init__.py:35` | no `ENV_FILE` anywhere points at `.aes`; `gns3/Makefile:101-108` and both deploy workflows call `openssl` directly | ~30 |

**Total straightforwardly deletable: ~1,440 LOC**, before the consolidation wins below.

### "Wire, do not delete" — ~230 LOC of good research code with no surface

These are required capabilities that are unreachable, not dead weight. Their only callers are unit tests, which gives the false impression the pipeline is end-to-end.

| Capability | Location | Missing surface |
|-|-|-|
| IRR / Cohen's kappa, gold-label count | `evaluation/annotation.py:9,31,41` | `GET /admin/annotation-irr` |
| Anonymised reproducibility bundle | `evaluation/reproducibility.py:18` | `GET /admin/reproducibility-bundle` |
| Help-dependence trajectory (MRT secondary endpoint) | `evaluation/help_dependence.py:12` | a `## Help-dependence` section in `scripts/export_defense_metrics.py` |
| Cycle-latency percentiles | `learning_analytics/latency.py:32` | a `## Latency` section calling `stage_percentiles(db, 'analysis', [50,95,99])` |
| Kaplan-Meier retention | `cohort/metrics.py:260` (`retention_metric`, `RetentionMetric`, `RETENTION_NOTE`) | a `## Retention` section |
| Grounded/ungrounded pair generation | `evaluation/grounding.py:16` | see the note below |

**Correction to one surveyor claim (PARTIAL):** `monitor._maybe_grounding_ablation` (`monitor.py:441`) does *not* re-implement `generate_grounding_pair`. It reuses the already-dispatched `pending.response` for the grounded side and makes one extra call; `generate_grounding_pair` makes two. Swapping in the helper would double the LLM interventions per ablation. The only real duplication is the 2-line hint extraction and its `data['text']` fallback — hoist `_hint_text` and use it in both, nothing more.

**Correction on `gold_label_count` (PARTIAL):** `reproducibility.py:36-41` is *not* the same query — it adds the sim-session firewall that `gold_label_count` lacks. Do not swap one for the other without carrying the exclusion over (and see bug #24).

---

## Overengineering and simplification

Ranked by (LOC + cognitive load removed) × safety.

### S1. The GNS3 action surface is written out three times — −170 LOC (PARTIAL: proposal needs care)

**Now:** `gns3-mcp/src/server.py:54-137` is an 84-line `ACTIONS: list[dict]` of 17 operations; `:297-341` is a 52-line `match action_name` re-listing the same 17 and hand-unpacking their params to call the same `GNS3ApiClient` methods; `domain_tools.py:29-175` is a 147-line `_SIMPLE_TOOLS` tuple of 22 operations (a strict superset) whose `_build_simple_tool` (`:186-192`) already does the generic `getattr(client, spec.api_method)` dispatch the match statement does by hand.

**Should be:** one table. `ACTIONS`/`list_available_actions` becomes a comprehension over `_SIMPLE_TOOLS`; `execute_action` becomes `getattr(api, spec.api_method)(pid, *ordered_params)` with the same `KeyError → ActionExecutionError` mapping.

**Behavior preservation — three things must be carried across, or it is not a refactor:** (1) `ACTIONS` descriptions are Russian and `_SIMPLE_TOOLS` are English — the agent-facing text must not silently change language; (2) `component_types` exists only on `ACTIONS` and drives the `list_available_actions` filter (`server.py:270-284`) — it becomes an extra field on the spec; (3) deriving from the superset would add 5 actions (`lock`/`unlock`/`duplicate_project`, `reset_console`, `create_node_from_template`) to the `ActionSpec` surface — decide explicitly whether to include or exclude them.

### S2. mcp-sdk's protocol auto-discovery — −160 LOC (PARTIAL)

**Now:** four `@runtime_checkable` Protocols (`mcp_sdk/protocols.py:20`), `_validate_minimum` (`server.py:64-70`) and `_discover_and_register` (`:74-93`) isinstance-checking them, and five `_register_*` methods, all serving exactly one implementation — `GNS3Server` (`gns3-mcp/src/server.py:140`) — which satisfies all four, so every branch always fires. `runtime_checkable` isinstance checks method *names* only, so the "validation" cannot catch a signature mismatch. This is the textbook shallow module: the interface is as large as the body it hides.

**Should be:** one flat table `(tool_name, impl_method, extra_params, …)` plus a single loop that builds the closure — the shape `domain_tools.py` already uses. Keep `_tool_errors`; keep `get_capabilities`, deriving `capabilities` from which impl methods exist.

**Corrections:** `README.md:278` documents `from mcp_sdk import OnlinetlabsMCPServer` as the public API, so the `__init__.py` barrel is referenced by docs even though no in-tree code imports it — keep or deprecate deliberately. `__all__` has 24 names, not 25. `list_errors`/`get_logs` parse `since` and `LogLevel`, so a bare 4-tuple table will not cover them; they need a per-tool argument adapter.

### S3. Config bootstrap + observability duplicated across services — −180 LOC

**Now:** `_resolve_env_file` + `.aes`/`CONFIG_PASSWORD` handling + `@lru_cache(maxsize=1)` loader + `_LazySettings` + `settings = _LazySettings()` appears verbatim three times (`backend/config/env_config_loader.py:207+`, `gns3-service/src/config/__init__.py:12`, `gns3-mcp/src/config/__init__.py:11`). `sentry.py` differs between backend and gns3-service by one docstring line. Logging has already drifted: backend uses structlog contextvars and disables `uvicorn.access`; gns3-service uses a hand-rolled ContextVar plus `_add_request_id` and *propagates* `uvicorn.access` while its middleware also logs `request_handled` — so gns3-service logs every request twice (its Dockerfile has no `--no-access-log`). **Correction:** gns3-mcp has no observability module at all, so this is 2× for logging/sentry and 3× for the config bootstrap.

**Should be:** `mcp_sdk.observability` (logging, sentry, request_id) and `mcp_sdk.config_bootstrap` (`resolve_env_file`, `lazy_settings(loader)`), parameterised by service name/environment. Each service keeps only its own `config_model.py` and `env_config_loader._build`. Adopt the backend's structlog-contextvars variant (the one without the double access log). gns3-service does not currently depend on `mcp_sdk` — add it to the workspace deps. Keep the metrics modules separate: `platform_*` and gns3-service's metric sets are genuinely different domains.

### S4. The env encrypt/decrypt CLI exists three times and has drifted — −150 LOC

**Now:** `backend/tools/env_cipher.py:33`, `gns3-service/src/config/encryption.py:30`, `gns3-mcp/src/config/encryption.py:31`. `diff` of the two gns3 copies shows exactly one difference: gns3-service writes `filepath.removesuffix('.aes')` and leaves the plaintext next to the ciphertext; gns3-mcp uses `tempfile.mkstemp` + `atexit.register(unlink)`. All three shell out with `-pass pass:{password}`, putting the config password in argv.

**Should be:** one `mcp_sdk.env_cipher`, keeping the tempfile+atexit variant, and `-pass fd:N` or an env-var pass source. **Note (PARTIAL):** in-place decryption is currently the repo *norm* — `gns3/Makefile:101-108` and the deploy workflows also leave plaintext on disk — so consolidating on the tempfile variant is a deliberate behavior change (a good one), not a pure refactor. Also: the `.aes` Python branch is currently unreachable in all three services, so this can be a straight delete instead if the Makefile path is the only one you intend to support.

### S5. The cohort result shape is written out four times — −110 LOC

**Now:** four dataclasses in `cohort/metrics.py:26+`; a field-for-field Pydantic mirror at `instructor/schemas.py:107-177` whose docstrings literally say "Mirror of the … dataclass", plus `_cell_schema`/`cohort_response_from_result`; two hand-rolled markdown emitters each with their own `_fmt_days` (`scripts/export_cohort_metrics.py:10`, `scripts/export_defense_metrics.py:36`) that already differ (6 vs 7 columns); and `admin/router.py:186-189` reaching into the dataclass with a comment explaining it is not a dict.

**Should be:** make the four cohort types `pydantic.BaseModel` (they are pure data, no behaviour) and delete `instructor/schemas.py:107-177` — `CohortMetricsResponse` composes the domain models directly. Extract the shared table emitter into `cohort/report.py`.

**Behavior preserved:** no `dataclasses.asdict` usage exists anywhere in the tree, so the swap has no serialization side effects; the two markdown emitters keep their own column sets by passing a column list.

### S6. Synthetic research fixtures triplicated, with divergent grids and costs — −140/+35 LOC

**Now:** the scenario builder appears at `admin/router.py:54`, `scripts/eval_identifier.py:38` and `scripts/export_defense_metrics.py:40`; the session builder at `admin/router.py:70`, `export_defense_metrics.py:56` and `control/derive_thresholds.py:188` (two of them carrying "mirrors derive_thresholds.__main__"). Inputs diverge: `admin/router.py:48` uses a 10-point `_T_K_GRID` while both scripts use the 6-point `cfg.eval_t_k_grid`; `eval_identifier.py:88` hardcodes `Costs(1.0, 1.0, 5.0)` while the other two derive from config (`c_false=0.5`). **Correction:** `eval_identifier.py` does use `cfg` — it passes `cfg.eval_t_k_grid` and `cfg` at `:100`; only the costs are hardcoded.

**Should be:** `build_synthetic_scenarios()`/`build_synthetic_sessions()` in `evaluation/scenarios.py` (where `make_struggle_scenario`/`make_normal_scenario` already live), plus `costs_from_config(cfg) -> Costs` next to `Costs` in `control/criterion.py`. One grid (`cfg.eval_t_k_grid`) everywhere. Delete `derive_thresholds.__main__` in favour of `export_defense_metrics.py` §4, which already produces the same table.

**Behavior preserved:** identical fixture, identical J computation. The admin dashboard's numbers *will* change because it currently uses a different grid — that is the point: three artefacts a reader treats as the same experiment stop disagreeing.

### S7. Two agents encoded in three lookup tables plus a per-run pydantic-ai Agent — −70 LOC (PARTIAL)

**Now:** `AGENT_REGISTRY` maps 2 names (`agents/registry.py:12-15`); `INTENT_TO_AGENT` maps 3 intents onto the same 2 (`agents/orchestrator/router.py:3-7`); `Orchestrator._LLM_AGENTS = frozenset({'tutor','hint'})` restates the set a third time (`orchestrator/agent.py:49`); `_get_agent` then re-special-cases by class identity (`:40`). `INTENT_TO_AGENT['hint']` is unreachable — `resolve_agent`'s only production caller is `agent.py:65` with `f"intervene_{...}"`. Separately, `BaseAgent._agent_for` (`base.py:19`) builds a fresh `pydantic_ai.Agent` with only `model` and `system_prompt`, and both callers read only `result.output` (`tutor/agent.py:51`, `hint/agent.py:60`) — no tools, no structured output, no deps — while `chat/router.py:249` calls `client.chat.completions.create` directly on the same `build_client`.

**Should be:** one `AGENTS: dict[str, AgentSpec]` holding class, input model and an `is_llm` flag, keyed by the intent string already in use. Drop `INTENT_TO_AGENT`, `_LLM_AGENTS`, the `resolve_agent` wrapper and the dead `'hint'` key. Replace `_agent_for` with a direct `completions.create` using `build_client`, so both halves of the system share one LLM path; `pydantic_ai` is imported in exactly one file, so the dependency can then go.

**Caveat:** this is the one entry where "behavior preserved" needs a caveat — pydantic-ai and the raw client can differ in how they assemble the system prompt. Verify the produced messages match before removing the dependency. Lower priority than everything above it.

### S8. Two `load_lab_spec` implementations; `sessions/service.py` vs `sessions/services/` — −60 LOC (PARTIAL)

**Now:** `labs/spec.py:8` reads `validation/labs/{slug}.yaml` uncached and is used by `chat/router.py:415` (i.e. re-parses YAML synchronously on the event loop for every chat request); `validation/runner.py:34` reads the same path with an mtime cache and is used by `validation/service.py:72`, `learning_analytics/progress_observer.py:169`, `sessions/services/lifecycle.py:56` and `simulation/run.py:99,187`.

**Should be:** delete the loader in `labs/spec.py`, import the cached one, keep only `expected_vpcs_config` there.

**Correction — the second half of this finding was wrong:** `backend/sessions/services/__init__.py` is a 0-byte file that exports nothing, so `sessions/service.py` is *not* a redundant duplicate of it and the proposed "point callers at `sessions.services`" would `ImportError`. Five modules import `sessions.service` (`escalation/router.py`, `chat/router.py`, `sessions/routers/commands.py`, `queries.py`, `ws.py`, plus `simulation/run.py:95`). The near-identical-name confusion is real; the fix is to pick a name (`sessions/api.py`, or populate `services/__init__.py`) — not to delete the barrel.

### S9. Template building via subprocess + regex over stdout — −60 LOC (PARTIAL)

**Now:** `routers/templates.py:41-71` spawns `sys.executable <script>` and recovers the result with `_UUID_RE.findall(decoded)[-1]` — the last UUID-shaped substring anywhere in stdout — with a 600s timeout held by the request. The scripts re-authenticate to GNS3 with their own `httpx.Client` and their own `GNS3_ADMIN_USER/PASSWORD` reads (`build_lan_static_ip_template.py:19-21,28-30`) while the service already holds an authenticated admin client. `backend/admin/router.py:413` calls this over HTTP.

**Should be:** `build_template(admin_client, force)` called directly from the route as a background task keyed by lab slug.

**Corrections:** asyncio reaps killed children, so there is no zombie (the original claim overstated it); and `scripts/lib/topology_builder.py` is 281 LOC of *sync* httpx while `_admin` is async — so this needs a threadpool hop or an async rewrite, not just passing the client. Medium effort, not a free win.

### S10. Session state TTL-cached on both sides of the same seam — −25 LOC

`gns3-service/src/services/session_lifecycle.py:56` builds `StateCache(ttl_seconds=5.0)` feeding `state_snapshot.py:35,87` behind `routers/sessions.py:90`; `backend/main.py:118` builds a *differently implemented, identically named* Redis-backed `StateCache(redis, 5)` used at `sessions/services/query.py:59,91` in front of that same endpoint. "How stale can node status be?" has no single answer. Both layers invalidate on mutating actions, so the doubled staleness mainly bites out-of-band GNS3 changes. Pick the Redis one (it survives multiple gns3-service replicas) and reduce the other to pass-through.

### S11. `gns3/Makefile` still drives everything through poetry — −12/+10 LOC

`gns3/Makefile` lines 54,55,58,61,65,69,70,91,94,97 run `poetry install|run`. Neither gns3 `pyproject.toml` has a `[tool.poetry]` section, there is no `poetry.lock` in `gns3/`, the root declares a uv workspace, both Dockerfiles use `uv sync --frozen --package`, and `.github/workflows/ci.yml:45` uses `uv sync --locked`. Every documented local workflow for this subtree — install, serve, serve-mcp, test, lint, migrate — is stale, and `make test` runs only the gns3-mcp suite while gns3-service's 15 test files have no target.

**Fix:** `uv run --package gns3-service …` / `--package gns3-mcp-server …`, and make `test` run both suites.

---

## Architecture

The deep-module criterion: a module earns its keep when its **interface is much smaller than the implementation it hides**. Applying it:

**Genuinely deep, leave alone.** `mcp_sdk.connection.ConnectionPool` — small surface (`acquire`/`release`), real LRU + TTL + health-check behind it. `mcp_sdk` shared models + `SessionContext` — used by the backend too, correctly placed. `mcp_sdk.testing` TMS bridge — widely used. `backend/validation/` and `learning_analytics/features.py` — small interfaces, real logic. The three exception hierarchies (`mcp_sdk.errors`, gns3-service exceptions, backend auth exceptions) are genuinely per-domain and should stay separate.

**Shallow — interface ≈ implementation. Collapse:**

| Module | Problem | Action |
|-|-|-|
| `mcp_sdk/protocols.py` + `server._discover_and_register` | 4 Protocols + 5 register methods for 1 implementation that satisfies all four (S2) | Replace with one table + one loop. Interface after: `OnlinetlabsMCPServer(name, implementation)` — unchanged. |
| `backend/labs/spec.py` | one uncached YAML read duplicating `validation/runner.py:34` (S8) | Delete the loader, keep `expected_vpcs_config` |
| `gns3-service/src/config/encryption.py` ×2, `backend/tools/env_cipher.py` | three copies of one `openssl` shell-out (S4) | One `mcp_sdk.env_cipher`, or delete the unreachable branch entirely |
| `instructor/schemas.py:107-177` | 70 LOC whose only job is to restate `cohort/metrics.py` (S5) | Delete; make the dataclasses `BaseModel` |
| `simulation/env/actor.py` | a Protocol with zero importers guarding one implementation | Delete, or make `run_cohort` actually type against it |

**Packages to merge or rename.** `mcp-sdk` is the right shared home for cross-service code and is **under-used**: it should absorb `observability` (logging/sentry/request_id) and `config_bootstrap` (S3), and `env_cipher` (S4). `gns3-service` needs to be added as a dependant. That single move deletes ~330 LOC of triplication and gives the drifted logging one definition.

**Packages to split by name, not by code.** Four packages collide semantically: `backend/analytics/` is browser telemetry ingest (one `POST /analytics/events`, `analytics/router.py:16`), `backend/learning_analytics/` is the online control loop, `backend/agents/analytics/` is the regime identifier (`agents/analytics/agent.py:25` `STRUGGLE_RULES`), and `backend/evaluation/` + `backend/experiment/analysis.py` are two different offline statistics layers. Rename: `analytics/` → `telemetry/`, `agents/analytics/` → `agents/identifier/` (its public symbol is already `identify_regime`), and fold `experiment/analysis.py` under `evaluation/` so there is one offline-statistics home.

**The one module that should be created.** There is no single place that answers "under what conditions does a proactive intervention reach a student?" Today the answer is spread across nine locations in seven files: `config/config_model.py` (enabled, cooldown, dwell thresholds, mrt_enabled), `monitor.py:164` (`_run_analysis` ordering), `monitor.py:~553` (`_dwell_ready`), `monitor.py:567` (`_should_trigger_intervention`), `monitor.py:587` (`_mrt_step`), `learning_analytics/process_state.py:24` (`is_bad`), `agents/analytics/agent.py:25` (first-match rule list), `experiment/assignment.py:123` (`effective_arm`/L2 holdout), and `control_interface/interface.py:56` (an act gate that turns out not to apply).

Extract `learning_analytics/control_law.py::should_intervene(regime, dwell, arm, last_intervention_at, cfg) -> Decision(intervene|withhold|log_only|skip, reason)`. Both the CLOSED path and `_mrt_step` call it; `monitor.py` then only collects, calls the law, and dispatches. This is the single highest-leverage readability change in the repo, and it structurally fixes bug #8 (the arm gate cannot be bypassed if it lives inside the law). **Capability preserved:** every existing branch becomes a `Decision` variant with the same conditions; nothing is added or removed, and the `reason` field makes the currently-implicit provenance explicit.

**Regime vocabulary: five declarations, two definitions of "bad".** `StruggleType` (`agents/analytics/models.py:36`), `ProcessRegime` (`learning_analytics/process_state.py:7`, docstring "mirrors StruggleType"), `BAD_REGIMES` as a literal string set (`control/criterion.py:27`), `TrueRegime` (`simulation/policy.py:26`), the `dwell_thresholds` default keys (`config_model.py:250-253`) and `_STRUGGLE_QUESTIONS` (`monitor.py:34`). Two independent notions of bad: `criterion.is_bad_regime` = membership in a hardcoded set vs `process_state.is_bad` = `!= PRODUCTIVE`. They agree today only by coincidence of contents. Adding a regime and missing `criterion.py` makes it cost-free in J while the live controller still intervenes on it — the offline optimizer and the online controller would then optimize different objectives with no error anywhere.

Make `ProcessRegime` the single source: derive or delete `StruggleType`, define `BAD_REGIMES = frozenset(r.value for r in ProcessRegime if r is not ProcessRegime.PRODUCTIVE)`, have `is_bad_regime` delegate to `is_bad`, replace `TrueRegime` with `ProcessRegime`, and build the `dwell_thresholds` default via `dict.fromkeys(BAD_REGIMES, 0.0)`. Also delete `DifficultyLevel` (`agents/analytics/models.py:28`) in favour of `models/enums.Difficulty` — or, given that `models/enums.py` is dead, keep `DifficultyLevel` and delete the enums module. **Capability preserved:** the vocabulary and the J definition are unchanged; only the number of places declaring them drops from five to one.

**Error contract at the MCP seam (PARTIAL).** `_tool_errors` (`mcp_sdk/server.py:27-45`) re-raises `MCPServerError` subclasses and maps everything else to `"Internal server error"`; `domain_tool` (`:231-241`) applies no decorator, so the 26 GNS3 domain tools raise raw `KeyError`/`AttributeError`/httpx errors; and two of them (`exec_vtysh`, `domain_tools.py:246,259`) instead return `{"success": False, …}` with HTTP 200 — three conventions in one server. The backend rebuilds everything as an opaque `MCPToolError(name, text)` (`backend/mcp_client/client.py:80`). **Correction:** `TargetSystemAPIError`'s default message is `"Target system API error: {status_code}"` (`errors.py:23`), so 404 and 500 differ in the *text* — they are unstructured, not indistinguishable. Apply `_tool_errors` inside `domain_tool`, serialize as `{code, status_code, message}` so `MCPToolError` can carry a status, and convert the `success: False` returns to the same path.

---

## Readability / self-documentation

Three renames/restructures worth doing, with before/after.

### R1. Four "analytics" packages → four distinct names

```
before                              after
backend/analytics/                  backend/telemetry/          # POST /analytics/events, browser ingest
backend/learning_analytics/         backend/learning_analytics/ # unchanged: the online control loop
backend/agents/analytics/           backend/agents/identifier/  # exports identify_regime already
backend/experiment/analysis.py      backend/evaluation/arm_analysis.py
```

A newcomer asked to "look at the analytics code" currently has a 1-in-4 chance of opening the right package. After: each name states what it is.

### R2. The intervention decision, in one function

```python
# before — spread across monitor.py:164/553/567/587, process_state.py:24,
#          agent.py:25, assignment.py:123, config_model.py, interface.py:56
if self._learning_analytics_config.mrt_enabled:
    await self._mrt_step(...)
    return                                  # <- silently skips the arm gate below
if self._control_arm == ControlArm.OPEN:
    await self._log_would_intervene(...)
    return
...
```

```python
# after — learning_analytics/control_law.py
decision = should_intervene(
    regime=regime, dwell=dwell, arm=self._control_arm,
    last_intervention_at=self._last_intervention_at, cfg=cfg, now=now,
)
match decision.action:
    case "intervene":  await self._dispatch_intervention(...)
    case "withhold":   await self._log_would_intervene(decision.reason, ...)
    case "log_only":   await self._log_decision_point(decision.reason, ...)
    case "skip":       pass
```

Every gate is visible in one function, `decision.reason` records provenance the log currently hardcodes, and the MRT bypass (bug #8) becomes structurally impossible.

### R3. `monitor.py`'s deferred imports

23 indented imports between lines 105 and 669 hide the module's real dependency set from its import block — grepping the header understates coupling by roughly 3×, which is also what lets circular-import pressure accumulate unnoticed. Hoist all but the genuinely circular ones and put a one-line comment on those. (Note: 7 of the 15 line numbers cited by the original survey — 240, 322, 419, 507, 606, 620, 660 — contain no import; re-enumerate before editing.)

Smaller, mechanical:

- `sessions/service.py` vs `sessions/services/` — two spellings for one concept (see S8). Rename the barrel to `sessions/api.py`, or populate the currently-empty `services/__init__.py` and delete the barrel. Grep for a caller currently returns half the answer.
- `gns3-service/src/models.py:56 SessionStatus` vs `src/db/models.py:14 SessionStatus` — two unrelated symbols, same name, same package. Rename the former (it is dead anyway; see the table).
- `labeled_real_n` on `admin/schemas.py:28` is filled by `len(metrics)` over `ExperimentMetrics` (`admin/router.py:204`) — the number of finished sessions, not labeled real scenarios, which are provably zero (`scripts/eval_identifier.py:94`). Rename to `finished_sessions_n`; the two meanings currently collide on the same dashboard as the defense report's `labeled-real-N: 0`.
- `simulation/orchestrator.py`'s `_CMD → _default_command_for → command_for → actor.execute(cmd=…)` trace ends at a parameter `GNS3Actor.execute` ignores. Delete the chain (see the dead-code table) so the trace terminates where the command actually comes from: `task.correct_cmd`/`task.wrong_cmd`.

---

## Sequencing

Four batches, each independently shippable.

### Batch 1 — safe deletions and one-line fixes (no behavior change beyond the stated bugs)

Ship this first; it shrinks everything downstream and unblocks nothing else.

1. Delete the dead-code table's entries: `models/enums.py`, `agents/tutor/tools.py` + `analytics/tools.py`, the three dead gns3 build scripts + their three orphaned `topology_builder` helpers, `gns3-service/src/routers/projects.py` + its admin methods + models, `reset-password`/`GET /sessions/{id}`, the three unused metrics + two ActivityKinds, `StateCache` dict shims, `ConnectionPool.start`, `simulation/env/actor.py` + the `command_for` chain, `harvest_open_arm_sessions`. **~1,100 LOC.**
2. Fix #1 (queue release in `_mark_ended_and_finalize`), #7 (`request.state.user` in `get_current_user`), #12 (`template_project_id_for`), #15 (WS `try/finally` + fan-out), #18 (`is_active` default), #21 (`default_model_id` precedence), #23 (`enabled` filter in `labs/router.py`).
3. Rewrite `gns3/Makefile` to `uv run --package …` and make `test` run both gns3 suites (S11).
4. Apply or delete the three dead LLM config knobs (S: `dead-config-knobs`) — applying `request_timeout` is the one that matters, since today no LLM call has a client-side timeout. **Caveat:** `autonomy_intervention_threshold` and `eval_onset_window_seconds` are asserted on by `tests/unit/config/test_cohort_config.py` and `test_eval_config.py`; deleting them breaks those two tests.

### Batch 2 — the research-integrity fixes (do before any number is quoted anywhere)

These are the reason the report exists. None of them removes capability.

5. **#3 — realized J.** Feed `total_J` the identifier's detections. Land this before #4, because #4 makes derived thresholds deployable and you do not want to deploy a threshold derived from an oracle.
6. **#4 — `_build_learning_analytics`** in `env_config_loader`, defaults preserved as fallback. Then replace `simulation/run.py:39-52`'s in-process mutation with a sim env file.
7. **#8 — hoist the arm gate above the MRT branch.** Must land in the same release as #4, since #4 is what makes `mrt_enabled=True` reachable.
8. **#2 — decide the A/B arm.** Wire it (~15 LOC) or retire it (~−370 LOC). Do not ship another export while `GET /experiment/analysis` reports `significant` on a non-existent treatment.
9. **#11 — time-driven analysis cycle** so IDLE is observable; filter the observer heartbeat out of `idle_periods`.
10. **#10 — route `_dispatch_intervention` through `ControlInterface.act`** (or delete the act half and stop claiming it). This is also what makes #8's fix load-bearing rather than advisory.
11. **#24 — exclude `sim-truth`** from `gold_label_count`/`inter_rater_kappa`/`_labels_by_window` *before* Batch 4 gives them endpoints.

### Batch 3 — security and operations

12. **#5 — attach `verify_internal_token`** to gns3-service's sessions/projects/history at include time; `compare_digest` in `exec.py:35`/`ws.py:35`.
13. **#6 — per-`(user_id, project_id)` LogBuffer.** Cross-tenant leak into the tutor context and the LA feature vector.
14. **#9 — `PATCH /sessions/{id}`**: delete it, or `Literal` status + idempotent finalize + unique index on `experiment_metrics.session_id`.
15. **#16, #22 — gns3-service WS liveness race and the orphaned proxy lock.**
16. **#13 — authenticate `exec_vtysh`** from gns3-mcp, or delete the tool and say the backend owns that path.
17. **#14 — one publisher for `history.event`**; **#17 — memoize `build_client`**; **#19 — batch the activity log**; **#20 — JWT in the pool key**.

### Batch 4 — consolidation and readability (mechanical, reviewable in isolation)

18. **S3 + S4** — move observability, config bootstrap and env_cipher into `mcp_sdk`; add `mcp_sdk` to gns3-service. **−330 LOC**, and gns3-service stops double-logging every request.
19. **S1 + S2** — one GNS3 action table; replace mcp-sdk protocol discovery with a table. **−330 LOC.** Carry the three caveats in S1 explicitly.
20. **S5 + S6** — cohort types become `BaseModel`; synthetic fixtures and cost/grid vocabulary get one home. **−250 LOC.** Note S6 changes the admin dashboard's numbers by design.
21. **R1 + R2 + R3** — the four renames, `control_law.py`, and hoisting `monitor.py`'s deferred imports.
22. Wire the six test-only research capabilities to admin endpoints and defense-export sections (~+60 LOC to make ~230 reachable).
23. **S10** — pick one session-state cache layer; **S8** — one `load_lab_spec`, and rename the `sessions/service.py` barrel.

### Leave alone

- The exception hierarchies. Three domains, three vocabularies, correct as is.
- `mcp_sdk.connection.ConnectionPool` internals and `mcp_sdk.testing`. Deep and used.
- The central `models/` package. It is the shape large FastAPI codebases converge on.
- `S7` (agent registry collapse / dropping pydantic-ai) until Batch 2 is finished — it touches the intervention path, which is exactly where the research fixes are landing.
- `S9` (template build via subprocess) — real problem, but needs an async rewrite of a 281-LOC sync module. Not worth interleaving with the above.

---

## Appendix: refuted claims

No claim was refuted outright in this round. The following *sub-claims* were corrected during verification and should not be re-investigated:

- `backend/sessions/services/__init__.py` does **not** re-export the session services — it is a 0-byte file. Any refactor that points callers at `sessions.services` instead of `sessions.service` will `ImportError`.
- `gns3_template_project_id_iosvl2` **is** settable — `AdminLabUpdate` (`backend/admin/schemas.py:108`) + `PATCH /admin/labs/{slug}` write it and `launch.py:85` reads it. It is not orphaned by the missing build script.
- `routers/templates.py`'s subprocess does **not** leave a zombie; asyncio reaps killed children.
- `TargetSystemAPIError` messages **do** differ between a GNS3 404 and a 500 (`mcp_sdk/errors.py:23`); they are unstructured, not identical.
- `monitor._maybe_grounding_ablation` does **not** duplicate `generate_grounding_pair` — it makes one extra orchestrator call, the helper makes two. Swapping them would double LLM cost per ablation.
- `reproducibility.py`'s inline gold count is **not** the same query as `gold_label_count` — it adds the sim-session firewall.
- `eval_identifier.py` **does** use the loaded config (`:100` passes `cfg.eval_t_k_grid` and `cfg`); only the `Costs` at `:88` are hardcoded.
- `GNS3Actor.execute`'s signature **already** matches the `Actor` Protocol; the Protocol is unused for other reasons.
- `mcp_sdk/__init__.py`'s barrel is **not** unreferenced — `README.md:278` documents it as the package's public API.
- gns3-mcp has **no** observability module, so logging/sentry duplication is 2×, not 3×.
- `OpenClawConfig` **is** built from the environment (`env_config_loader.py:170-175`) and `Makefile:75` has an `openclaw` target — neither is a production caller of the adapter, but neither is dead config either.
- `src/models.py:56 SessionStatus` in gns3-service is a different symbol from the heavily used `src/db/models.py:14` enum of the same name — deleting the former is safe, the latter is not.
- "Every rate limit is IP-keyed" is 6 of 7: `/auth/exchange` (`auth/router.py:96`) has its own working key function.
