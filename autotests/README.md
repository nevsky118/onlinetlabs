# Autotests

API-автотесты. Все запросы идут на `config.base_url` / `config.gns3_base_url`.

## Структура

```
autotests/
├── conftest.py                          # Фикстуры: users, tokens, lab, GNS3 project, очистка
├── pytest.ini                           # Маркеры, логи
├── Makefile                             # Команды запуска
│
├── settings/                            # Инфраструктура
│   ├── api_client/
│   │   └── api_client.py               # ApiClient — async REST клиент с JWT
│   ├── configuration/
│   │   ├── config_model.py             # ConfigModel, Account (Pydantic)
│   │   ├── env_config_loader.py        # Загрузка из .env / os.environ
│   │   ├── local.env.aes              # Локальный конфиг (зашифрованный)
│   │   └── ci.env.aes                 # CI конфиг (Docker-сети, зашифрованный)
│   ├── constants/
│   │   └── constants_settings.py       # Константы фреймворка (аккаунты и др.)
│   ├── reports/
│   │   └── autotest.py                 # step(), num(), name(), external_id()
│   ├── utils/
│   │   ├── data_generator_abstraction.py  # Базовый класс генераторов тестовых данных
│   │   ├── custom_assertions.py        # Кастомные ассерты (equal, true, in, greater, ...)
│   │   └── utils.py                    # Глобальные вспомогательные методы (рандомизация, проверки, пути)
│   └── delete_entities/
│       ├── entity_types.py             # Перечисление типов сущностей для автоочистки
│       ├── entities_registry.py        # Реестр созданных сущностей
│       └── entities_cleanup.py         # Автоудаление после теста
│
├── api/                                 # Переиспользуемые компоненты (НЕ тесты)
│   ├── api_methods/                     # Слой 1: HTTP-обёртки
│   │   ├── onlinetlabs_service/        # auth, courses, labs, progress, sessions
│   │   └── gns3_service/               # gns3_sessions, gns3_projects
│   ├── data/                            # Слой 2: Генераторы данных
│   │   └── <controller>_data_api.py
│   └── api_helpers/                     # Слой 3: Вспомогательные методы
│       └── <controller>_helper_api.py
│
└── api_tests/                           # Тесты
    ├── onlinetlabs_service/             # auth, courses, labs, progress, sessions
    └── gns3_service/                    # sessions
```

## Запуск

```bash
make test              # все тесты (ENV=local по умолчанию)
make test ENV=ci       # CI-окружение (Docker-сети)
```

### Кастомный запуск через pytest

```bash
cd autotests
PYTHONPATH=.. poetry run pytest --rootdir=. --envFile settings/configuration/local.env [опции] .
```

| Опция | Описание |
|-|-|
| `-m smoke` | Только smoke-тесты |
| `-m crud` | Только crud-тесты |
| `-k auth` | Тесты, содержащие "auth" в имени |
| `-k "gns3 and not history"` | Комбинация фильтров |
| `--lf` | Перезапуск только упавших |
| `-x` | Остановка на первом фейле |
| `-v` | Подробный вывод |

## Conftest — автоматическая настройка

Conftest автоматически при старте сессии:

1. **`_ensure_test_users`** — регистрирует `ANON_ACCOUNT` и `REGISTERED_ACCOUNT` через `POST /auth/register`, получает реальные UUID
2. **`_generate_tokens`** — обменивает `user_id + email` на JWT через `POST /auth/exchange`
3. **`_ensure_gns3_template_project`** — создаёт шаблонный проект в GNS3 через `POST /projects` (gns3-service)
4. **`_ensure_test_lab`** — создаёт тестовую лабораторную `autotest-lab` через `POST /labs`

После всех тестов — удаляет всё в обратном порядке (lab → GNS3 project → users).

Каждый тест также чистит за собой через `EntitiesRegistry` (сессии, пользователи, GNS3-сессии).

## Слои архитектуры

