import pytest
from mcp_sdk.models import Component, ComponentDetail, SystemOverview
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_in,
    assert_is_instance,
    assert_true,
)

from src.mappers import (
    build_system_overview,
    link_to_component,
    link_to_component_detail,
    node_to_component,
    node_to_component_detail,
)
from tests.settings.data.gns3_data import Gns3LinkData, Gns3NodeData, Gns3VersionData

pytestmark = [pytest.mark.unit, pytest.mark.mappers]


class TestNodeToComponent:
    @autotest.num("3473")
    @autotest.external_id("721bda40-7007-4319-a34a-04e84b5d6d24")
    @autotest.name("node_to_component: maps the basic fields")
    def test_721bda40_basic(self):
        with autotest.step("Map GNS3 node → Component"):
            node = Gns3NodeData().data
            component = node_to_component(node)

        with autotest.step("Assert the fields"):
            assert_is_instance(component, Component, "a component")
            assert_equal(component.id, "node-1", "id")
            assert_equal(component.name, "R1", "name")
            assert_equal(component.type, "dynamips", "type")
            assert_equal(component.status, "started", "status")
            assert_in("R1", component.summary, "'R1'")

    @autotest.num("3474")
    @autotest.external_id("5a00eaa8-6454-48c6-bb8c-e405e0282017")
    @autotest.name("node_to_component: stopped status")
    def test_5a00eaa8_stopped(self):
        with autotest.step("Map a stopped node"):
            node = Gns3NodeData(status="stopped").data
            component = node_to_component(node)

        with autotest.step("Assert the status"):
            assert_equal(component.status, "stopped", "status")
            assert_in("stopped", component.summary, "'stopped'")


class TestNodeToComponentDetail:
    @autotest.num("3475")
    @autotest.external_id("3188f955-79b3-44d7-8b67-c7d7c58ca3da")
    @autotest.name("node_to_component_detail: properties and relationships")
    def test_3188f955_detail(self):
        with autotest.step("Map node → ComponentDetail"):
            node = Gns3NodeData().data
            cd = node_to_component_detail(node, peer_node_ids=["node-2", "node-3"])

        with autotest.step("Assert the fields"):
            assert_true(isinstance(cd, ComponentDetail), "isinstance")
            assert_equal(cd.properties["console"], 5000, "console")
            assert_equal(cd.properties["console_type"], "telnet", "console type")
            assert_equal(cd.relationships, ["node-2", "node-3"], "relationships")

    @autotest.num("3476")
    @autotest.external_id("335beb39-3f46-41e7-938e-ad7bdb2b3d88")
    @autotest.name("node_to_component_detail: no peer_node_ids")
    def test_335beb39_no_peers(self):
        with autotest.step("Map with no peers"):
            cd = node_to_component_detail(Gns3NodeData().data)

        with autotest.step("relationships is empty"):
            assert_equal(cd.relationships, [], "relationships")


class TestLinkToComponent:
    @autotest.num("3477")
    @autotest.external_id("1f1c9363-5f56-457b-bf02-866bac998f4d")
    @autotest.name("link_to_component: name built from node_names")
    def test_1f1c9363_basic(self):
        with autotest.step("Map the link"):
            link = Gns3LinkData().data
            names = {"node-1": "R1", "node-2": "R2"}
            component = link_to_component(link, names)

        with autotest.step("Assert the fields"):
            assert_is_instance(component, Component, "a component")
            assert_equal(component.type, "link", "type")
            assert_in("R1", component.name, "first node name")
            assert_in("R2", component.name, "second node name")
            assert_equal(component.status, "active", "status")

    @autotest.num("305")
    @autotest.external_id("57d7b90c-0d57-4773-8808-969d9145a757")
    @autotest.name("link_to_component: capturing → status")
    def test_57d7b90c_capturing(self):
        with autotest.step("Map a capturing link"):
            link = Gns3LinkData(capturing=True).data
            component = link_to_component(link, {"node-1": "R1", "node-2": "R2"})

        with autotest.step("Assert the status"):
            assert_equal(component.status, "capturing", "status")


class TestLinkToComponentDetail:
    @autotest.num("306")
    @autotest.external_id("df4939fb-74cf-4460-be92-e0dc9ffedd34")
    @autotest.name("link_to_component_detail: relationships contains node_ids")
    def test_df4939fb_detail(self):
        with autotest.step("Map link → ComponentDetail"):
            link = Gns3LinkData().data
            cd = link_to_component_detail(link, {"node-1": "R1", "node-2": "R2"})

        with autotest.step("Assert relationships"):
            assert_true(isinstance(cd, ComponentDetail), "isinstance")
            assert_in("node-1", cd.relationships, "'node-1'")
            assert_in("node-2", cd.relationships, "'node-2'")
            assert_equal(cd.properties["capturing"], False, "capturing")


class TestBuildSystemOverview:
    @autotest.num("307")
    @autotest.external_id("b271c879-2053-4745-aada-168c5cb2d5d1")
    @autotest.name("build_system_overview: component counts")
    def test_b271c879_overview(self):
        with autotest.step("Build the overview"):
            nodes = [Gns3NodeData().data, Gns3NodeData(node_id="node-2", name="R2").data]
            links = [Gns3LinkData().data]
            version = Gns3VersionData().data
            overview = build_system_overview(nodes, links, version, "test-project")

        with autotest.step("Assert the counts"):
            assert_true(isinstance(overview, SystemOverview), "isinstance")
            assert_equal(overview.component_count, 3, "component count")
            assert_equal(overview.components_by_type["dynamips"], 2, "dynamips")
            assert_equal(overview.components_by_type["link"], 1, "link")
            assert_equal(overview.system_version, "3.0.0", "system version")
            assert_in("test-project", overview.summary, "'test-project'")

    @autotest.num("308")
    @autotest.external_id("5d178f04-2f28-4277-83da-76504007b376")
    @autotest.name("build_system_overview: empty topology")
    def test_5d178f04_empty(self):
        with autotest.step("Empty nodes and links"):
            overview = build_system_overview([], [], Gns3VersionData().data, "empty")

        with autotest.step("Assert the zeros"):
            assert_equal(overview.component_count, 0, "component count")
            assert_equal(overview.components_by_type, {"link": 0}, "components by type")
