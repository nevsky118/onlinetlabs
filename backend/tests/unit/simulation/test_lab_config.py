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
    @autotest.name("lab_config: the correct command matches the reference from spec.expect")
    async def test_1ba8c09f_correct_command_matches_spec_expectation(self):
        with autotest.step("Arrange: static addressing spec"):
            spec = _STATIC_SPEC

        with autotest.step("Act: build node tasks"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: commands are built from expect.ip per node"):
            assert_equal([t.node for t in tasks], ["PC1", "PC2"], "nodes")
            assert_equal(tasks[0].correct_cmd, "ip 192.168.1.11/24", "PC1 command")
            assert_equal(tasks[1].correct_cmd, "ip 192.168.1.12/24", "PC2 command")

    @autotest.num("2018")
    @autotest.external_id("90a1edac-592c-470a-af97-4fd0f68efe45")
    @autotest.name("lab_config: the wrong command lands in a different subnet (check fails)")
    async def test_90a1edac_wrong_command_lands_in_another_subnet(self):
        with autotest.step("Arrange: static addressing spec"):
            spec = _STATIC_SPEC

        with autotest.step("Act: build node tasks"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: error is plausible, same address, different subnet"):
            assert_equal(tasks[0].wrong_cmd, "ip 192.168.2.11/24", "wrong command")
            assert_true(tasks[0].wrong_cmd != tasks[0].correct_cmd, "error differs from correct")

    @autotest.num("2019")
    @autotest.external_id("26ed4bd9-c448-4c7b-baed-5573fe5130b5")
    @autotest.name("lab_config: connectivity checks (vpcs.ping) don't produce configuration tasks")
    async def test_26ed4bd9_connectivity_checks_are_ignored(self):
        with autotest.step("Arrange: spec contains both show_ip and ping"):
            spec = _STATIC_SPEC

        with autotest.step("Act: build node tasks"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: only addressing, connectivity is its consequence"):
            assert_equal(len(tasks), 2, "task count")

    @autotest.num("2020")
    @autotest.external_id("06ffc4d7-13af-4707-920c-3fe96c9719a6")
    @autotest.name("lab_config: empty spec → no tasks")
    async def test_06ffc4d7_empty_spec_yields_no_tasks(self):
        with autotest.step("Arrange: empty spec"):
            spec: dict = {}

        with autotest.step("Act: build node tasks"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: no tasks"):
            assert_equal(tasks, [], "tasks")

    @autotest.num("2021")
    @autotest.external_id("972745d4-e903-40df-8c8c-e9d0ae822c91")
    @autotest.name("lab_config: DHCP lab, correct action is `ip dhcp`, not static")
    async def test_972745d4_dhcp_lab_uses_dhcp_client(self):
        with autotest.step("Arrange: spec with vpcs.ip_in_subnet (address assigned by DHCP)"):
            spec = _DHCP_SPEC

        with autotest.step("Act: build node tasks"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: correct command is the DHCP client"):
            assert_equal(len(tasks), 1, "task count")
            assert_equal(tasks[0].correct_cmd, "ip dhcp", "correct command")

    @autotest.num("2022")
    @autotest.external_id("22331f3f-a139-489b-8db4-4fa62098c338")
    @autotest.name("lab_config: DHCP lab, the error is static addressing in another subnet")
    async def test_22331f3f_dhcp_wrong_command_is_static_in_other_subnet(self):
        with autotest.step("Arrange: spec with vpcs.ip_in_subnet"):
            spec = _DHCP_SPEC

        with autotest.step("Act: build node tasks"):
            tasks = build_node_tasks(spec)

        with autotest.step("Assert: the wrong command is static outside the expected subnet"):
            assert_true(tasks[0].wrong_cmd.startswith("ip 192.168.11."), "different subnet")
            assert_true(tasks[0].wrong_cmd != tasks[0].correct_cmd, "error differs from correct")
