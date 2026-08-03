import pytest
from mcp_sdk.models import Component, ComponentDetail, SystemOverview
from mcp_sdk.testing import autotest

from src.mappers import (
    build_system_overview,
    link_to_component,
    link_to_component_detail,
    node_to_component,
    node_to_component_detail,
)
from tests.unit.conftest import build_gns3_link, build_gns3_node, build_gns3_version

pytestmark = [pytest.mark.unit, pytest.mark.mappers]


class TestNodeToComponent:
    @autotest.num("300")
    @autotest.external_id("gns3-mappers-node-to-component")
    @autotest.name("node_to_component: maps the basic fields")
    def test_gns3mapp_basic(self):
        with autotest.step("Map GNS3 node → Component"):
            node = build_gns3_node()
            c = node_to_component(node)

        with autotest.step("Assert the fields"):
            assert isinstance(c, Component)
            assert c.id == "node-1"
            assert c.name == "R1"
            assert c.type == "dynamips"
            assert c.status == "started"
            assert "R1" in c.summary

    @autotest.num("301")
    @autotest.external_id("gns3-mappers-node-to-component-stopped")
    @autotest.name("node_to_component: stopped status")
    def test_gns3mapp_stopped(self):
        with autotest.step("Map a stopped node"):
            node = build_gns3_node(status="stopped")
            c = node_to_component(node)

        with autotest.step("Assert the status"):
            assert c.status == "stopped"
            assert "stopped" in c.summary


class TestNodeToComponentDetail:
    @autotest.num("302")
    @autotest.external_id("gns3-mappers-node-detail")
    @autotest.name("node_to_component_detail: properties and relationships")
    def test_gns3mapp_detail(self):
        with autotest.step("Map node → ComponentDetail"):
            node = build_gns3_node()
            cd = node_to_component_detail(node, peer_node_ids=["node-2", "node-3"])

        with autotest.step("Assert the fields"):
            assert isinstance(cd, ComponentDetail)
            assert cd.properties["console"] == 5000
            assert cd.properties["console_type"] == "telnet"
            assert cd.relationships == ["node-2", "node-3"]

    @autotest.num("303")
    @autotest.external_id("gns3-mappers-node-detail-no-peers")
    @autotest.name("node_to_component_detail: no peer_node_ids")
    def test_gns3mapp_no_peers(self):
        with autotest.step("Map with no peers"):
            cd = node_to_component_detail(build_gns3_node())

        with autotest.step("relationships is empty"):
            assert cd.relationships == []


class TestLinkToComponent:
    @autotest.num("304")
    @autotest.external_id("gns3-mappers-link-to-component")
    @autotest.name("link_to_component: name built from node_names")
    def test_gns3mapp_basic(self):
        with autotest.step("Map the link"):
            link = build_gns3_link()
            names = {"node-1": "R1", "node-2": "R2"}
            c = link_to_component(link, names)

        with autotest.step("Assert the fields"):
            assert isinstance(c, Component)
            assert c.type == "link"
            assert "R1" in c.name
            assert "R2" in c.name
            assert c.status == "active"

    @autotest.num("305")
    @autotest.external_id("gns3-mappers-link-capturing")
    @autotest.name("link_to_component: capturing → status")
    def test_gns3mapp_capturing(self):
        with autotest.step("Map a capturing link"):
            link = build_gns3_link(capturing=True)
            c = link_to_component(link, {"node-1": "R1", "node-2": "R2"})

        with autotest.step("Assert the status"):
            assert c.status == "capturing"


class TestLinkToComponentDetail:
    @autotest.num("306")
    @autotest.external_id("gns3-mappers-link-detail")
    @autotest.name("link_to_component_detail: relationships contains node_ids")
    def test_gns3mapp_detail(self):
        with autotest.step("Map link → ComponentDetail"):
            link = build_gns3_link()
            cd = link_to_component_detail(link, {"node-1": "R1", "node-2": "R2"})

        with autotest.step("Assert relationships"):
            assert isinstance(cd, ComponentDetail)
            assert "node-1" in cd.relationships
            assert "node-2" in cd.relationships
            assert cd.properties["capturing"] is False


class TestBuildSystemOverview:
    @autotest.num("307")
    @autotest.external_id("gns3-mappers-system-overview")
    @autotest.name("build_system_overview: component counts")
    def test_gns3mapp_overview(self):
        with autotest.step("Build the overview"):
            nodes = [build_gns3_node(), build_gns3_node(node_id="node-2", name="R2")]
            links = [build_gns3_link()]
            version = build_gns3_version()
            overview = build_system_overview(nodes, links, version, "test-project")

        with autotest.step("Assert the counts"):
            assert isinstance(overview, SystemOverview)
            assert overview.component_count == 3
            assert overview.components_by_type["dynamips"] == 2
            assert overview.components_by_type["link"] == 1
            assert overview.system_version == "3.0.0"
            assert "test-project" in overview.summary

    @autotest.num("308")
    @autotest.external_id("gns3-mappers-system-overview-empty")
    @autotest.name("build_system_overview: empty topology")
    def test_gns3mapp_empty(self):
        with autotest.step("Empty nodes and links"):
            overview = build_system_overview([], [], build_gns3_version(), "empty")

        with autotest.step("Assert the zeros"):
            assert overview.component_count == 0
            assert overview.components_by_type == {"link": 0}
