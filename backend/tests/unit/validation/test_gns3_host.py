from types import SimpleNamespace

import pytest

from validation.service import _gns3_host_from_settings

pytestmark = [pytest.mark.unit]


def _settings(node_host="", internal="http://gns3-server:3080", public="http://localhost:3080"):
    return SimpleNamespace(
        gns3=SimpleNamespace(node_host=node_host, internal_url=internal, public_url=public)
    )


def test_derives_host_from_internal_url():
    # internal_url hostname "gns3-server" is skipped → fall back to public_url
    assert _gns3_host_from_settings(_settings()) == "localhost"


def test_derives_host_from_public_url():
    # internal is skipped because of gns3-server, public gives the real host
    s = _settings(internal="http://gns3-server:3080", public="http://192.168.1.10:3080")
    assert _gns3_host_from_settings(s) == "192.168.1.10"


def test_explicit_node_host_wins():
    assert _gns3_host_from_settings(_settings(node_host="10.0.0.5")) == "10.0.0.5"


def test_raises_when_nothing_derivable():
    with pytest.raises(ValueError):
        _gns3_host_from_settings(_settings(node_host="", internal="", public=""))
