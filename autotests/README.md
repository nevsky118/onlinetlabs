# Autotests

API autotests. All requests go to `config.base_url` / `config.gns3_base_url`.

## Structure

```
autotests/
├── conftest.py                          # Fixtures: users, tokens, lab, GNS3 project, cleanup
├── pytest.ini                           # Markers, logs
├── Makefile                             # Run commands
│
├── settings/                            # Infrastructure
│   ├── api_client/
│   │   └── api_client.py               # ApiClient, an async REST client with JWT
│   ├── configuration/
│   │   ├── config_model.py             # ConfigModel, Account (Pydantic)
│   │   ├── env_config_loader.py        # Loading from .env / os.environ
│   │   ├── .env.aes              # Local config (encrypted)
│   │   └── .env.ci.aes                 # CI config (Docker networks, encrypted)
│   ├── constants/
│   │   └── constants_settings.py       # Framework constants (accounts and others)
│   ├── reports/
│   │   └── autotest.py                 # step(), num(), name(), external_id()
│   ├── utils/
│   │   ├── data_generator_abstraction.py  # Base class for test data generators
│   │   ├── custom_assertions.py        # Custom assertions (equal, true, in, greater, ...)
│   │   └── utils.py                    # Global helper methods (randomization, checks, paths)
│   └── delete_entities/
│       ├── entity_types.py             # Enumeration of entity types for auto-cleanup
│       ├── entities_registry.py        # Registry of created entities
│       └── entities_cleanup.py         # Auto-deletion after a test
│
├── api/                                 # Reusable components (NOT tests)
│   ├── api_methods/                     # Layer 1: HTTP wrappers
│   │   ├── onlinetlabs_service/        # auth, courses, labs, progress, sessions
│   │   └── gns3_service/               # gns3_sessions, gns3_projects
│   ├── data/                            # Layer 2: Data generators
│   │   └── <controller>_data_api.py
│   └── api_helpers/                     # Layer 3: Helper methods
│       └── <controller>_helper_api.py
│
└── api_tests/                           # Tests
    ├── onlinetlabs_service/             # auth, courses, labs, progress, sessions
    ├── gns3_service/                    # sessions
    └── e2e/                             # end-to-end tests (backend → gns3-service → MCP → LLM)
```

### E2E tests

`api_tests/e2e/` holds end-to-end tests that run through several services
(backend → gns3-service → MCP → LLM). The class marker is `@pytest.mark.e2e`
(one marker, without `api`/`smoke`/`crud`). All other rules of this README
(the `@autotest.num/external_id/name` decorators, the `test_<uuid8>_<snake>` naming,
AAA with `autotest.step()`, cleanup through `EntitiesRegistry`) still apply.

## Running

```bash
make test              # all tests (ENV=local by default)
make test ENV=ci       # CI environment (Docker networks)
```

### Custom run through pytest

```bash
cd autotests
PYTHONPATH=.. poetry run pytest --rootdir=. --envFile settings/configuration/.env [options] .
```

| Option | Description |
|-|-|
| `-m smoke` | Smoke tests only |
| `-m crud` | Crud tests only |
| `-k auth` | Tests whose name contains "auth" |
| `-k "gns3 and not history"` | A combination of filters |
| `--lf` | Rerun only the failed ones |
| `-x` | Stop at the first failure |
| `-v` | Verbose output |

## Conftest, automatic setup

At session start conftest automatically:

1. **`_ensure_test_users`** registers `ANON_ACCOUNT` and `REGISTERED_ACCOUNT` through `POST /auth/register` and receives real UUIDs
2. **`_generate_tokens`** exchanges `user_id + email` for a JWT through `POST /auth/exchange`
3. **`_ensure_gns3_template_project`** creates a template project in GNS3 through `POST /projects` (gns3-service)
4. **`_ensure_test_lab`** creates the `autotest-lab` test lab through `POST /labs`

After all the tests it deletes everything in reverse order (lab → GNS3 project → users).

Every test also cleans up after itself through `EntitiesRegistry` (sessions, users, GNS3 sessions).

## Architecture layers

```
Test → Helper → API Method
            └→ Data
```

Every layer has a single responsibility. Dependencies point downwards only.

---

## Guide: how to write tests

### 1. Data, the data generator

File: `api/data/<controller>_data_api.py`

The class inherits `DataAbstractionGenerator`. It generates random data in `__init__`, keeps the payload in `self.data`, and exposes individual fields as attributes.

```python
from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class SessionCreateData(DataAbstractionGenerator):
    def __init__(self, lab_slug: str = None):
        uid = Randomizer.uuid()
        self.lab_slug = lab_slug or f"lab-{Randomizer.random_string(8).lower()}"
        self.data = {"lab_slug": self.lab_slug}
```

### 2. API Method, the HTTP wrapper

File: `api/api_methods/<controller>_api.py`

A thin wrapper, one method = one HTTP request. Returns `httpx.Response`.

```python
class SessionsApi:
    def __init__(self, client, config, account_name=ConstantsSettings.REGISTERED_ACCOUNT):
        self.api_client = ApiClient(client=client, config=config, account_name=account_name,
                                    controller_path="/users/me/sessions")

    async def post_session(self, data: dict) -> Response:
        with autotest.step("POST /users/me/sessions"):
            return await self.api_client.post("", json_data=data)
```

### 3. Helper, the helper methods

File: `api/api_helpers/<controller>_helper_api.py`

Composition: build the data → call the API → check the status → register the entity → return the result.

### 4. Test, the test file

File: `api_tests/<controller>/<marker>/test_<action>_<marker>_api.py`

The **AAA** pattern (Arrange / Act / Assert). Every block is an `autotest.step()`.

### Test naming

**Method format:** `test_<uuid8>_<snake_case_description>`

### Decorators, strict order

```python
@autotest.num("37")
@autotest.external_id("f0caad1d-6bc0-4a48-beac-362c7eb2e3bc")
@autotest.name("Auth Register: success (201)")
async def test_f0caad1d_register_success(self):
```

### Class markers, strict order

```python
@pytest.mark.api
@pytest.mark.smoke     # smoke | crud
@pytest.mark.asyncio
class TestAuthRegisterSmokeApi:
```

---

## Environment management

Only `.aes` files are stored in git. Decrypted ones are gitignored.

```bash
# Decrypt
CONFIG_PASSWORD=... make decrypt file=settings/configuration/.env.aes

# Encrypt after making changes
CONFIG_PASSWORD=... make encrypt file=settings/configuration/.env
```

| File | URLs | Purpose |
|-|-|-|
| `.env.aes` | `localhost:8000`, `localhost:8101` | Local development + Docker (exposed ports) |
| `.env.ci.aes` | `backend:8000`, `gns3-service:8101` | CI inside the Docker network |

`GNS3_LAB_TEMPLATE_PROJECT_ID` is filled in automatically by a conftest fixture.

## Checklist: a new service

1. `api/data/<controller>_data_api.py`, Data classes (inherit `DataAbstractionGenerator`)
2. `api/api_methods/<controller>_api.py`, API class (constructor with `controller_path`)
3. `api/api_helpers/<controller>_helper_api.py`, Helper class (composition of API + Data + cleanup)
4. `settings/delete_entities/entity_types.py`, add the type to `EntitiesTypes`
5. `settings/delete_entities/entities_cleanup.py`, implement deletion
6. `api_tests/<controller>/<marker>/`, test class
7. Markers: `@pytest.mark.api` + `@pytest.mark.<marker>` + `@pytest.mark.asyncio`
8. Decorators: `@autotest.num()` → `@autotest.external_id()` → `@autotest.name()`
