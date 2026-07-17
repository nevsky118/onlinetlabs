"""Resolve LLM provider and client by model_id from the catalog."""

from openai import AsyncOpenAI

from config import settings
from config.config_model import LlmProvider, ModelEntry, ProviderCreds


def resolve_model(model_id: str) -> tuple[ProviderCreds, ModelEntry]:
    """Returns (provider creds, catalog entry) for model_id. Raises KeyError if missing."""
    cfg = settings.agents
    entry = cfg.get_entry(model_id)
    if entry is None:
        raise KeyError(f"Unknown model_id: {model_id}")
    return cfg.providers[entry.provider_ref], entry


def build_client(model_id: str) -> AsyncOpenAI:
    """AsyncOpenAI for the selected model's provider (base_url + key + headers)."""
    creds, _ = resolve_model(model_id)
    headers = dict(creds.extra_headers or {})
    base_url = creds.base_url
    if creds.provider == LlmProvider.YANDEX:
        headers["x-folder-id"] = creds.yandex_folder
        base_url = base_url or "https://ai.api.cloud.yandex.net/v1"
    return AsyncOpenAI(
        api_key=creds.api_key or "ollama",
        base_url=base_url,
        default_headers=headers or None,
    )


def model_uri(model_id: str) -> str:
    """Model string for the API. Yandex needs gpt://folder/model, everyone else just the slug."""
    creds, entry = resolve_model(model_id)
    if creds.provider == LlmProvider.YANDEX and creds.yandex_folder:
        return f"gpt://{creds.yandex_folder}/{entry.model}"
    return entry.model


def model_supports_tools(model_id: str) -> bool:
    """Whether the model supports function calling."""
    _, entry = resolve_model(model_id)
    return entry.tools
