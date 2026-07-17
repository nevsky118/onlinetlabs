"""Общие builders и фикстуры для unit-тестов gns3-service."""

import os

# Сидируем env до любого импорта src.config — settings ленивые, но как только
# роутерные тесты дотягиваются до settings.security.internal_api_token, грузится
# полная модель. Дефолты не должны конфликтовать с реальными .env переменными.
os.environ.setdefault("GNS3_URL", "http://gns3:3080")
os.environ.setdefault("GNS3_ADMIN_USER", "admin")
os.environ.setdefault("GNS3_ADMIN_PASSWORD", "admin")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-internal-token")

import pytest


def build_gns3_node(**overrides) -> dict:
    """Сборка JSON-структуры узла GNS3 API."""
    defaults = {
        "node_id": "node-1",
        "project_id": "project-1",
        "name": "R1",
        "node_type": "docker",
        "status": "started",
        "console": 5000,
        "console_type": "telnet",
        "console_host": "127.0.0.1",
        "compute_id": "local",
        "properties": {"container_id": "container-xyz"},
        "ports": [{"name": "eth0", "port_number": 0, "adapter_number": 0}],
    }
    return defaults | overrides


def build_gns3_link(**overrides) -> dict:
    """Сборка JSON-структуры связки GNS3 API."""
    defaults = {
        "link_id": "link-1",
        "project_id": "project-1",
        "nodes": [
            {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
            {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
        ],
        "link_type": "ethernet",
        "capturing": False,
        "filters": {},
    }
    return defaults | overrides


def build_gns3_project(**overrides) -> dict:
    """Сборка JSON-структуры проекта GNS3 API."""
    defaults = {
        "project_id": "project-1",
        "name": "test-project",
        "status": "opened",
        "path": "/tmp/projects/project-1",
        "auto_close": False,
        "auto_open": False,
        "auto_start": False,
    }
    return defaults | overrides


def build_gns3_user(**overrides) -> dict:
    """Сборка JSON-структуры пользователя GNS3 API."""
    defaults = {
        "user_id": "user-1",
        "username": "student-1",
        "email": "student-1@example.com",
        "full_name": "Student One",
        "is_active": True,
        "is_superadmin": False,
    }
    return defaults | overrides


@pytest.fixture
def gns3_node():
    return build_gns3_node


@pytest.fixture
def gns3_link():
    return build_gns3_link


@pytest.fixture
def gns3_project():
    return build_gns3_project


@pytest.fixture
def gns3_user():
    return build_gns3_user
