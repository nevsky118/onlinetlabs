"""lab_config: student console commands are derived FROM THE LAB SPEC, not hardcoded."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from simulation.lab_config import build_node_tasks

pytestmark = [pytest.mark.unit]

_STATIC_SPEC = {
    "slug": "lan-static-ip",
    "steps": [
        {
            "id": "pc-ips",
            "checks": [
                {
                    "kind": "vpcs.show_ip",
                    "node": "PC1",
                    "expect": {"ip": "192.168.1.11/24", "gateway": "0.0.0.0"},
                },
                {
                    "kind": "vpcs.show_ip",
                    "node": "PC2",
                    "expect": {"ip": "192.168.1.12/24", "gateway": "0.0.0.0"},
                },
            ],
        },
        {"id": "connectivity", "checks": [{"kind": "vpcs.ping", "from": "PC1", "to": "x"}]},
    ],
}

_DHCP_SPEC = {
    "slug": "dhcp-basics",
    "steps": [
        {
            "id": "dhcp",
            "checks": [
                {
                    "kind": "vpcs.ip_in_subnet",
                    "node": "PC1",
                    "expect": {"subnet": "192.168.10.0/24", "gateway": "192.168.10.1"},
                },
            ],
        }
    ],
}


class TestBuildNodeTasks:
    @autotest.num("2017")
    @autotest.external_id("1ba8c09f-7e59-4428-9c5a-fde5e9444c78")
    @autotest.name("lab_config: верная команда совпадает с эталоном из spec.expect")
    async def test_1ba8c09f_correct_command_matches_spec_expectation(self):
        with autotest.step("Arrange: спека статической адресации"):
            spec = _STATIC_SPEC

        with autotest.step("Act: строим задачи узлов"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: команды собраны из expect.ip по узлам"):
            assert_equal([t.node for t in tasks], ["PC1", "PC2"], "узлы")
            assert_equal(tasks[0].correct_cmd, "ip 192.168.1.11/24", "команда PC1")
            assert_equal(tasks[1].correct_cmd, "ip 192.168.1.12/24", "команда PC2")

    @autotest.num("2018")
    @autotest.external_id("90a1edac-592c-470a-af97-4fd0f68efe45")
    @autotest.name("lab_config: ошибочная команда уводит в чужую подсеть (проверка падает)")
    async def test_90a1edac_wrong_command_lands_in_another_subnet(self):
        with autotest.step("Arrange: спека статической адресации"):
            spec = _STATIC_SPEC

        with autotest.step("Act: строим задачи узлов"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: ошибка правдоподобна — тот же адрес, другая подсеть"):
            assert_equal(tasks[0].wrong_cmd, "ip 192.168.2.11/24", "ошибочная команда")
            assert_true(tasks[0].wrong_cmd != tasks[0].correct_cmd, "ошибка отличается от верной")

    @autotest.num("2019")
    @autotest.external_id("26ed4bd9-c448-4c7b-baed-5573fe5130b5")
    @autotest.name("lab_config: проверки связности (vpcs.ping) не дают задачи конфигурации")
    async def test_26ed4bd9_connectivity_checks_are_ignored(self):
        with autotest.step("Arrange: спека содержит и show_ip, и ping"):
            spec = _STATIC_SPEC

        with autotest.step("Act: строим задачи узлов"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: только адресация — связность её следствие"):
            assert_equal(len(tasks), 2, "число задач")

    @autotest.num("2020")
    @autotest.external_id("06ffc4d7-13af-4707-920c-3fe96c9719a6")
    @autotest.name("lab_config: пустая спека → нет задач")
    async def test_06ffc4d7_empty_spec_yields_no_tasks(self):
        with autotest.step("Arrange: пустая спека"):
            spec: dict = {}

        with autotest.step("Act: строим задачи узлов"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: задач нет"):
            assert_equal(tasks, [], "задачи")

    @autotest.num("2021")
    @autotest.external_id("972745d4-e903-40df-8c8c-e9d0ae822c91")
    @autotest.name("lab_config: DHCP-лаба — верное действие `ip dhcp`, а не статика")
    async def test_972745d4_dhcp_lab_uses_dhcp_client(self):
        with autotest.step("Arrange: спека с vpcs.ip_in_subnet (адрес выдаёт DHCP)"):
            spec = _DHCP_SPEC

        with autotest.step("Act: строим задачи узлов"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: верная команда — DHCP-клиент"):
            assert_equal(len(tasks), 1, "число задач")
            assert_equal(tasks[0].correct_cmd, "ip dhcp", "верная команда")

    @autotest.num("2022")
    @autotest.external_id("22331f3f-a139-489b-8db4-4fa62098c338")
    @autotest.name("lab_config: DHCP-лаба — ошибка это статика в чужой подсети")
    async def test_22331f3f_dhcp_wrong_command_is_static_in_other_subnet(self):
        with autotest.step("Arrange: спека с vpcs.ip_in_subnet"):
            spec = _DHCP_SPEC

        with autotest.step("Act: строим задачи узлов"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: ошибочная команда — статика вне ожидаемой подсети"):
            assert_true(tasks[0].wrong_cmd.startswith("ip 192.168.11."), "чужая подсеть")
            assert_true(tasks[0].wrong_cmd != tasks[0].correct_cmd, "ошибка отличается от верной")
