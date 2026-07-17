"""Default catalog of LLM models. Provider secrets are substituted from env."""

from config.config_model import ModelEntry


def default_catalog() -> list[ModelEntry]:
    """Seed catalog: Yandex direct + models via OpenRouter (all tools-capable)."""
    return [
        ModelEntry(
            id="yandex-gpt-5.1",
            label="YandexGPT 5.1 Pro",
            provider_ref="yandex",
            model="yandexgpt/latest",
        ),
        ModelEntry(
            id="claude-opus-4.8",
            label="Claude Opus 4.8",
            provider_ref="openrouter",
            model="anthropic/claude-opus-4.8",
        ),
        ModelEntry(
            id="claude-sonnet-4.5",
            label="Claude Sonnet 4.5",
            provider_ref="openrouter",
            model="anthropic/claude-sonnet-4.5",
        ),
        ModelEntry(
            id="claude-haiku-4.5",
            label="Claude Haiku 4.5",
            provider_ref="openrouter",
            model="anthropic/claude-haiku-4.5",
        ),
        ModelEntry(
            id="gemini-2.5-flash",
            label="Gemini 2.5 Flash",
            provider_ref="openrouter",
            model="google/gemini-2.5-flash",
        ),
        ModelEntry(
            id="gpt-5-mini",
            label="GPT-5 mini",
            provider_ref="openrouter",
            model="openai/gpt-5-mini",
        ),
        ModelEntry(
            id="deepseek-v3.1",
            label="DeepSeek V3.1",
            provider_ref="openrouter",
            model="deepseek/deepseek-chat-v3.1",
        ),
        # Free-tier, no OpenRouter balance top-up (rate-limited).
        # Named and deterministic, so we know which model answered (important for experiments).
        ModelEntry(
            id="qwen3-next-free",
            label="Qwen3 Next (free)",
            provider_ref="openrouter",
            model="qwen/qwen3-next-80b-a3b-instruct:free",
        ),
        # OpenRouter auto-router over free models, more reliable (fewer 429s) but nondeterministic.
        ModelEntry(
            id="openrouter-free",
            label="OpenRouter Free (auto)",
            provider_ref="openrouter",
            model="openrouter/free",
        ),
    ]
