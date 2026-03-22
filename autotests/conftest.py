# Единый conftest для всех автотестов.
# Реальные HTTP-запросы на бэкенд, генерация токенов через API.

import logging
import os
from datetime import datetime

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient

logger = logging.getLogger(__name__)

from autotests.settings.configuration.config_model import ConfigModel
from autotests.settings.configuration.env_config_loader import EnvConfigLoader
from autotests.settings.delete_entities.entities_cleanup import delete_test_entities
from autotests.settings.delete_entities.entities_helper_api import EntitiesHelperApi
from autotests.settings.utils.utils import get_current_test_name


# Хуки Pytest


def pytest_addoption(parser):
    """
    Добавляет пользовательские опции командной строки для pytest.

    :param parser: Объект парсера опций Pytest.
    """
    parser.addoption(
        "--envFile",
        action="store",
        help="Путь к .env-файлу для генерации конфигурации окружения.",
    )
    parser.addoption(
        "--htmlReport",
        action="store_true",
        default=False,
        help="Сгенерировать HTML-отчёт pytest в директорию logs/reports/report_<...>.html",
    )


def pytest_configure(config):
    """
    Хук инициализации Pytest — настраивает pytest-html при --htmlReport.

    :param config: Объект конфигурации Pytest.
    """
    if config.getoption("--htmlReport"):
        os.makedirs("logs/reports", exist_ok=True)
        mark_expr = config.option.markexpr or "all"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"report_{mark_expr}_{timestamp}.html"
        config.option.htmlpath = os.path.join("logs", "reports", filename)


# Конфигурация


@pytest.fixture(scope="session")
def config(pytestconfig) -> ConfigModel:
    """
    Сессионная фикстура, загружающая конфигурацию из .env-файла.

    :param pytestconfig: Объект конфигурации Pytest.
    :return: Объект ConfigModel с параметрами окружения.
    """
    env_path = pytestconfig.getoption("envFile")

    if env_path is None:
        return EnvConfigLoader().load_from_environ()

    # Приводим к абсолютному пути относительно корня проекта
    if not os.path.isabs(env_path):
        project_root = os.path.abspath(os.path.dirname(__file__))
        env_path = os.path.join(project_root, env_path)

    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env file not found: {env_path}")

    return EnvConfigLoader().load(env_path=env_path)


# Генерация токенов через реальный API


_TEST_PASSWORD = "test_password_12345"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _ensure_test_users(config):
    """
    Регистрирует тестовых пользователей, обновляет account.sub реальным UUID.
    После всех тестов — удаляет созданных пользователей.
    """
    from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi

    created_user_ids: list[str] = []

    async with AsyncClient(base_url=config.base_url) as client:
        auth_api = AuthApi(client=client, config=config)
        for name, account in config.accounts.items():
            if not account.email:
                continue
            response = await auth_api.post_register({
                "email": account.email,
                "password": _TEST_PASSWORD,
                "name": name,
            })
            if response.status_code == 201:
                user_id = response.json()["id"]
                account.sub = user_id
                created_user_ids.append(user_id)
                logger.info(f"Registered {name}: id={user_id}")
            elif response.status_code == 409:
                login_response = await auth_api.post_login({
                    "email": account.email,
                    "password": _TEST_PASSWORD,
                })
                if login_response.status_code == 200:
                    account.sub = login_response.json()["id"]
                    created_user_ids.append(account.sub)
                    logger.info(f"User {name} exists, id={account.sub}")
                else:
                    logger.warning(f"Cannot login {name}: {login_response.text}")
            else:
                logger.warning(f"Cannot register {name}: {response.text}")

    yield

    async with AsyncClient(base_url=config.base_url) as client:
        auth_api = AuthApi(client=client, config=config)
        for user_id in created_user_ids:
            response = await auth_api.delete_user(user_id)
            if response.status_code in (200, 204):
                logger.info(f"Deleted user {user_id}")
            else:
                logger.warning(f"Cannot delete user {user_id}: {response.text}")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _ensure_gns3_template_project(config):
    """
    Создаёт шаблонный проект в GNS3 через gns3-service API.
    После тестов — удаляет.
    """
    from autotests.api.api_methods.gns3_service.gns3_projects_api import Gns3ProjectsApi

    project_id = None

    async with AsyncClient(base_url=config.gns3_base_url) as client:
        projects_api = Gns3ProjectsApi(client=client, config=config, base_url=config.gns3_base_url)
        try:
            response = await projects_api.post_project({"name": "autotest-template"})
            if response.status_code == 201:
                project_id = response.json()["project_id"]
                config.gns3_lab_template_project_id = project_id
                logger.info(f"Created GNS3 template project: {project_id}")
            else:
                logger.warning(f"Cannot create GNS3 project: {response.text}")
        except Exception as exc:
            logger.warning(f"GNS3 service unavailable: {exc}")

    yield

    if project_id:
        async with AsyncClient(base_url=config.gns3_base_url) as client:
            projects_api = Gns3ProjectsApi(client=client, config=config, base_url=config.gns3_base_url)
            response = await projects_api.delete_project(project_id)
            if response.status_code in (200, 204):
                logger.info(f"Deleted GNS3 template project: {project_id}")
            else:
                logger.warning(f"Cannot delete GNS3 project: {response.text}")


