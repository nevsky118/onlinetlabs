"""Базовый класс для всех агентов платформы."""

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

from config.config_model import ConfigModel, LlmProvider


class BaseAgent:
    """Базовый агент. Наследники переопределяют system_prompt() и run()."""

    def __init__(self, config: ConfigModel):
        self.config = config
        self.agents_config = config.agents
        self._agent: Agent | None = None

    @property
    def agent(self) -> Agent:
        """Lazy-построение pydantic-ai Agent."""
        if self._agent is None:
            self._agent = self._build_agent()
        return self._agent

    def _build_agent(self) -> Agent:
        """Построить pydantic-ai Agent."""
        return Agent(
            model=self._get_model(),
            system_prompt=self.system_prompt(),
        )

    def _get_model(self) -> AnthropicModel | OpenAIModel:
        """Построить pydantic-ai model object из конфига."""
        cfg = self.agents_config
        match cfg.provider:
            case LlmProvider.ANTHROPIC:
                return AnthropicModel(
                    cfg.model,
                    provider=AnthropicProvider(api_key=cfg.api_key),
                )
            case LlmProvider.OPENAI:
                kwargs = {"api_key": cfg.api_key}
                if cfg.base_url:
                    kwargs["base_url"] = cfg.base_url
                return OpenAIModel(
                    cfg.model,
                    provider=OpenAIProvider(**kwargs),
                )
            case LlmProvider.OLLAMA:
                return OpenAIModel(
                    cfg.model,
                    provider=OpenAIProvider(base_url=cfg.base_url),
                )
            case _:
                raise ValueError(f"Unsupported LLM provider: {cfg.provider}")

    def system_prompt(self) -> str:
        """System prompt. Переопределяется в каждом агенте."""
        raise NotImplementedError

    async def run(self, input_data: BaseModel) -> BaseModel:
        """Основной метод. Переопределяется в каждом агенте."""
        raise NotImplementedError
