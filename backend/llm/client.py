"""AsyncOpenAI клиент под текущего LLM-провайдера (пилот: Yandex)."""

from openai import AsyncOpenAI

from config import settings


def get_llm_client() -> AsyncOpenAI:
    """Создаёт AsyncOpenAI-клиент под текущего провайдера, подставляя base_url и заголовки для Yandex."""
    cfg = settings.agents
    headers = {}
    base_url = cfg.base_url
    if cfg.provider.value == "yandex":
        headers["x-folder-id"] = cfg.yandex_folder
        base_url = base_url or "https://ai.api.cloud.yandex.net/v1"
    return AsyncOpenAI(
        api_key=cfg.api_key or "ollama",
        base_url=base_url,
        default_headers=headers or None,
    )


def default_model() -> str:
    """Возвращает URI модели по умолчанию из конфигурации агентов."""
    return settings.agents.model_uri