_TEST_LAB_SLUG = "autotest-lab"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _ensure_test_lab(config):
    """
    Создаёт тестовую лабораторную через API бэкенда.
    После тестов — удаляет.
    """
    from autotests.api.api_methods.onlinetlabs_service.labs_api import LabsApi

    created = False

    async with AsyncClient(base_url=config.base_url) as client:
        labs_api = LabsApi(client=client, config=config)
        response = await labs_api.post_lab({
            "slug": _TEST_LAB_SLUG,
            "title": "Autotest Lab",
            "difficulty": "beginner",
            "environment_type": "none",
        })
        if response.status_code == 201:
            created = True
            logger.info(f"Created test lab: {_TEST_LAB_SLUG}")
        elif response.status_code == 409:
            created = True
            logger.info(f"Test lab already exists: {_TEST_LAB_SLUG}")
        else:
            logger.warning(f"Cannot create test lab: {response.text}")

    yield

    if created:
        async with AsyncClient(base_url=config.base_url) as client:
            labs_api = LabsApi(client=client, config=config)
            response = await labs_api.delete_lab(_TEST_LAB_SLUG)
            if response.status_code in (200, 204):
                logger.info(f"Deleted test lab: {_TEST_LAB_SLUG}")
            else:
                logger.warning(f"Cannot delete test lab: {response.text}")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _generate_tokens(config, _ensure_test_users):
    """
    Получает JWT-токены для всех аккаунтов через POST /auth/exchange.
    """
    from autotests.api.api_methods.onlinetlabs_service.auth_api import AuthApi

    async with AsyncClient(base_url=config.base_url) as client:
        auth_api = AuthApi(client=client, config=config)
        for name, account in config.accounts.items():
            if account.sub and account.token is None:
                response = await auth_api.post_exchange({
                    "user_id": account.sub,
                    "email": account.email,
                })
                if response.status_code == 200:
                    account.token = response.json()["access_token"]
                else:
                    logger.warning(
                        f"Не удалось получить токен для {name}: "
                        f"status={response.status_code} body={response.text}"
                    )


# HTTP-клиенты


@pytest_asyncio.fixture()
async def anon_client(config, _generate_tokens, _ensure_gns3_template_project, _ensure_test_lab):
    """
    AsyncClient для запросов от анонимного пользователя.

    :param config: Объект ConfigModel.
    :param _generate_tokens: Фикстура генерации токенов.
    :return: httpx.AsyncClient с base_url из конфига.
    """
    transport = httpx.AsyncHTTPTransport(retries=3)
    async with AsyncClient(base_url=config.base_url, timeout=60, transport=transport) as client:
        yield client


# Очистка сущностей


@pytest_asyncio.fixture(autouse=True)
async def clean_entities_after_test():
    """
    Автоматическая очистка созданных сущностей после выполнения каждого теста.

    Проверяет, были ли созданы сущности в текущем тесте, и если да — удаляет их.
    """
    yield

    current_test_name = get_current_test_name()

    if not delete_test_entities.entities_registry.has_test(current_test_name):
        return

    delete_test_entities.entities_helper_api = EntitiesHelperApi(
        config=delete_test_entities.entities_registry.get_config()
    )

    await delete_test_entities.delete_test_entities_by_id(test_name=current_test_name)
    await delete_test_entities.delete_test_entities_by_name(test_name=current_test_name)
    delete_test_entities.entities_registry.unregister_test(test_name=current_test_name)
