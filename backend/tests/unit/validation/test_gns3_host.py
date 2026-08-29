from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from validation.checks.context import _gns3_host_from_settings

pytestmark = [pytest.mark.unit]


def _settings(node_host="", internal="http://gns3-server:3080", public="http://localhost:3080"):
    return SimpleNamespace(
        gns3=SimpleNamespace(node_host=node_host, internal_url=internal, public_url=public)
    )


class TestGns3Host:
    @autotest.num("3264")
    @autotest.external_id("7e072cf5-c310-46f3-bf26-ae6f22d399c9")
    @autotest.name(
        "_gns3_host_from_settings: skips the gns3-server hostname, falls back to public_url"
    )
    def test_7e072cf5_derives_host_from_internal_url(self):
        # internal_url hostname "gns3-server" is skipped → fall back to public_url
        with autotest.step("Act+Assert: derived host is the public_url hostname"):
            assert_equal(
                _gns3_host_from_settings(_settings()),
                "localhost",
                "gns3 host from settings",
            )

    @autotest.num("3265")
    @autotest.external_id("c08b0b0f-8c2d-4e18-8bf0-ca58bd1397e7")
    @autotest.name("_gns3_host_from_settings: derives host from public_url")
    def test_c08b0b0f_derives_host_from_public_url(self):
        # internal is skipped because of gns3-server, public gives the real host
        with autotest.step(
            "Arrange: settings with a gns3-server internal_url and a real public_url"
        ):
            settings = _settings(
                internal="http://gns3-server:3080", public="http://192.168.1.10:3080"
            )

        with autotest.step("Act+Assert: derived host is the public_url hostname"):
            assert_equal(
                _gns3_host_from_settings(settings), "192.168.1.10", "gns3 host from settings"
            )

    @autotest.num("3266")
    @autotest.external_id("e00471a2-ac1f-439f-b4b5-2c12066ff130")
    @autotest.name("_gns3_host_from_settings: an explicit node_host wins over derived urls")
    def test_e00471a2_explicit_node_host_wins(self):
        with autotest.step("Act+Assert: explicit node_host is returned as-is"):
            assert_equal(
                _gns3_host_from_settings(_settings(node_host="10.0.0.5")),
                "10.0.0.5",
                "gns3 host from settings",
            )

    @autotest.num("3267")
    @autotest.external_id("7ea4c054-7279-4144-ae92-ff99880a2c9a")
    @autotest.name("_gns3_host_from_settings: raises ValueError when no host is derivable")
    def test_7ea4c054_raises_when_nothing_derivable(self):
        with autotest.step("Act+Assert: no node_host, internal_url or public_url → ValueError"):
            with pytest.raises(ValueError):
                _gns3_host_from_settings(_settings(node_host="", internal="", public=""))
