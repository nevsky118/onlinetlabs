# Tests for GNS3 JSON → SDK model mappers.

import pytest

from onlinetlabs_mcp_sdk.models import Component, ComponentDetail, SystemOverview
from src.mappers import (
    build_system_overview,
    link_to_component,
    link_to_component_detail,
    node_to_component,
    node_to_component_detail,
)
from tests.helpers.factories import build_gns3_link, build_gns3_node, build_gns3_version
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.mappers]


class TestNodeMappers:
    @autotests.num("330")
    @autotests.external_id("ac330001-0000-0000-0000-000000000001")
    @autotests.name("node_to_component: fields map correctly")
    def test_node_to_component(self):
        """node_to_component maps GNS3 node JSON to Component."""

        # Arrange
        with autotests.step("Build GNS3 node"):
            node = build_gns3_node(node_id="n1", name="R1", node_type="router", status="started")

        # Act
        with autotests.step("Map node to Component"):
            result = node_to_component(node)

        # Assert
        with autotests.step("Check all fields"):
            assert isinstance(result, Component)
            assert result.id == "n1"
            assert result.name == "R1"
            assert result.type == "router"
            assert result.status == "started"
            assert result.summary == "router R1 (started)"

    @autotests.num("331")
    @autotests.external_id("ac331001-0000-0000-0000-000000000002")
    @autotests.name("node_to_component_detail: properties and relationships")
    def test_node_to_component_detail(self):
        """node_to_component_detail includes properties and peer relationships."""

        # Arrange
        with autotests.step("Build GNS3 node"):
            node = build_gns3_node(console=5001, console_type="vnc")

        # Act
        with autotests.step("Map node to ComponentDetail with peers"):
            result = node_to_component_detail(node, peer_node_ids=["peer-1", "peer-2"])

        # Assert
        with autotests.step("Check properties and relationships"):
            assert isinstance(result, ComponentDetail)
            assert result.properties["console"] == 5001
            assert result.properties["console_type"] == "vnc"
            assert result.properties["compute_id"] == "local"
            assert isinstance(result.properties["ports"], list)
            assert result.configuration is None
            assert result.relationships == ["peer-1", "peer-2"]


class TestLinkMappers:
    @autotests.num("332")
    @autotests.external_id("ac332001-0000-0000-0000-000000000003")
    @autotests.name("link_to_component: name includes both node names")
    def test_link_to_component(self):
        """link_to_component builds human-readable name with node names."""

        # Arrange
        with autotests.step("Build link and node_names map"):
            link = build_gns3_link()
            node_names = {"node-1": "PC1", "node-2": "SW1"}

        # Act
        with autotests.step("Map link to Component"):
            result = link_to_component(link, node_names)

        # Assert
        with autotests.step("Check name, type and status"):
            assert isinstance(result, Component)
            assert "PC1" in result.name
            assert "SW1" in result.name
            assert "<->" in result.name
            assert result.type == "link"
            assert result.status == "active"
            assert "PC1" in result.summary
            assert "SW1" in result.summary

    @autotests.num("333")
    @autotests.external_id("ac333001-0000-0000-0000-000000000004")
    @autotests.name("link_to_component: capturing=True → status='capturing'")
    def test_link_to_component_capturing(self):
        """Link with capturing=True gets status='capturing'."""

        # Arrange
        with autotests.step("Build capturing link"):
            link = build_gns3_link(capturing=True)
            node_names = {"node-1": "PC1", "node-2": "SW1"}

        # Act
        with autotests.step("Map link to Component"):
            result = link_to_component(link, node_names)

        # Assert
        with autotests.step("Check status is capturing"):
            assert result.status == "capturing"

    @autotests.num("334")
    @autotests.external_id("ac334001-0000-0000-0000-000000000005")
    @autotests.name("link_to_component_detail: properties and relationships")
    def test_link_to_component_detail(self):
        """link_to_component_detail includes nodes, filters, relationships."""

        # Arrange
        with autotests.step("Build link"):
            link = build_gns3_link(filters={"freq_drop": [50]})
            node_names = {"node-1": "PC1", "node-2": "SW1"}

        # Act
        with autotests.step("Map link to ComponentDetail"):
            result = link_to_component_detail(link, node_names)

        # Assert
        with autotests.step("Check properties and relationships"):
            assert isinstance(result, ComponentDetail)
            assert result.properties["nodes"] == link["nodes"]
            assert result.properties["filters"] == {"freq_drop": [50]}
            assert result.properties["link_type"] == "ethernet"
            assert result.properties["capturing"] is False
            assert result.relationships == ["node-1", "node-2"]


class TestSystemOverview:
    @autotests.num("335")
    @autotests.external_id("ac335001-0000-0000-0000-000000000006")
    @autotests.name("build_system_overview: counts, version, summary")
    def test_build_system_overview(self):
        """build_system_overview aggregates nodes and links."""

        # Arrange
        with autotests.step("Build nodes, links, version"):
            nodes = [
                build_gns3_node(node_id="n1", node_type="vpcs", status="started"),
                build_gns3_node(node_id="n2", node_type="router", status="stopped"),
            ]
            links = [build_gns3_link()]
            version = build_gns3_version(version="3.1.0")

        # Act
        with autotests.step("Build overview"):
            result = build_system_overview(nodes, links, version, "Lab1")

        # Assert
        with autotests.step("Check overview fields"):
            assert isinstance(result, SystemOverview)
            assert result.system_name == "GNS3"
            assert result.system_version == "3.1.0"
            assert result.component_count == 3
            assert result.components_by_type["vpcs"] == 1
            assert result.components_by_type["router"] == 1
            assert result.components_by_type["link"] == 1
            assert result.components_by_status["started"] == 1
            assert result.components_by_status["stopped"] == 1
            assert result.components_by_status["active"] == 1
            assert "Lab1" in result.summary
            assert "2 nodes" in result.summary
            assert "1 links" in result.summary

    @autotests.num("336")
    @autotests.external_id("ac336001-0000-0000-0000-000000000007")
    @autotests.name("build_system_overview: empty — 0 nodes, 0 links")
    def test_build_system_overview_empty(self):
        """build_system_overview with no nodes and no links."""

        # Arrange
        with autotests.step("Empty inputs"):
            version = build_gns3_version()

        # Act
        with autotests.step("Build overview"):
            result = build_system_overview([], [], version, "EmptyLab")

        # Assert
        with autotests.step("Check zero counts"):
            assert result.component_count == 0
            assert result.components_by_type == {"link": 0}
            assert result.components_by_status == {}
            assert "0 nodes" in result.summary
            assert "0 links" in result.summary


class TestEdgeCases:
    @autotests.num("337")
    @autotests.external_id("ac337001-0000-0000-0000-000000000008")
    @autotests.name("node_to_component_detail: no peers → empty relationships")
    def test_node_to_component_detail_no_peers(self):
        """peer_node_ids=None results in empty relationships list."""

        # Arrange
        with autotests.step("Build node"):
            node = build_gns3_node()

        # Act
        with autotests.step("Map without peer_node_ids"):
            result = node_to_component_detail(node, peer_node_ids=None)

        # Assert
        with autotests.step("Check empty relationships"):
            assert result.relationships == []
