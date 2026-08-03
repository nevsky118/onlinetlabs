from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest

from validation.service import _gns3_host_from_settings

pytestmark = [pytest.mark.unit]


def _settings(node_host="", internal="http://gns3-server:3080", public="http://localhost:3080"):
    return SimpleNamespace(
        gns3=SimpleNamespace(node_host=node_host, internal_url=internal, public_url=public)
    )


@autotest.num("3264")
@autotest.external_id("7e072cf5-c310-46f3-bf26-ae6f22d399c9")
@autotest.name("_gns3_host_from_settings: skips the gns3-server hostname, falls back to public_url")
def test_7e072cf5_derives_host_from_internal_url():
    # internal_url hostname "gns3-server" is skipped → fall back to public_url
    assert _gns3_host_from_settings(_settings()) == "localhost"


@autotest.num("3265")
@autotest.external_id("c08b0b0f-8c2d-4e18-8bf0-ca58bd1397e7")
@autotest.name("_gns3_host_from_settings: derives host from public_url")
def test_c08b0b0f_derives_host_from_public_url():
    # internal is skipped because of gns3-server, public gives the real host
    s = _settings(internal="http://gns3-server:3080", public="http://192.168.1.10:3080")
    assert _gns3_host_from_settings(s) == "192.168.1.10"


@autotest.num("3266")
@autotest.external_id("e00471a2-ac1f-439f-b4b5-2c12066ff130")
@autotest.name("_gns3_host_from_settings: an explicit node_host wins over derived urls")
def test_e00471a2_explicit_node_host_wins():
    assert _gns3_host_from_settings(_settings(node_host="10.0.0.5")) == "10.0.0.5"


@autotest.num("3267")
@autotest.external_id("7ea4c054-7279-4144-ae92-ff99880a2c9a")
@autotest.name("_gns3_host_from_settings: raises ValueError when no host is derivable")
def test_7ea4c054_raises_when_nothing_derivable():
    with pytest.raises(ValueError):
        _gns3_host_from_settings(_settings(node_host="", internal="", public=""))
