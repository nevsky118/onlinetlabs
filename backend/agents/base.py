"""Базовый класс для всех агентов платформы."""

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from config.config_model import ConfigModel, LlmProvider
from llm.client import resolve_model


class BaseAgent:
    """Базовый агент. Наследники переопределяют system_prompt() и run()."""

    def __init__(self, config: ConfigModel):
        self.config = config
        self.agents_config = config.agents
        self._agents_by_model: dict[str, Agent] = {}

    def _agent_for(self, model_id: str) -> Agent:
        """pydantic-ai Agent под model_id, кэш по id."""
        if model_id not in self._agents_by_model:
            self._agents_by_model[model_id] = Agent(
                model=self._build_model(model_id),
                system_prompt=self.system_prompt(),
            )
        return self._agents_by_model[model_id]

    def _build_model(self, model_id: str) -> OpenAIModel:
        """OpenAI-совместимая модель (yandex/openrouter) по кредам провайдера."""
        creds, entry = resolve_model(model_id)
        headers = dict(creds.extra_headers or {})
        base_url = creds.base_url
        api_key = creds.api_key or "ollama"
        model_name = entry.model
        if creds.provider == LlmProvider.YANDEX:
            if not creds.yandex_folder:
                raise ValueError(f"yandex_folder required for YANDEX provider, model {model_id}")
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url or "https://ai.api.cloud.yandex.net/v1",
                default_headers={"x-folder-id": creds.yandex_folder, **headers},
            )
            model_name = f"gpt://{creds.yandex_folder}/{entry.model}"
            return OpenAIModel(model_name, provider=OpenAIProvider(openai_client=client))
        # openrouter / openai-compatible
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url=base_url, default_headers=headers or None)
        return OpenAIModel(model_name, provider=OpenAIProvider(openai_client=client))

    def system_prompt(self) -> str:
        """System prompt. Переопределяется в каждом агенте."""
        raise NotImplementedError

    async def run(self, input_data: BaseModel) -> BaseModel:
        """Основной метод. Переопределяется в каждом агенте."""
        raise NotImplementedError
