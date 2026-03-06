import pytest

from tests.report import autotests

pytestmark = [pytest.mark.smoke]


class TestImports:
    @autotests.num("310")
    @autotests.external_id("c2d3e4f5-a6b7-4c8d-9e0f-1a2b3c4d5e6f")
    @autotests.name("GNS3 MCP: config импортируем")
    def test_config_importable(self):
        with autotests.step("Импортируем config"):
            from src.config import GNS3MCPConfigModel  # noqa: F401
            from src.config.env_config_loader import EnvConfigLoader  # noqa: F401

    @autotests.num("311")
    @autotests.external_id("d3e4f5a6-b7c8-4d9e-0f1a-2b3c4d5e6f7a")
    @autotests.name("GNS3 MCP: SDK импортируем")
    def test_sdk_importable(self):
        with autotests.step("Импортируем SDK"):
            from onlinetlabs_mcp_sdk import (  # noqa: F401
                OnlinetlabsMCPServer,
                SessionContext,
                StateProvider,
            )