```
Test → Helper → API Method
            └→ Data
```

Каждый слой имеет одну ответственность. Зависимости — только вниз.

---

## Гайд: как писать тесты

### 1. Data — генератор данных

Файл: `api/data/<controller>_data_api.py`

Класс наследует `DataAbstractionGenerator`. Генерирует случайные данные в `__init__`, хранит payload в `self.data`, отдельные поля — как атрибуты.

```python
from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class SessionCreateData(DataAbstractionGenerator):
    def __init__(self, lab_slug: str = None):
        uid = Randomizer.uuid()
        self.lab_slug = lab_slug or f"lab-{Randomizer.random_string(8).lower()}"
        self.data = {"lab_slug": self.lab_slug}
```

### 2. API Method — HTTP-обёртка

Файл: `api/api_methods/<controller>_api.py`

Тонкая обёртка: один метод = один HTTP-запрос. Возвращает `httpx.Response`.

```python
class SessionsApi:
    def __init__(self, client, config, account_name=ConstantsSettings.REGISTERED_ACCOUNT):
        self.api_client = ApiClient(client=client, config=config, account_name=account_name,
                                    controller_path="/users/me/sessions")

    async def post_session(self, data: dict) -> Response:
        with autotest.step("POST /users/me/sessions"):
            return await self.api_client.post("", json_data=data)
```

### 3. Helper — вспомогательные методы

Файл: `api/api_helpers/<controller>_helper_api.py`

Композиция: создать данные → вызвать API → проверить статус → зарегистрировать сущность → вернуть результат.

### 4. Test — тестовый файл

Файл: `api_tests/<controller>/<marker>/test_<action>_<marker>_api.py`

Паттерн **AAA** (Arrange / Act / Assert). Каждый блок — `autotest.step()`.

### Именование тестов

**Формат метода:** `test_<uuid8>_<snake_case_описание>`

### Декораторы — строгий порядок

```python
@autotest.num("37")
@autotest.external_id("f0caad1d-6bc0-4a48-beac-362c7eb2e3bc")
@autotest.name("Auth Register: success (201)")
async def test_f0caad1d_register_success(self):
```

### Маркеры класса — строгий порядок

```python
@pytest.mark.api
@pytest.mark.smoke     # smoke | crud
@pytest.mark.asyncio
class TestAuthRegisterSmokeApi:
```

---

## Управление окружением

В git хранятся только `.aes` файлы. Расшифрованные — gitignored.

```bash
# Расшифровать
CONFIG_PASSWORD=... make decrypt file=settings/configuration/local.env.aes

# Зашифровать после изменений
CONFIG_PASSWORD=... make encrypt file=settings/configuration/local.env
```

| Файл | URLs | Назначение |
|-|-|-|
| `local.env.aes` | `localhost:8000`, `localhost:8101` | Локальная разработка + Docker (exposed ports) |
| `ci.env.aes` | `backend:8000`, `gns3-service:8101` | CI внутри Docker-сети |

`GNS3_LAB_TEMPLATE_PROJECT_ID` заполняется автоматически conftest-фикстурой.

## Чеклист: новый сервис

1. `api/data/<controller>_data_api.py` — Data-классы (наследуют `DataAbstractionGenerator`)
2. `api/api_methods/<controller>_api.py` — API-класс (конструктор с `controller_path`)
3. `api/api_helpers/<controller>_helper_api.py` — Helper-класс (композиция API + Data + очистка)
4. `settings/delete_entities/entity_types.py` — добавить тип в `EntitiesTypes`
5. `settings/delete_entities/entities_cleanup.py` — реализовать удаление
6. `api_tests/<controller>/<marker>/` — тестовый класс
7. Маркеры: `@pytest.mark.api` + `@pytest.mark.<marker>` + `@pytest.mark.asyncio`
8. Декораторы: `@autotest.num()` → `@autotest.external_id()` → `@autotest.name()`
