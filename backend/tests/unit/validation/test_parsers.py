"""Unit tests for pure check-handler parsers."""

from pathlib import Path

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_in,
    assert_is_none,
    assert_is_not_none,
    assert_true,
)

from validation.checks.cisco import (
    _parse_cisco_interface,
    _parse_cisco_neighbor,
    _parse_cisco_route,
)
from validation.checks.frr import _parse_neighbor_state, _parse_route
from validation.checks.vpcs import _matches, _parse_ping

pytestmark = [pytest.mark.unit]

_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


# ---------------- FRR: ospf neighbor ----------------


class TestParsers:
    @autotest.num("3268")
    @autotest.external_id("3f8b4dbb-77d4-44ea-af7e-ec53002fd194")
    @autotest.name("FRR neighbor state: Full/DR for 2.2.2.2")
    def test_3f8b4dbb_parse_neighbor_state_full_dr(self):
        with autotest.step("Arrange: fixture FRR 'show ip ospf neighbor' output"):
            stdout = _load("show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: neighbor 2.2.2.2 state is Full/DR"):
            assert_equal(
                _parse_neighbor_state(stdout, "2.2.2.2"),
                "Full/DR",
                "parse neighbor state",
            )

    @autotest.num("3269")
    @autotest.external_id("2512169e-3b2d-4d81-8619-6707d56f4f55")
    @autotest.name("FRR neighbor state: Full/Backup for 3.3.3.3")
    def test_2512169e_parse_neighbor_state_full_backup(self):
        with autotest.step("Arrange: fixture FRR 'show ip ospf neighbor' output"):
            stdout = _load("show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: neighbor 3.3.3.3 state is Full/Backup"):
            assert_equal(
                _parse_neighbor_state(stdout, "3.3.3.3"),
                "Full/Backup",
                "parse neighbor state",
            )

    @autotest.num("3270")
    @autotest.external_id("df0b13c2-a713-4cb1-8383-9258793c517d")
    @autotest.name("FRR neighbor state: 2-Way/DROther for 4.4.4.4")
    def test_df0b13c2_parse_neighbor_state_two_way(self):
        with autotest.step("Arrange: fixture FRR 'show ip ospf neighbor' output"):
            stdout = _load("show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: neighbor 4.4.4.4 state is 2-Way/DROther"):
            assert_equal(
                _parse_neighbor_state(stdout, "4.4.4.4"),
                "2-Way/DROther",
                "parse neighbor state",
            )

    @autotest.num("3271")
    @autotest.external_id("00a29ccd-8854-4dac-91e2-516a7fbae3dc")
    @autotest.name("FRR neighbor state: returns None for an unknown neighbor")
    def test_00a29ccd_parse_neighbor_state_missing(self):
        with autotest.step("Arrange: fixture FRR 'show ip ospf neighbor' output"):
            stdout = _load("show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: unknown neighbor 9.9.9.9 returns None"):
            assert_is_none(_parse_neighbor_state(stdout, "9.9.9.9"), "parse neighbor state")

    @autotest.num("3272")
    @autotest.external_id("f8bfc638-79b5-40f2-843e-b0dad51b642c")
    @autotest.name("FRR neighbor state: returns None on empty output")
    def test_f8bfc638_parse_neighbor_state_empty_output(self):
        with autotest.step("Arrange: output with only the header, no neighbor rows"):
            empty = "\nNeighbor ID     Pri State           Up Time         ...\n\n"

        with autotest.step("Act+Assert: returns None"):
            assert_is_none(_parse_neighbor_state(empty, "2.2.2.2"), "parse neighbor state")

    # ---------------- FRR: route ----------------

    @autotest.num("3273")
    @autotest.external_id("c69b896b-efc8-4f28-9072-b2a84b213c75")
    @autotest.name("FRR route: matches the active OSPF route (O>*)")
    def test_c69b896b_parse_route_ospf_active(self):
        with autotest.step("Arrange: fixture FRR 'show ip route ospf' output"):
            stdout = _load("show_ip_route_ospf.txt")

        with autotest.step("Act: _parse_route for 192.168.110.0/24"):
            parsed = _parse_route(stdout, "192.168.110.0/24")

        with autotest.step("Assert: matched as the active OSPF route (O>*)"):
            assert_is_not_none(parsed, "parsed")
            code, line = parsed
            assert_equal(code, "O>*", "code")
            assert_in("via 10.0.12.2", line, "'via 10.0.12.2'")

    @autotest.num("3274")
    @autotest.external_id("b2af81d6-b47b-4ece-aa54-aaeb029b9112")
    @autotest.name("FRR route: matches a secondary OSPF route (O>*)")
    def test_b2af81d6_parse_route_ospf_secondary(self):
        with autotest.step("Arrange: fixture FRR 'show ip route ospf' output"):
            stdout = _load("show_ip_route_ospf.txt")

        with autotest.step("Act: _parse_route for 192.168.120.0/24"):
            parsed = _parse_route(stdout, "192.168.120.0/24")

        with autotest.step("Assert: matched as an active OSPF route (O>*)"):
            assert_is_not_none(parsed, "parsed")
            assert_equal(parsed[0], "O>*", "parsed[0]")

    @autotest.num("3275")
    @autotest.external_id("d9d24f69-23b4-45bc-83d1-2391d675b534")
    @autotest.name("FRR route: matches a competing route without >* (O)")
    def test_d9d24f69_parse_route_connected(self):
        with autotest.step("Arrange: fixture FRR 'show ip route ospf' output"):
            stdout = _load("show_ip_route_ospf.txt")

        with autotest.step("Act: _parse_route for 10.0.12.0/24"):
            parsed = _parse_route(stdout, "10.0.12.0/24")

        with autotest.step("Assert: matched as a competing route without >* (O)"):
            assert_is_not_none(parsed, "parsed")
            # `O` without `>*`, this is a competing route, still matches.
            assert_equal(parsed[0], "O", "parsed[0]")

    @autotest.num("3276")
    @autotest.external_id("4c417a0e-a57d-425e-8859-1c9be2b899ee")
    @autotest.name("FRR route: returns None for an unmatched prefix")
    def test_4c417a0e_parse_route_missing(self):
        with autotest.step("Arrange: fixture FRR 'show ip route ospf' output"):
            stdout = _load("show_ip_route_ospf.txt")

        with autotest.step("Act+Assert: an unmatched prefix returns None"):
            assert_is_none(_parse_route(stdout, "172.16.0.0/16"), "parse route")

    # ---------------- VPCS: ping ----------------

    @autotest.num("3277")
    @autotest.external_id("0b0b9618-c6ef-4ec7-a4c2-5f10e0a28e2d")
    @autotest.name("VPCS ping: parses received count and TTL on success")
    def test_0b0b9618_parse_ping_success_5_packets(self):
        with autotest.step("Arrange: fixture VPCS ping output with 5 successful replies"):
            text = _load("vpcs_ping_success.txt")

        with autotest.step("Act: _parse_ping"):
            parsed = _parse_ping(text)

        with autotest.step("Assert: received count and TTL"):
            assert_equal(parsed["received"], 5, "received")
            assert_equal(parsed["ttl"], 62, "ttl")

    @autotest.num("3278")
    @autotest.external_id("d7ce6be7-dbbb-4080-8a0e-b21c207f3717")
    @autotest.name("VPCS ping: received=0 and ttl=None when there are no replies")
    def test_d7ce6be7_parse_ping_failure_no_replies(self):
        with autotest.step("Arrange: fixture VPCS ping output with no replies"):
            text = _load("vpcs_ping_failure.txt")

        with autotest.step("Act: _parse_ping"):
            parsed = _parse_ping(text)

        with autotest.step("Assert: received=0, ttl=None"):
            assert_equal(parsed["received"], 0, "received")
            assert_is_none(parsed["ttl"], "ttl")

    @autotest.num("3279")
    @autotest.external_id("6ca797cb-2342-4bd0-971b-1347ec545b20")
    @autotest.name("VPCS ping: garbage input returns received=0, ttl=None")
    def test_6ca797cb_parse_ping_handles_garbage(self):
        with autotest.step("Arrange: unrelated, non-ping text"):
            text = "random unrelated text"

        with autotest.step("Act: _parse_ping"):
            parsed = _parse_ping(text)

        with autotest.step("Assert: received=0, ttl=None"):
            assert_equal(parsed, {"received": 0, "ttl": None}, "parsed")

    # ---------------- VPCS: _matches ----------------

    @pytest.mark.parametrize(
        ("actual", "expected", "ok"),
        [
            (5, 5, True),
            (5, ">=4", True),
            (3, ">=4", False),
            (4, "=4", True),
            (4, "==4", True),
            (62, 62, True),
            (62, ">60", True),
            (60, "<=62", True),
            (None, ">=1", False),
            (5, "garbage", False),
        ],
    )
    @autotest.num("3280")
    @autotest.external_id("33cd1fa8-c6e2-4edf-b1c8-389772b5c836")
    @autotest.name("VPCS _matches: comparator matrix (equality, >=, <=, >, <, garbage)")
    def test_33cd1fa8_matches(self, actual, expected, ok):
        with autotest.step("Act+Assert: _matches matches the expected verdict"):
            assert_true(_matches(actual, expected) is ok, "_matches(actual, expected) is ok")

    # ---------------- Cisco: ospf neighbor ----------------

    @autotest.num("3281")
    @autotest.external_id("d00379b5-7c9b-41a6-b860-9bcac534c676")
    @autotest.name("Cisco neighbor: FULL/BDR for 2.2.2.2")
    def test_d00379b5_parse_cisco_neighbor_full_bdr(self):
        with autotest.step("Arrange: fixture Cisco 'show ip ospf neighbor' output"):
            stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: neighbor 2.2.2.2 state is FULL/BDR"):
            assert_equal(
                _parse_cisco_neighbor(stdout, "2.2.2.2"),
                "FULL/BDR",
                "parse cisco neighbor",
            )

    @autotest.num("3282")
    @autotest.external_id("00ca9e6b-0e06-4609-ae5a-4880c5407746")
    @autotest.name("Cisco neighbor: FULL/DR for 3.3.3.3")
    def test_00ca9e6b_parse_cisco_neighbor_full_dr(self):
        with autotest.step("Arrange: fixture Cisco 'show ip ospf neighbor' output"):
            stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: neighbor 3.3.3.3 state is FULL/DR"):
            assert_equal(
                _parse_cisco_neighbor(stdout, "3.3.3.3"),
                "FULL/DR",
                "parse cisco neighbor",
            )

    @autotest.num("3283")
    @autotest.external_id("ad09631f-f19d-4c41-8ab6-5149f06699d9")
    @autotest.name("Cisco neighbor: 2WAY/DROTHER for 4.4.4.4")
    def test_ad09631f_parse_cisco_neighbor_two_way(self):
        with autotest.step("Arrange: fixture Cisco 'show ip ospf neighbor' output"):
            stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: neighbor 4.4.4.4 state is 2WAY/DROTHER"):
            assert_equal(
                _parse_cisco_neighbor(stdout, "4.4.4.4"),
                "2WAY/DROTHER",
                "parse cisco neighbor",
            )

    @autotest.num("3284")
    @autotest.external_id("340a90ab-3994-49ac-a00c-76dd0aced40d")
    @autotest.name("Cisco neighbor: returns None for an unknown neighbor")
    def test_340a90ab_parse_cisco_neighbor_missing(self):
        with autotest.step("Arrange: fixture Cisco 'show ip ospf neighbor' output"):
            stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")

        with autotest.step("Act+Assert: unknown neighbor 9.9.9.9 returns None"):
            assert_is_none(_parse_cisco_neighbor(stdout, "9.9.9.9"), "parse cisco neighbor")

    @autotest.num("3285")
    @autotest.external_id("8d937027-b2c8-4f89-82a2-74079d9a1483")
    @autotest.name("Cisco neighbor: returns None on empty output")
    def test_8d937027_parse_cisco_neighbor_empty_output(self):
        with autotest.step("Arrange: output with only the header, no neighbor rows"):
            empty = "R1#show ip ospf neighbor\nNeighbor ID     Pri   State\nR1#\n"

        with autotest.step("Act+Assert: returns None"):
            assert_is_none(_parse_cisco_neighbor(empty, "2.2.2.2"), "parse cisco neighbor")

    # ---------------- Cisco: route ----------------

    @autotest.num("3286")
    @autotest.external_id("61d4acbd-2c1b-4888-b37f-fb140b67e416")
    @autotest.name("Cisco route: matches the active OSPF route")
    def test_61d4acbd_parse_cisco_route_ospf_active(self):
        with autotest.step("Arrange: fixture Cisco 'show ip route ospf' output"):
            stdout = _load("cisco_show_ip_route_ospf.txt")

        with autotest.step("Act: _parse_cisco_route for 192.168.110.0/24"):
            parsed = _parse_cisco_route(stdout, "192.168.110.0/24")

        with autotest.step("Assert: matched as the active OSPF route"):
            assert_is_not_none(parsed, "parsed")
            code, line = parsed
            assert_equal(code, "O", "code")
            assert_in("via 10.0.0.2", line, "'via 10.0.0.2'")

    @autotest.num("3287")
    @autotest.external_id("d13f8af8-0888-45cf-a9f3-ea911e2906da")
    @autotest.name("Cisco route: matches a secondary OSPF route")
    def test_d13f8af8_parse_cisco_route_ospf_secondary(self):
        with autotest.step("Arrange: fixture Cisco 'show ip route ospf' output"):
            stdout = _load("cisco_show_ip_route_ospf.txt")

        with autotest.step("Act: _parse_cisco_route for 192.168.120.0/24"):
            parsed = _parse_cisco_route(stdout, "192.168.120.0/24")

        with autotest.step("Assert: matched as an OSPF route"):
            assert_is_not_none(parsed, "parsed")
            assert_equal(parsed[0], "O", "parsed[0]")

    @autotest.num("3288")
    @autotest.external_id("8b5d7fd0-0202-4657-8800-e16b7a2bf825")
    @autotest.name("Cisco route: returns None for an unmatched prefix")
    def test_8b5d7fd0_parse_cisco_route_missing(self):
        with autotest.step("Arrange: fixture Cisco 'show ip route ospf' output"):
            stdout = _load("cisco_show_ip_route_ospf.txt")

        with autotest.step("Act+Assert: an unmatched prefix returns None"):
            assert_is_none(
                _parse_cisco_route(stdout, "172.16.0.0/16"),
                "parse cisco route",
            )

    @autotest.num("3289")
    @autotest.external_id("b717f3fc-5fee-4b43-8b25-75c94ef55439")
    @autotest.name("Cisco route: does not mistake the Codes: header for a route")
    def test_b717f3fc_parse_cisco_route_skips_codes_header(self):
        # "Codes:" line contains the format `O - OSPF, IA - OSPF inter area`,
        # the parser must not mistake this for a route.
        with autotest.step("Arrange: fixture Cisco 'show ip route ospf' output"):
            stdout = _load("cisco_show_ip_route_ospf.txt")

        with autotest.step("Act+Assert: the Codes: header prefix does not match as a route"):
            assert_is_none(
                _parse_cisco_route(stdout, "10.0.0.0/30"),
                "parse cisco route",
            )

    # ---------------- Cisco: interface brief ----------------

    @autotest.num("3290")
    @autotest.external_id("93b67474-1f36-41eb-adb1-ce37b9474e5c")
    @autotest.name("Cisco interface: subinterface with an assigned IP, up/up")
    def test_93b67474_parse_cisco_interface_subinterface_with_ip(self):
        with autotest.step("Arrange: fixture Cisco 'show ip interface brief' output"):
            stdout = _load("cisco_show_ip_interface_brief.txt")

        with autotest.step("Act: _parse_cisco_interface for FastEthernet0/0.10"):
            parsed = _parse_cisco_interface(stdout, "FastEthernet0/0.10")

        with autotest.step("Assert: assigned ip, status and protocol both up"):
            assert_is_not_none(parsed, "parsed")
            assert_equal(parsed["ip"], "192.168.10.1", "ip")
            assert_equal(parsed["status"], "up", "status")
            assert_equal(parsed["protocol"], "up", "protocol")

    @autotest.num("3291")
    @autotest.external_id("2be0cee2-b3d6-469a-bc0e-57dab01da0e6")
    @autotest.name("Cisco interface: unassigned IP, status up")
    def test_2be0cee2_parse_cisco_interface_unassigned(self):
        with autotest.step("Arrange: fixture Cisco 'show ip interface brief' output"):
            stdout = _load("cisco_show_ip_interface_brief.txt")

        with autotest.step("Act: _parse_cisco_interface for FastEthernet0/0"):
            parsed = _parse_cisco_interface(stdout, "FastEthernet0/0")

        with autotest.step("Assert: unassigned ip, status up"):
            assert_is_not_none(parsed, "parsed")
            assert_equal(parsed["ip"], "unassigned", "ip")
            assert_equal(parsed["status"], "up", "status")

    @autotest.num("3292")
    @autotest.external_id("d55a3cb0-5830-4096-8ce6-bcab3a77229c")
    @autotest.name("Cisco interface: administratively down, protocol down")
    def test_d55a3cb0_parse_cisco_interface_admin_down(self):
        with autotest.step("Arrange: fixture Cisco 'show ip interface brief' output"):
            stdout = _load("cisco_show_ip_interface_brief.txt")

        with autotest.step("Act: _parse_cisco_interface for FastEthernet0/2"):
            parsed = _parse_cisco_interface(stdout, "FastEthernet0/2")

        with autotest.step("Assert: administratively down, protocol down"):
            assert_is_not_none(parsed, "parsed")
            assert_equal(parsed["status"], "administratively down", "status")
            assert_equal(parsed["protocol"], "down", "protocol")

    @autotest.num("3293")
    @autotest.external_id("47c1378a-6025-40db-b2a4-918be0b03b79")
    @autotest.name("Cisco interface: returns None for an unknown interface")
    def test_47c1378a_parse_cisco_interface_missing(self):
        with autotest.step("Arrange: fixture Cisco 'show ip interface brief' output"):
            stdout = _load("cisco_show_ip_interface_brief.txt")

        with autotest.step("Act+Assert: an unknown interface returns None"):
            assert_is_none(
                _parse_cisco_interface(stdout, "FastEthernet9/9"), "parse cisco interface"
            )
