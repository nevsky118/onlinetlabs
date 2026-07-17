"""Unit-тесты на subnet-membership и парсинг `show ip` для vpcs.ip_in_subnet."""

from pathlib import Path

import pytest

from validation.checks.vpcs import _ip_in_subnet, _parse_show_ip

_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


# ---------------- VPCS: parse show ip ----------------


def test_parse_show_ip_reads_ip_and_gateway():
    text = _load("vpcs_show_ip.txt")
    parsed = _parse_show_ip(text)
    assert parsed["ip"] == "192.168.10.10/24"
    assert parsed["gateway"] == "192.168.10.1"


def test_parse_show_ip_garbage():
    parsed = _parse_show_ip("random unrelated text")
    assert parsed == {"ip": "", "gateway": ""}


# ---------------- VPCS: ip_in_subnet membership ----------------


@pytest.mark.parametrize(
    ("ip_with_mask", "subnet", "ok"),
    [
        ("192.168.10.10/24", "192.168.10.0/24", True),
        ("192.168.10.10", "192.168.10.0/24", True),
        ("192.168.10.10/24", "192.168.11.0/24", False),
        ("192.168.10.20/24", "192.168.10.0/28", False),
        ("10.0.0.5/8", "10.0.0.0/8", True),
        ("192.168.10.10/24", "192.168.10.10/32", True),
        ("", "192.168.10.0/24", False),
        ("not-an-ip/24", "192.168.10.0/24", False),
        ("192.168.10.10/24", "garbage", False),
    ],
)
def test_ip_in_subnet(ip_with_mask, subnet, ok):
    assert _ip_in_subnet(ip_with_mask, subnet) is ok
