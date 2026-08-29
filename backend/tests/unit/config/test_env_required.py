import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from config.env_config_loader import _build

pytestmark = [pytest.mark.unit]


def _base_env():
    return {
        "DB_USER": "u",
        "DB_PASSWORD": "p",
        "DB_HOST": "h",
        "DB_PORT": "5432",
        "DB_NAME": "n",
        "REDIS_URL": "redis://localhost:6379/0",
        "ENVIRONMENT": "test",
        "JWT_SECRET": "s",
        "CRED_ENCRYPTION_KEY": "r1juy4ePJMqjrYbqXaCw7kDPq8Gwudckyv0wiIBIwfU=",
        "INTERNAL_API_TOKEN": "t",
        "YANDEX_API_KEY": "k",
        "YANDEX_FOLDER": "f",
        "LOG_LEVEL": "DEBUG",
        "AGENTS_CHAT_MODEL": "yandex-gpt-5.1",
        "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
        "FRONTEND_URL": "http://localhost:3000",
        "GNS3_SERVICE_URL": "http://localhost:8101",
        "GNS3_PUBLIC_URL": "http://localhost:3080",
        "GNS3_INTERNAL_URL": "http://localhost:3080",
        "MCP_SERVER_URL": "http://localhost:8100",
    }


class TestEnvRequired:
    @autotest.num("3224")
    @autotest.external_id("0a250261-625e-4651-9f47-4f9eb82593f8")
    @autotest.name(
        "env_config_loader._build: raises with a clear message on a missing required var"
    )
    def test_0a250261_missing_required_url_raises_with_clear_message(self):
        with autotest.step("Arrange: env missing GNS3_SERVICE_URL"):
            env = _base_env()
            del env["GNS3_SERVICE_URL"]

        with autotest.step("Act+Assert: _build raises naming the missing var"):
            with pytest.raises(ValueError, match="Missing required env vars: GNS3_SERVICE_URL"):
                _build(env)

    @autotest.num("3225")
    @autotest.external_id("d9c5a1bb-68f6-4b3f-819b-d81d3e8a971d")
    @autotest.name("env_config_loader._build: builds config when all required vars are present")
    def test_d9c5a1bb_builds_when_all_required_present(self):
        with autotest.step("Act: _build with a complete env"):
            cfg = _build(_base_env())

        with autotest.step("Assert: gns3.service_url is carried through"):
            assert_equal(cfg.gns3.service_url, "http://localhost:8101", "service url")
