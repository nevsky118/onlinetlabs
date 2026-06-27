# Smoke-тесты гейта активации аккаунта.
# Активированный пользователь имеет доступ к ресурсам (запуск лаб, ИИ);
# require_active_user не блокирует активного. Блокировка неактивного (403)
# покрыта backend-юнит-тестами — в API-наборе нет аккаунта-источника
# неактивного пользователя (credential-аккаунты активны).

import pytest

from autotests.api.api_helpers.onlinetlabs_service.sessions_helper_api import (
    SessionsHelperApi,
)
from autotests.settings.reports import autotest
from autotests.settings.utils.custom_assertions import assert_is_not_none


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
class TestActivationSmokeApi:
    """Smoke-тесты гейта активации: активный пользователь не блокируется."""

    @pytest.fixture(autouse=True)
    def setup(self, anon_client, config):
        self.sessions_helper = SessionsHelperApi(anon_client, config)

    @autotest.num("804")
    @autotest.external_id("3a985e9f-26b7-4fe1-84dc-9834a296fa67")
    @autotest.name(
        "Smoke: активный пользователь проходит гейт активации и запускает лабу"
    )
    async def test_3a985e9f_active_user_passes_activation_gate(self):
        """Активный пользователь не получает 403 require_active_user и запускает лабу."""
        # Act
        with autotest.step("Активный пользователь запускает autotest-lab"):
            body = await self.sessions_helper.launch_session("autotest-lab")

        # Assert
        with autotest.step("Гейт активации пройден: сессия создана (нет 403)"):
            assert_is_not_none(
                body.get("session_id"),
                "session_id присутствует — активный пользователь не заблокирован",
            )
