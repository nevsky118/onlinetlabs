import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from pydantic import ValidationError

from src.config.config_model import GNS3MCPConfigModel, MCPConfig
from src.config.env_config_loader import EnvConfigLoader

pytestmark = [pytest.mark.unit, pytest.mark.config]


class TestConfigModel:
    @autotest.num("320")
    @autotest.external_id("fb454d77-3ffe-4d4f-9abc-0f1258bb7847")
    @autotest.name("GNS3MCPConfigModel: default values")
    def test_fb454d77_defaults(self):
        with autotest.step("Create the default config"):
            cfg = GNS3MCPConfigModel()

        with autotest.step("Assert the defaults"):
            assert_equal(cfg.mcp.server_name, "gns3", "server name")
            assert_equal(cfg.mcp.transport, "streamable-http", "transport")
            assert_equal(cfg.mcp.host, "127.0.0.1", "host")
            assert_equal(cfg.mcp.port, 8100, "port")
            assert_equal(cfg.pool.max_size, 200, "max size")
            assert_equal(cfg.pool.idle_ttl, 600.0, "idle ttl")
            assert_equal(cfg.pool.health_check_interval, 60.0, "health check interval")
            assert_equal(cfg.pool.min_evict_idle, 30.0, "min evict idle")
            assert_equal(cfg.log_buffer.max_entries, 500, "max entries")
            assert_equal(cfg.log_buffer.inactivity_timeout, 300.0, "inactivity timeout")
            assert_equal(cfg.gns3_service_url, "http://localhost:8101", "gns3 service url")

    @autotest.num("321")
    @autotest.external_id("9e309cff-0725-47ca-8d74-e3a0adb2595a")
    @autotest.name("MCPConfig: invalid transport")
    def test_9e309cff_invalid_transport(self):
        with autotest.step("Create a config with an invalid transport"):
            with pytest.raises(ValidationError):
                MCPConfig(transport="grpc")


class TestEnvConfigLoader:
    @autotest.num("322")
    @autotest.external_id("365a6afd-2666-456e-944a-e340036913f9")
    @autotest.name("EnvConfigLoader: empty dict → default values")
    def test_365a6afd_build_defaults(self):
        with autotest.step("Build from an empty dict"):
            cfg = EnvConfigLoader._build({})

        with autotest.step("Assert the defaults"):
            assert_equal(cfg.mcp.server_name, "gns3", "server name")
            assert_equal(cfg.mcp.port, 8100, "port")
            assert_equal(cfg.pool.max_size, 200, "max size")

    @autotest.num("323")
    @autotest.external_id("3e8a5993-5f21-4265-b527-502427a15740")
    @autotest.name("EnvConfigLoader: overrides via env vars")
    def test_3e8a5993_build_overrides(self):
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
            assert_equal(cfg.mcp.server_name, "custom", "server name")
            assert_equal(cfg.mcp.port, 9000, "port")
            assert_equal(cfg.pool.max_size, 10, "max size")
            assert_equal(cfg.log_buffer.max_entries, 100, "max entries")
            assert_equal(cfg.gns3_service_url, "http://gns3:8101", "gns3 service url")

    @autotest.num("324")
    @autotest.external_id("65c312ad-f20b-484a-83dd-1464239cb79b")
    @autotest.name("EnvConfigLoader: stdio transport")
    def test_65c312ad_stdio_transport(self):
        with autotest.step("Build with transport=stdio"):
            cfg = EnvConfigLoader._build({"MCP_TRANSPORT": "stdio"})

        with autotest.step("Assert"):
            assert_equal(cfg.mcp.transport, "stdio", "transport")
