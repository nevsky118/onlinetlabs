# Data builders для GNS3 MCP Server тестов.

from typing import Any

from onlinetlabs_mcp_sdk.context import SessionContext


def build_session_context(**overrides: Any) -> SessionContext:
    defaults = {
        "user_id": "test-student",
        "session_id": "test-session",
        "environment_url": "http://localhost:3080",
        "project_id": "test-project-id",
        "metadata": {"gns3_jwt": "test-jwt-token"},
    }
    defaults.update(overrides)
    return SessionContext(**defaults)


def build_gns3_node(**overrides: Any) -> dict:
    """Сырой GNS3 JSON для ноды."""
    defaults = {
        "node_id": "node-1",
        "name": "PC1",
        "node_type": "vpcs",
        "status": "started",
        "console": 5000,
        "console_type": "telnet",
        "console_host": "0.0.0.0",
        "ports": [{"name": "Ethernet0", "port_number": 0, "adapter_number": 0}],
        "compute_id": "local",
        "node_directory": "/tmp/gns3/PC1",
    }
    defaults.update(overrides)
    return defaults


def build_gns3_link(**overrides: Any) -> dict:
    """Сырой GNS3 JSON для линка."""
    defaults = {
        "link_id": "link-1",
        "link_type": "ethernet",
        "capturing": False,
        "capture_file_path": None,
        "filters": {},
        "nodes": [
            {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
            {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
        ],
    }
    defaults.update(overrides)
    return defaults


def build_gns3_project(**overrides: Any) -> dict:
    """Сырой GNS3 JSON для проекта."""
    defaults = {
        "project_id": "test-project-id",
        "name": "Test Lab",
        "status": "opened",
    }
    defaults.update(overrides)
    return defaults


def build_gns3_version(**overrides: Any) -> dict:
    defaults = {"version": "3.0.0", "local": True}
    defaults.update(overrides)
    return defaults
