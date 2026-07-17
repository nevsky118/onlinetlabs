# simulation/ — генеративная когорта сим-студентов

> **УДАЛЯЕМЫЙ модуль.** Снести: `rm -rf backend/simulation backend/tests/unit/simulation` +
> `DELETE FROM users WHERE is_simulated = true;` (CASCADE снесёт сессии/данные).

## Чем это НЕ является (критично)

Симуляция **НЕ** доказательство эффективности обучения или construct-validity детектора —
это требует **живых людей**. Выдать «протестировано на 50 симулированных студентах» за
результат = desk-reject и повтор ловушки засеянного A/B.

**Firewall:** каждый сим-юзер `User.is_simulated=True`; `evaluation/reproducibility.py`
и любые «реальные результаты» ИСКЛЮЧАЮТ такие данные (guard-тест
`tests/unit/evaluation/test_reproducibility_firewall.py`).

## Для чего это (законно)

De-risk ДО реального пилота: приборы (MRT-рандомизатор/decision-log/evidence/latency/IRR)
пишут корректно; анализ-код гоняется на реалистичных данных; метрики/логи/admin-дашборд
живьём; баги под конкурентностью; очередь/провижн.

## Как работает

- `profiles.py` — латентные черты (skill/persistence/strategy/pace/help_propensity), seeded.
- `policy.py` — **латентный mode правит действиями** (mode = причина, действия = следствие;
  порождён независимо от порогов детектора → честная observer-ROC).
- `env/gns3_actor.py` — действие → наблюдаемая GNS3 node-операция (toggle start/stop) / chat / idle.
  ask_help пишет вопрос студента + **ответ тьютора** (`tutor_reply`: YandexGPT → шаблон-фолбэк)
  → полный диалог в чат-логе (`/session/<id>/chat`).
- `help_text.py` — LLM (gated, бюджет ≤500₽ → шаблон-fallback) для текста просьб.
- `ground_truth.py` — истинный режим как `RegimeAnnotation(coder_id="sim-truth")`.
- `orchestrator.py` — пул из N + очередь, is_simulated+is_active-юзеры, per-student отлов сбоев.
- `run.py::_make_finalize` — **полный протокол**: L1 (ассист) → L2 (near-transfer, БЕЗ ассиста,
  L2-пара по `meta.skill`) + LabProgress + `end_session` → ExperimentMetrics/cohort (дашборд).
  Мульти-лаб: `_find_l2_pair` находит пару того же навыка (нет пары → только L1).

## Запуск (нужен живой стек)

```bash
make up-db                    # из корня: db + redis
cd gns3 && make up            # gns3-стек (~4vCPU/6GB)
cd backend
poetry run python -m simulation.run --n 50 --concurrency 3 --seed 0 --lab lan-static-ip
```

**E2E-провижн** (launch + монитор + actor из console host/port) собирается на живом стеке
(deps как в `deps.py`/lifespan). Юнит-ядро (profiles/policy/actor/help/ground-truth/orchestrator)
покрыто моками и тестами — реальный GNS3 не нужен для тестов.

## Живой E2E-прогон (2026-07-12): результаты

`_live_provision` подключён и прогнан на реальном GNS3-стеке. Контур замкнулся: все 5
приборов пишут вживую (312 behavioral_events, 171 ground-truth, 6 evidence, 10 latency,
1 MRT decision-log). Firewall проверен живьём — reproducibility-бандл исключает сим-данные.

### Наблюдаемый сигнал (важно)

Платформа наблюдает поведение через **GNS3 project-notifications** (node/link lifecycle +
серверные `log.*`), НЕ через консольный ввод. Поэтому actor маппит действие студента на
**node-операцию** (toggle start/stop → `node.updated`), а не telnet-консоль. Консольная
конфигурация детектору невидима — ограничение платформы, отражённое в дизайне actor'а.

### 3 бага, пойманных живым прогоном

1. Сим-юзеры без study-consent → шов режет observe (fix: `grant_consent` в `_live_provision`).
2. **prod**: `control_interface.observe` ронял `ctx` при вызове MCP → ошибка (fix: диспатч
   через типизированную обёртку, как `act()`; `control_interface/interface.py`).
3. **prod**: collector читал историю по backend session id, а gns3-service ключует её своим
   id → `list_user_actions` НИКОГДА не давал событий (fix: gns3-service id в `ctx.metadata`,
   `sessions/context.py` + `gns3-mcp/server.py::list_user_actions`).

### Тюнинг под сжатое время

Сим-сессия ~40с против минут у живого студента. `_build_deps` масштабирует детектор idle
(`idle_gap_seconds`, `idle_threshold`) и включает приборы (`mrt_enabled` и т.д.). Это
де-риск приборов, НЕ валидация детектора (требует живых людей).

## Осталось (follow-on)

- lab-config: реальные корректные/неверные консольные команды per-lab (по MDX + validation YAML).
- (опц.) реальный `llm_call` к YandexGPT для help-текста; валидация-на-submit.
- Baseline `dwell_thresholds` в конфиге = 0.0 для всех режимов — задать реальные T_k.
