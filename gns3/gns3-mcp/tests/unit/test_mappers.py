import pytest

from mcp_sdk.models import Component, ComponentDetail, SystemOverview
from src.mappers import (
    build_system_overview,
    link_to_component,
    link_to_component_detail,
    node_to_component,
    node_to_component_detail,
)
from mcp_sdk.testing import autotest
from tests.unit.conftest import build_gns3_link, build_gns3_node, build_gns3_version

pytestmark = [pytest.mark.unit, pytest.mark.mappers]


class TestNodeToComponent:
    @autotest.num("300")
    @autotest.external_id("gns3-mappers-node-to-component")
    @autotest.name("node_to_component: маппинг базовых полей")
    def test_basic(self):
        with autotest.step("Маппим GNS3 node → Component"):
            node = build_gns3_node()
            c = node_to_component(node)

        with autotest.step("Проверяем поля"):
            assert isinstance(c, Component)
            assert c.id == "node-1"
            assert c.name == "R1"
            assert c.type == "dynamips"
            assert c.status == "started"
            assert "R1" in c.summary

    @autotest.num("301")
    @autotest.external_id("gns3-mappers-node-to-component-stopped")
    @autotest.name("node_to_component: stopped статус")
    def test_stopped(self):
        with autotest.step("Маппим stopped node"):
            node = build_gns3_node(status="stopped")
            c = node_to_component(node)

        with autotest.step("Проверяем статус"):
            assert c.status == "stopped"
            assert "stopped" in c.summary


class TestNodeToComponentDetail:
    @autotest.num("302")
    @autotest.external_id("gns3-mappers-node-detail")
    @autotest.name("node_to_component_detail: properties и relationships")
    def test_detail(self):
        with autotest.step("Маппим node → ComponentDetail"):
            node = build_gns3_node()
            cd = node_to_component_detail(node, peer_node_ids=["node-2", "node-3"])

        with autotest.step("Проверяем поля"):
            assert isinstance(cd, ComponentDetail)
            assert cd.properties["console"] == 5000
            assert cd.properties["console_type"] == "telnet"
            assert cd.relationships == ["node-2", "node-3"]

    @autotest.num("303")
    @autotest.external_id("gns3-mappers-node-detail-no-peers")
    @autotest.name("node_to_component_detail: без peer_node_ids")
    def test_no_peers(self):
        with autotest.step("Маппим без peers"):
            cd = node_to_component_detail(build_gns3_node())

        with autotest.step("relationships пуст"):
            assert cd.relationships == []


class TestLinkToComponent:
    @autotest.num("304")
    @autotest.external_id("gns3-mappers-link-to-component")
    @autotest.name("link_to_component: имя из node_names")
    def test_basic(self):
        with autotest.step("Маппим link"):
            link = build_gns3_link()
            names = {"node-1": "R1", "node-2": "R2"}
            c = link_to_component(link, names)

        with autotest.step("Проверяем поля"):
            assert isinstance(c, Component)
            assert c.type == "link"
            assert "R1" in c.name
            assert "R2" in c.name
            assert c.status == "active"

    @autotest.num("305")
    @autotest.external_id("gns3-mappers-link-capturing")
    @autotest.name("link_to_component: capturing → status")
    def test_capturing(self):
        with autotest.step("Маппим capturing link"):
            link = build_gns3_link(capturing=True)
            c = link_to_component(link, {"node-1": "R1", "node-2": "R2"})

        with autotest.step("Проверяем статус"):
            assert c.status == "capturing"


class TestLinkToComponentDetail:
    @autotest.num("306")
    @autotest.external_id("gns3-mappers-link-detail")
    @autotest.name("link_to_component_detail: relationships содержит node_ids")
    def test_detail(self):
        with autotest.step("Маппим link → ComponentDetail"):
            link = build_gns3_link()
            cd = link_to_component_detail(link, {"node-1": "R1", "node-2": "R2"})

        with autotest.step("Проверяем relationships"):
            assert isinstance(cd, ComponentDetail)
            assert "node-1" in cd.relationships
            assert "node-2" in cd.relationships
            assert cd.properties["capturing"] is False


class TestBuildSystemOverview:
    @autotest.num("307")
    @autotest.external_id("gns3-mappers-system-overview")
    @autotest.name("build_system_overview: подсчёт компонентов")
    def test_overview(self):
        with autotest.step("Строим overview"):
            nodes = [build_gns3_node(), build_gns3_node(node_id="node-2", name="R2")]
            links = [build_gns3_link()]
            version = build_gns3_version()
            overview = build_system_overview(nodes, links, version, "test-project")

        with autotest.step("Проверяем подсчёты"):
            assert isinstance(overview, SystemOverview)
            assert overview.component_count == 3
            assert overview.components_by_type["dynamips"] == 2
            assert overview.components_by_type["link"] == 1
            assert overview.system_version == "3.0.0"
            assert "test-project" in overview.summary

    @autotest.num("308")
    @autotest.external_id("gns3-mappers-system-overview-empty")
    @autotest.name("build_system_overview: пустая топология")
    def test_empty(self):
        with autotest.step("Пустые nodes и links"):
            overview = build_system_overview([], [], build_gns3_version(), "empty")

        with autotest.step("Проверяем нули"):
            assert overview.component_count == 0
            assert overview.components_by_type == {"link": 0}
