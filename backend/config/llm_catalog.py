"""Дефолтный каталог LLM-моделей. Секреты провайдеров подставляются из env."""

from config.config_model import ModelEntry


def default_catalog() -> list[ModelEntry]:
    """Сид-каталог: Yandex напрямую + модели через OpenRouter (все tools-capable)."""
    return [
        ModelEntry(id="yandex-gpt-5.1", label="YandexGPT 5.1 Pro",
                   provider_ref="yandex", model="yandexgpt/latest"),
        ModelEntry(id="claude-opus-4.8", label="Claude Opus 4.8",
                   provider_ref="openrouter", model="anthropic/claude-opus-4.8"),
        ModelEntry(id="claude-sonnet-4.5", label="Claude Sonnet 4.5",
                   provider_ref="openrouter", model="anthropic/claude-sonnet-4.5"),
        ModelEntry(id="claude-haiku-4.5", label="Claude Haiku 4.5",
                   provider_ref="openrouter", model="anthropic/claude-haiku-4.5"),
        ModelEntry(id="gemini-2.5-flash", label="Gemini 2.5 Flash",
                   provider_ref="openrouter", model="google/gemini-2.5-flash"),
        ModelEntry(id="gpt-5-mini", label="GPT-5 mini",
                   provider_ref="openrouter", model="openai/gpt-5-mini"),
        ModelEntry(id="deepseek-v3.1", label="DeepSeek V3.1",
                   provider_ref="openrouter", model="deepseek/deepseek-chat-v3.1"),
        # Free-tier без пополнения баланса OpenRouter (rate-limited).
        # Named/детерминированная — знаем, какая модель отвечала (важно для экспериментов).
        ModelEntry(id="qwen3-next-free", label="Qwen3 Next (free)",
                   provider_ref="openrouter", model="qwen/qwen3-next-80b-a3b-instruct:free"),
        # Авто-роутер OpenRouter по free-моделям — надёжнее (меньше 429), но недетерминирован.
        ModelEntry(id="openrouter-free", label="OpenRouter Free (auto)",
                   provider_ref="openrouter", model="openrouter/free"),
    ]
