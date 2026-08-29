"""Unit tests for the single definition of lab launchability."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_false, assert_in, assert_true

from labs.readiness import audit_labs, is_launchable, launch_blocker, template_column_for
from tests.settings.data.labs_data import LabData, LabSetData

pytestmark = [pytest.mark.unit]


class TestLaunchBlocker:
    """launch_blocker is the one answer launch, the admin view and the audit all use."""

    @autotest.num("3385")
    @autotest.external_id("dfbbc637-003c-4739-84ba-8938ea0523aa")
    @autotest.name("readiness: a gns3 lab without a template id cannot launch")
    def test_dfbbc637_gns3_lab_without_template_is_blocked(self):
        with autotest.step("Arrange: a gns3 lab with no template id"):
            lab = LabData("dhcp-basics").lab

        with autotest.step("Assert: blocked with the default template code"):
            assert_equal(launch_blocker(lab), "error.lab.no_template_project", "blocker code")
            assert_false(is_launchable(lab), "lab is not launchable")

    @autotest.num("3386")
    @autotest.external_id("7b6e0f53-b750-41b2-973e-62915d0aaea7")
    @autotest.name("readiness: a non-gns3 lab needs no template")
    def test_7b6e0f53_non_gns3_lab_needs_no_template(self):
        with autotest.step("Arrange: a lab that needs no environment"):
            lab = LabData("theory-only", environment_type="none").lab

        with autotest.step("Assert: nothing blocks it"):
            assert_true(launch_blocker(lab) is None, "no blocker")
            assert_true(is_launchable(lab), "lab is launchable")

    @autotest.num("3388")
    @autotest.external_id("f2007836-4fec-4cbe-9b2e-768cb9bdaf4f")
    @autotest.name("readiness: a -frr lab with only the default column set is still blocked")
    def test_f2007836_frr_lab_ignores_the_default_column(self):
        with autotest.step("Arrange: a -frr lab whose default column is populated"):
            lab = LabData("routing-frr", gns3_template_project_id="not-the-frr-one").lab

        with autotest.step("Assert: blocked, so the admin view cannot call it ready"):
            assert_equal(launch_blocker(lab), "error.lab.no_template", "blocker code")
            assert_false(is_launchable(lab), "lab is not launchable")


class TestTemplateColumn:
    """The slug suffix decides which template column a lab launches from."""

    @autotest.num("3387")
    @autotest.external_id("9c185aa4-46b3-46d2-9abd-34050293c896")
    @autotest.name("readiness: slug suffix selects the template column")
    def test_9c185aa4_suffix_selects_template_column(self):
        with autotest.step("Arrange: one lab per suffix convention"):
            ccna = LabData("x-ccna").lab
            frr = LabData("x-frr").lab
            plain = LabData("x").lab

        with autotest.step("Assert: each suffix maps to its own column"):
            assert_equal(
                template_column_for(ccna)[0], "gns3_template_project_id_iosvl2", "ccna column"
            )
            assert_equal(template_column_for(frr)[0], "gns3_template_project_id_frr", "frr column")
            assert_equal(
                template_column_for(plain)[0], "gns3_template_project_id", "default column"
            )


class TestAuditLabs:
    """The audit reports every misconfiguration at once, not the first one."""

    @autotest.num("3389")
    @autotest.external_id("5bf1533a-f276-4c70-8453-05b7194c7844")
    @autotest.name("readiness: audit reports unlaunchable enabled labs and orphan specs")
    def test_5bf1533a_audit_reports_every_problem(self):
        with autotest.step("Arrange: one broken enabled lab, one healthy lab, one orphan spec"):
            data = LabSetData()

        with autotest.step("Act: audit the labs against the specs on disk"):
            problems = audit_labs(data.labs, data.spec_slugs)

        with autotest.step("Assert: both problems are reported, the healthy lab is not"):
            kinds = {(problemroblem_2.slug, problemroblem_2.kind) for problemroblem_2 in problems}
            assert_in(
                (data.broken.slug, "enabled_but_unlaunchable"), kinds, "unlaunchable lab reported"
            )
            assert_in((data.orphan_spec_slug, "spec_orphan"), kinds, "orphan spec reported")
            assert_false(
                any(problemroblem_2.slug == data.healthy.slug for problemroblem_2 in problems),
                "healthy lab is not reported",
            )
