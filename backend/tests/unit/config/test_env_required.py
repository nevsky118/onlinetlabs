import pytest
from config.env_config_loader import _build

pytestmark = [pytest.mark.unit]


def _base_env():
    return {
        "DB_USER": "u", "DB_PASSWORD": "p", "DB_HOST": "h", "DB_PORT": "5432", "DB_NAME": "n",
        "REDIS_URL": "redis://localhost:6379/0", "ENVIRONMENT": "test", "JWT_SECRET": "s",
        "CRED_ENCRYPTION_KEY": "r1juy4ePJMqjrYbqXaCw7kDPq8Gwudckyv0wiIBIwfU=",
        "INTERNAL_API_TOKEN": "t", "YANDEX_API_KEY": "k", "YANDEX_FOLDER": "f", "LOG_LEVEL": "DEBUG",
        "AGENTS_CHAT_MODEL": "yandex-gpt-5.1", "AGENTS_INTERVENTION_MODEL": "yandex-gpt-5.1",
        "FRONTEND_URL": "http://localhost:3000", "GNS3_SERVICE_URL": "http://localhost:8101",
        "GNS3_PUBLIC_URL": "http://localhost:3080", "GNS3_INTERNAL_URL": "http://localhost:3080",
        "MCP_SERVER_URL": "http://localhost:8100",
    }


def test_missing_required_url_raises_with_clear_message():
    env = _base_env(); del env["GNS3_SERVICE_URL"]
    with pytest.raises(ValueError, match="Missing required env vars: GNS3_SERVICE_URL"):
        _build(env)


def test_builds_when_all_required_present():
    cfg = _build(_base_env())
    assert cfg.gns3.service_url == "http://localhost:8101"
