# simulation/, a generative cohort of sim students

> **DISPOSABLE module.** To tear it down: `rm -rf backend/simulation backend/tests/unit/simulation` +
> `DELETE FROM users WHERE is_simulated = true;` (CASCADE takes the sessions/data with it).

## What this is NOT (critical)

The simulation is **NOT** proof of learning effectiveness or of the detector's construct validity,
that requires **live humans**. Passing off "tested on 50 simulated students" as a
result = desk-reject and a repeat of the seeded A/B trap.

**Firewall:** every sim user carries `User.is_simulated=True`; `evaluation/reproducibility.py`
and anything claiming "real results" EXCLUDE such data (guard test
`tests/unit/evaluation/test_reproducibility_firewall.py`).

## What it is for (legitimately)

De-risking BEFORE the real pilot: the instruments (MRT randomizer/decision-log/evidence/latency/IRR)
write correctly; the analysis code runs over realistic data; metrics/logs/admin dashboard
live; bugs under concurrency; queue/provisioning.

## How it works

- `profiles.py`, latent traits (skill/persistence/strategy/pace/help_propensity), seeded.
- `policy.py`, **the latent mode drives the actions** (mode = cause, actions = effect;
  generated independently of the detector thresholds → an honest observer ROC).
- `env/gns3_actor.py`, action → an observable GNS3 node operation (toggle start/stop) / chat / idle.
  ask_help writes the student's question + **the tutor's reply** (`tutor_reply`: YandexGPT → template fallback)
  → the full dialogue in the chat log (`/session/<id>/chat`).
- `help_text.py`, an LLM (gated, budget ≤500₽ → template fallback) for the text of the requests.
- `ground_truth.py`, the true regime as `RegimeAnnotation(coder_id="sim-truth")`.
- `orchestrator.py`, a pool of N + a queue, is_simulated+is_active users, per-student failure trapping.
- `run.py::_make_finalize`, the **full protocol**: L1 (assisted) → L2 (near-transfer, WITHOUT assistance,
  the L2 pair taken from `meta.skill`) + LabProgress + `end_session` → ExperimentMetrics/cohort (dashboard).
  Multi-lab: `_find_l2_pair` finds a pair for the same skill (no pair → L1 only).

## Running (a live stack is required)

```bash
make up-db                    # from the root: db + redis
cd gns3 && make up            # gns3 stack (~4vCPU/6GB)
cd backend
poetry run python -m simulation.run --n 50 --concurrency 3 --seed 0 --lab lan-static-ip
```

**E2E provisioning** (launch + monitor + actor from the console host/port) is assembled on a live stack
(deps as in `deps.py`/lifespan). The unit core (profiles/policy/actor/help/ground-truth/orchestrator)
is covered by mocks and tests, so a real GNS3 is not needed for the tests.

## Live E2E run (2026-07-12): results

`_live_provision` is wired in and has been run against a real GNS3 stack. The loop closed, all 5
instruments write live (312 behavioral_events, 171 ground-truth, 6 evidence, 10 latency,
1 MRT decision-log). The firewall was checked live, the reproducibility bundle excludes sim data.

### The observable signal (important)

The platform observes behavior through **GNS3 project notifications** (node/link lifecycle +
server-side `log.*`), NOT through console input. That is why the actor maps a student action onto a
**node operation** (toggle start/stop → `node.updated`) rather than onto the telnet console. Console
configuration is invisible to the detector, a platform limitation reflected in the actor's design.

### 3 bugs caught by the live run

1. Sim users without study consent → the seam cuts off observe (fix: `grant_consent` in `_live_provision`).
2. **prod**: `control_interface.observe` dropped `ctx` when calling MCP → error (fix: dispatch
   through a typed wrapper, the way `act()` does it; `control_interface/interface.py`).
3. **prod**: the collector read history by the backend session id while gns3-service keys it by its own
   id → `list_user_actions` NEVER produced events (fix: the gns3-service id in `ctx.metadata`,
   `sessions/context.py` + `gns3-mcp/server.py::list_user_actions`).

### Tuning for compressed time

A sim session lasts ~40s against minutes for a live student. `_build_deps` scales the idle detector
(`idle_gap_seconds`, `idle_threshold`) and turns the instruments on (`mrt_enabled` and so on). This
de-risks the instruments, it is NOT detector validation (that requires live humans).

## What is left (follow-on)

- lab-config: real correct/incorrect console commands per lab (from MDX + validation YAML).
- (optional) a real `llm_call` to YandexGPT for the help text; validation on submit.
- Baseline `dwell_thresholds` in the config = 0.0 for every regime, the real T_k values still need setting.
