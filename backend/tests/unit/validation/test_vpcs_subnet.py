"""Unit tests for subnet membership and `show ip` parsing for vpcs.ip_in_subnet."""

from pathlib import Path

import pytest
from mcp_sdk.testing import autotest

from validation.checks.vpcs import _ip_in_subnet, _parse_show_ip

_FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


# ---------------- VPCS: parse show ip ----------------


@autotest.num("3294")
@autotest.external_id("beafd3af-dc2f-42b2-a956-46b3903d9631")
@autotest.name("VPCS _parse_show_ip: reads ip and gateway from show ip output")
def test_beafd3af_parse_show_ip_reads_ip_and_gateway():
    text = _load("vpcs_show_ip.txt")
    parsed = _parse_show_ip(text)
    assert parsed["ip"] == "192.168.10.10/24"
    assert parsed["gateway"] == "192.168.10.1"


@autotest.num("3295")
@autotest.external_id("370bc14b-745e-4a8e-b7bb-32234eccb109")
@autotest.name("VPCS _parse_show_ip: garbage input returns empty ip and gateway")
def test_370bc14b_parse_show_ip_garbage():
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
@autotest.num("3296")
@autotest.external_id("008caad4-1b1c-44b2-9352-8f82b8dc497b")
@autotest.name("VPCS _ip_in_subnet: membership matrix across masks and malformed input")
def test_008caad4_ip_in_subnet(ip_with_mask, subnet, ok):
    assert _ip_in_subnet(ip_with_mask, subnet) is ok
