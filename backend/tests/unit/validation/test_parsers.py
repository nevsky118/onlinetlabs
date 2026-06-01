"""Unit-тесты на чистые парсеры check-handlers."""

from pathlib import Path

import pytest

from validation.checks.cisco import (
    _parse_cisco_interface,
    _parse_cisco_neighbor,
    _parse_cisco_route,
)
from validation.checks.frr import _parse_neighbor_state, _parse_route
from validation.checks.vpcs import _matches, _parse_ping


_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


# ---------------- FRR: ospf neighbor ----------------


def test_parse_neighbor_state_full_dr():
    stdout = _load("show_ip_ospf_neighbor_full.txt")
    assert _parse_neighbor_state(stdout, "2.2.2.2") == "Full/DR"


def test_parse_neighbor_state_full_backup():
    stdout = _load("show_ip_ospf_neighbor_full.txt")
    assert _parse_neighbor_state(stdout, "3.3.3.3") == "Full/Backup"


def test_parse_neighbor_state_two_way():
    stdout = _load("show_ip_ospf_neighbor_full.txt")
    assert _parse_neighbor_state(stdout, "4.4.4.4") == "2-Way/DROther"


def test_parse_neighbor_state_missing():
    stdout = _load("show_ip_ospf_neighbor_full.txt")
    assert _parse_neighbor_state(stdout, "9.9.9.9") is None


def test_parse_neighbor_state_empty_output():
    empty = "\nNeighbor ID     Pri State           Up Time         ...\n\n"
    assert _parse_neighbor_state(empty, "2.2.2.2") is None


# ---------------- FRR: route ----------------


def test_parse_route_ospf_active():
    stdout = _load("show_ip_route_ospf.txt")
    parsed = _parse_route(stdout, "192.168.110.0/24")
    assert parsed is not None
    code, line = parsed
    assert code == "O>*"
    assert "via 10.0.12.2" in line


def test_parse_route_ospf_secondary():
    stdout = _load("show_ip_route_ospf.txt")
    parsed = _parse_route(stdout, "192.168.120.0/24")
    assert parsed is not None
    assert parsed[0] == "O>*"


def test_parse_route_connected():
    stdout = _load("show_ip_route_ospf.txt")
    parsed = _parse_route(stdout, "10.0.12.0/24")
    assert parsed is not None
    # `O` без `>*` — это конкурирующий маршрут, всё равно матчится.
    assert parsed[0] == "O"


def test_parse_route_missing():
    stdout = _load("show_ip_route_ospf.txt")
    assert _parse_route(stdout, "172.16.0.0/16") is None


# ---------------- VPCS: ping ----------------


def test_parse_ping_success_5_packets():
    text = _load("vpcs_ping_success.txt")
    parsed = _parse_ping(text)
    assert parsed["received"] == 5
    assert parsed["ttl"] == 62


def test_parse_ping_failure_no_replies():
    text = _load("vpcs_ping_failure.txt")
    parsed = _parse_ping(text)
    assert parsed["received"] == 0
    assert parsed["ttl"] is None


def test_parse_ping_handles_garbage():
    text = "random unrelated text"
    parsed = _parse_ping(text)
    assert parsed == {"received": 0, "ttl": None}


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
def test_matches(actual, expected, ok):
    assert _matches(actual, expected) is ok


# ---------------- Cisco: ospf neighbor ----------------


def test_parse_cisco_neighbor_full_bdr():
    stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")
    assert _parse_cisco_neighbor(stdout, "2.2.2.2") == "FULL/BDR"


def test_parse_cisco_neighbor_full_dr():
    stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")
    assert _parse_cisco_neighbor(stdout, "3.3.3.3") == "FULL/DR"


def test_parse_cisco_neighbor_two_way():
    stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")
    assert _parse_cisco_neighbor(stdout, "4.4.4.4") == "2WAY/DROTHER"


def test_parse_cisco_neighbor_missing():
    stdout = _load("cisco_show_ip_ospf_neighbor_full.txt")
    assert _parse_cisco_neighbor(stdout, "9.9.9.9") is None


def test_parse_cisco_neighbor_empty_output():
    empty = "R1#show ip ospf neighbor\nNeighbor ID     Pri   State\nR1#\n"
    assert _parse_cisco_neighbor(empty, "2.2.2.2") is None


# ---------------- Cisco: route ----------------


def test_parse_cisco_route_ospf_active():
    stdout = _load("cisco_show_ip_route_ospf.txt")
    parsed = _parse_cisco_route(stdout, "192.168.110.0/24")
    assert parsed is not None
    code, line = parsed
    assert code == "O"
    assert "via 10.0.0.2" in line


def test_parse_cisco_route_ospf_secondary():
    stdout = _load("cisco_show_ip_route_ospf.txt")
    parsed = _parse_cisco_route(stdout, "192.168.120.0/24")
    assert parsed is not None
    assert parsed[0] == "O"


def test_parse_cisco_route_missing():
    stdout = _load("cisco_show_ip_route_ospf.txt")
    assert _parse_cisco_route(stdout, "172.16.0.0/16") is None


def test_parse_cisco_route_skips_codes_header():
    # "Codes:" line содержит формат `O - OSPF, IA - OSPF inter area` —
    # парсер не должен принять это за маршрут.
    stdout = _load("cisco_show_ip_route_ospf.txt")
    assert _parse_cisco_route(stdout, "10.0.0.0/30") is None


# ---------------- Cisco: interface brief ----------------


def test_parse_cisco_interface_subinterface_with_ip():
    stdout = _load("cisco_show_ip_interface_brief.txt")
    parsed = _parse_cisco_interface(stdout, "FastEthernet0/0.10")
    assert parsed is not None
    assert parsed["ip"] == "192.168.10.1"
    assert parsed["status"] == "up"
    assert parsed["protocol"] == "up"


def test_parse_cisco_interface_unassigned():
    stdout = _load("cisco_show_ip_interface_brief.txt")
    parsed = _parse_cisco_interface(stdout, "FastEthernet0/0")
    assert parsed is not None
    assert parsed["ip"] == "unassigned"
    assert parsed["status"] == "up"


def test_parse_cisco_interface_admin_down():
    stdout = _load("cisco_show_ip_interface_brief.txt")
    parsed = _parse_cisco_interface(stdout, "FastEthernet0/2")
    assert parsed is not None
    assert parsed["status"] == "administratively down"
    assert parsed["protocol"] == "down"


def test_parse_cisco_interface_missing():
    stdout = _load("cisco_show_ip_interface_brief.txt")
    assert _parse_cisco_interface(stdout, "FastEthernet9/9") is None
