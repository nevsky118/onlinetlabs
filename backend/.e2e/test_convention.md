# Конвенция backend unit-тестов (рефактор под TMS-мост)

Эталон: `backend/tests/unit/test_rate_limit.py`. Применять СТРОГО. Поведение тестов НЕ менять — те же проверки, только переформатировать под конвенцию. После рефактора тесты обязаны проходить.

## 1. Шапка модуля

```python
import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none
# импортировать ТОЛЬКО используемые ассерты

pytestmark = [pytest.mark.unit]
```

Доступные ассерты (`mcp_sdk.testing.custom_assertions`): `assert_equal`, `assert_not_equal`, `assert_true`, `assert_false`, `assert_is_none`, `assert_is_not_none`, `assert_is_instance`, `assert_greater`, `assert_greater_equal`, `assert_less`, `assert_less_equal`, `assert_in`. Сигнатура: `assert_equal(actual, expected, message=None)` и т.п.

## 2. Класс-обёртка

Все тест-функции файла оборачиваются в ОДИН класс `class TestXxx:` (PascalCase, описывает юнит под тестом). Имя по сути файла, напр. `test_km.py` → `class TestKaplanMeier:`, `test_control_arm.py` → `class TestControlArm:`.

Модульные хелперы (`_rec`, `_lab`, `_request`, фикстуры `@pytest.fixture`) ОСТАЮТСЯ на уровне модуля (как `_request` в эталоне). Методы класса берут фикстуры как параметры.

## 3. Каждый метод — декораторы (СТРОГИЙ порядок) + AAA

```python
    @autotest.num("792")
    @autotest.external_id("d4e5f607-0809-4a1b-8c23-567890abcdef")
    @autotest.name("ControlArm: значения плеч open/closed")
    def test_d4e5f607_arm_values(self):
        with autotest.step("Act: собрать значения enum"):
            values = {a.value for a in ControlArm}
        with autotest.step("Assert: ровно open и closed"):
            assert_equal(values, {"open", "closed"}, "два плеча")
```

Правила:
- Порядок декораторов строго: `@autotest.num` → `@autotest.external_id` → `@autotest.name`.
- `num` — строка числа, УНИКАЛЬНА. Нумеровать тесты файла последовательно от выданного BASE (BASE, BASE+1, ...).
- `external_id` — свежий uuid4 на каждый тест (генерируй уникальные, формат `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`).
- `name` — человекочитаемое «Юнит: что проверяет» (рус.).
- Имя метода: `test_<uuid8>_<snake_описание>`, где `<uuid8>` = первые 8 hex external_id (до первого дефиса). Напр. external_id `d4e5f607-...` → `def test_d4e5f607_arm_values`.
- async-тесты: `async def test_<uuid8>_<snake>(self):` (asyncio_mode=auto, доп. маркеры НЕ нужны).
- Тело — блоки `with autotest.step("<Arrange|Act|Assert>: ..."):`. Минимум Act+Assert; Arrange если есть подготовка.
- Все `assert ...` заменить на кастом-ассерты. `assert a == b` → `assert_equal(a, b, "msg")`; `assert cond` → `assert_true(cond, "msg")`; `assert x is None` → `assert_is_none(x, "msg")`; `assert x is not None` → `assert_is_not_none`; `assert x in y` → `assert_in`; `assert a > b` → `assert_greater`; `assert a >= b` → `assert_greater_equal`; `assert a < b`/`<=` → `assert_less`/`assert_less_equal`; `assert a != b` → `assert_not_equal`; `assert not cond` → `assert_false`.
- `pytest.approx` можно оставлять внутри ассерта: `assert_equal(r, pytest.approx(0.5, abs=0.2), "msg")` (approx сравнивается через ==). Для диапазона можно `assert_true(0.3 < r < 0.7, "msg")`.
- `pytest.raises`, `monkeypatch`, `@pytest.mark.parametrize` — оставлять как есть; у параметризованного метода ОДИН num/external_id/name.
- `pytest.fixture`-фикстуры из файла — оставить на уровне модуля, методы принимают их параметром.

## 4. Что НЕ трогать
- Логику и значения проверок (те же ассерты по сути).
- Импорты тестируемого кода, фикстуры, хелперы.
- Имена тестовых данных.

## 5. После рефактора
Прогнать `cd backend && poetry run pytest <свои файлы> -v` (БЕЗ ENV_FILE) — все должны пройти. Если упал — это ошибка рефактора (импорт ассерта, опечатка), чинить.
