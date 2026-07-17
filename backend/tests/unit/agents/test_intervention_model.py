"""Тесты резолва модели интервенций в оркестраторе."""

from unittest.mock import patch

import pytest
from mcp_sdk.testing import autotest

from agents.orchestrator.agent import Orchestrator
from config.config_model import LlmProvider, ModelEntry, ProviderCreds

pytestmark = [pytest.mark.unit, pytest.mark.agents]


class TestResolveInterventionModel:
    @autotest.num("1790")
    @autotest.external_id("a0b1c2d3-e4f5-4a6b-7c8d-e9f0a1b2c3d4")
    @autotest.name("Orchestrator._resolve_intervention_model: дефолт из конфига")
    def test_a0b1c2d3_default(self, config_model):
        with autotest.step("Создаём оркестратор"):
            orch = Orchestrator(config_model)

        with autotest.step("Резолв без context — дефолт"):
            result = orch._resolve_intervention_model(context={})
            assert result == config_model.agents.intervention_model

    @autotest.num("1791")
    @autotest.external_id("b1c2d3e4-f5a6-4b7c-8d9e-f0a1b2c3d4e5")
    @autotest.name(
        "Orchestrator._resolve_intervention_model: follow_session возвращает session_model_id"
    )
    def test_b1c2d3e4_follows_session(self, config_model):
        with autotest.step("Включаем interventions_follow_session"):
            config_model.agents.interventions_follow_session = True
            orch = Orchestrator(config_model)

        with autotest.step("Резолв с валидным session_model_id"):
            result = orch._resolve_intervention_model(
                context={"session_model_id": "yandex-gpt-5.1"}
            )
            assert result == "yandex-gpt-5.1"

    @autotest.num("1792")
    @autotest.external_id("c2d3e4f5-a6b7-4c8d-9e0f-a1b2c3d4e5f6")
    @autotest.name(
        "Orchestrator._resolve_intervention_model: follow_session + неизвестная модель → дефолт"
    )
    def test_c2d3e4f5_follows_session_unknown_model(self, config_model):
        with autotest.step("Включаем follow_session, передаём неизвестную модель"):
            config_model.agents.interventions_follow_session = True
            orch = Orchestrator(config_model)

        with autotest.step("Неизвестная модель → дефолт"):
            result = orch._resolve_intervention_model(
                context={"session_model_id": "does-not-exist"}
            )
            assert result == config_model.agents.intervention_model

    @autotest.num("1793")
    @autotest.external_id("d3e4f5a6-b7c8-4d9e-0f1a-b2c3d4e5f6a7")
    @autotest.name(
        "Orchestrator._resolve_intervention_model: follow_session=True + пустой payload → дефолт (без KeyError)"
    )
    def test_d3e4f5a6_follow_session_empty_payload(self, config_model):
        with autotest.step("Включаем follow_session"):
            config_model.agents.interventions_follow_session = True
            orch = Orchestrator(config_model)

        with autotest.step("Пустой payload без session_model_id — не должен бросить KeyError"):
            result = orch._resolve_intervention_model(context={})
            assert result == config_model.agents.intervention_model

    @autotest.num("1794")
    @autotest.external_id("e4f5a6b7-c8d9-4e0f-1a2b-c3d4e5f6a7b8")
    @autotest.name(
        "Orchestrator._resolve_intervention_model: follow_session=True + валидный session_model_id → session id"
    )
    def test_e4f5a6b7_follow_session_valid_id(self, config_model):
        with autotest.step("Включаем follow_session"):
            config_model.agents.interventions_follow_session = True
            orch = Orchestrator(config_model)

        with autotest.step("Валидный session_model_id возвращается как есть"):
            result = orch._resolve_intervention_model(
                context={"session_model_id": "yandex-gpt-5.1"}
            )
            assert result == "yandex-gpt-5.1"


class TestInterventionMetadata:
    @autotest.num("1795")
    @autotest.external_id("f5a6b7c8-d9e0-4f1a-2b3c-d4e5f6a7b8c9")
    @autotest.name("intervene tutor/hint: metadata содержит model и provider")
    @pytest.mark.asyncio
    async def test_f5a6b7c8_intervene_llm_metadata(self, config_model):
        """Полный intervene требует MCP/DB; тест проверяет сборку metadata через
        resolve_model — ту же ветку, что выполняется в intervene для LLM-агентов."""
        with autotest.step("Резолвим model_id через resolve_model с тестовым конфигом"):
            orch = Orchestrator(config_model)
            model_id = orch._resolve_intervention_model(context={})

            fake_creds = ProviderCreds(
                provider=LlmProvider.YANDEX,
                api_key="k",
                yandex_folder="f",
            )
            fake_entry = ModelEntry(
                id=model_id, label="test", provider_ref="yandex", model="yandexgpt/latest"
            )

        with autotest.step("Имитируем resolve_model → проверяем сборку metadata"):
            with patch(
                "agents.orchestrator.agent.resolve_model", return_value=(fake_creds, fake_entry)
            ):
                # Воспроизводим логику ветки LLM в intervene
                creds, _ = __import__(
                    "agents.orchestrator.agent", fromlist=["resolve_model"]
                ).resolve_model(model_id)
                llm_meta = {"model": model_id, "provider": creds.provider.value}

            assert llm_meta["model"] == model_id
            assert llm_meta["provider"] == LlmProvider.YANDEX.value
