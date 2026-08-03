import pytest
from mcp_sdk.testing import autotest
from pydantic import ValidationError

from src.config.config_model import GNS3MCPConfigModel, MCPConfig
from src.config.env_config_loader import EnvConfigLoader

pytestmark = [pytest.mark.unit, pytest.mark.config]


class TestConfigModel:
    @autotest.num("320")
    @autotest.external_id("gns3-config-defaults")
    @autotest.name("GNS3MCPConfigModel: default values")
    def test_gns3conf_defaults(self):
        with autotest.step("Create the default config"):
            cfg = GNS3MCPConfigModel()

        with autotest.step("Assert the defaults"):
            assert cfg.mcp.server_name == "gns3"
            assert cfg.mcp.transport == "streamable-http"
            assert cfg.mcp.host == "127.0.0.1"
            assert cfg.mcp.port == 8100
            assert cfg.pool.max_size == 200
            assert cfg.pool.idle_ttl == 600.0
            assert cfg.pool.health_check_interval == 60.0
            assert cfg.pool.min_evict_idle == 30.0
            assert cfg.log_buffer.max_entries == 500
            assert cfg.log_buffer.inactivity_timeout == 300.0
            assert cfg.gns3_service_url == "http://localhost:8101"

    @autotest.num("321")
    @autotest.external_id("gns3-config-invalid-transport")
    @autotest.name("MCPConfig: invalid transport")
    def test_gns3conf_invalid_transport(self):
        with autotest.step("Create a config with an invalid transport"):
            with pytest.raises(ValidationError):
                MCPConfig(transport="grpc")


class TestEnvConfigLoader:
    @autotest.num("322")
    @autotest.external_id("gns3-config-loader-defaults")
    @autotest.name("EnvConfigLoader: empty dict → default values")
    def test_gns3conf_build_defaults(self):
        with autotest.step("Build from an empty dict"):
            cfg = EnvConfigLoader._build({})

        with autotest.step("Assert the defaults"):
            assert cfg.mcp.server_name == "gns3"
            assert cfg.mcp.port == 8100
            assert cfg.pool.max_size == 200

    @autotest.num("323")
    @autotest.external_id("gns3-config-loader-overrides")
    @autotest.name("EnvConfigLoader: overrides via env vars")
    def test_gns3conf_build_overrides(self):
        with autotest.step("Build with custom values"):
            cfg = EnvConfigLoader._build(
                {
                    "MCP_SERVER_NAME": "custom",
                    "MCP_PORT": "9000",
                    "POOL_MAX_SIZE": "10",
                    "LOG_BUFFER_MAX_ENTRIES": "100",
                    "GNS3_SERVICE_URL": "http://gns3:8101",
                }
            )

        with autotest.step("Assert the overrides"):
            assert cfg.mcp.server_name == "custom"
            assert cfg.mcp.port == 9000
            assert cfg.pool.max_size == 10
            assert cfg.log_buffer.max_entries == 100
            assert cfg.gns3_service_url == "http://gns3:8101"

    @autotest.num("324")
    @autotest.external_id("gns3-config-loader-stdio-transport")
    @autotest.name("EnvConfigLoader: stdio transport")
    def test_gns3conf_stdio_transport(self):
        with autotest.step("Build with transport=stdio"):
            cfg = EnvConfigLoader._build({"MCP_TRANSPORT": "stdio"})

        with autotest.step("Assert"):
            assert cfg.mcp.transport == "stdio"
