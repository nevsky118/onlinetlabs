"""Unit tests for gns3_username_for, GNS3 user names must not collide.

Regression. The name was built as `student-{user_id[:8]}`. Two students sharing
an 8-character id prefix got ONE name, and orphan cleanup during the second
student's provisioning deleted the first student's GNS3 user in the middle of
their session → ACL failed with `FOREIGN KEY constraint failed` and the session
failed with a 500. Students were breaking each other's labs.
"""

from mcp_sdk.testing import autotest

from src.gns3_identity import gns3_username_for


class TestGns3UsernameFor:
    @autotest.num("3323")
    @autotest.external_id("1df13869-8dc0-422a-8649-b129bf2d93d5")
    @autotest.name("gns3_username_for: distinct ids sharing an 8-char prefix get distinct names")
    def test_1df13869_distinct_users_with_shared_prefix_get_distinct_names(self):
        """A shared 8-character id prefix no longer yields identical names."""
        with autotest.step("Act: build a name for the first id"):
            a = gns3_username_for("sim-12000-1")

        with autotest.step("Act: build a name for a second id sharing the same prefix"):
            b = gns3_username_for("sim-12000-2")

        with autotest.step("Act: build a name for a third id sharing the same prefix"):
            c = gns3_username_for("sim-12000-49")

        with autotest.step("Assert: all three names are distinct"):
            assert a != b != c
            assert len({a, b, c}) == 3, "names must differ despite a shared prefix"

    @autotest.num("3324")
    @autotest.external_id("08d3d5a7-6981-4487-8038-bbd62375501e")
    @autotest.name("gns3_username_for: is deterministic for the same id")
    def test_08d3d5a7_is_deterministic(self):
        """Same student → same name (otherwise cleanup of their stray accounts breaks)."""
        with autotest.step("Act + Assert: the same id yields the same name twice"):
            assert gns3_username_for("user-abc") == gns3_username_for("user-abc")

    @autotest.num("3325")
    @autotest.external_id("785aaaf0-558f-42dd-97f8-4c3ee2c95890")
    @autotest.name("gns3_username_for: the name is prefixed and length-bounded")
    def test_785aaaf0_name_is_prefixed_and_bounded(self):
        """The name is recognizable and stays within the GNS3 length limits."""
        with autotest.step("Act: build a name from a UUID student id"):
            name = gns3_username_for("0d1903e5-d38a-41ff-bcfb-03554cddba20")

        with autotest.step("Assert: the name is prefixed, bounded and alphanumeric"):
            assert name.startswith("student-")
            assert len(name) == len("student-") + 16
            assert name[len("student-") :].isalnum()

    @autotest.num("3326")
    @autotest.external_id("5bd75aa5-9431-4f32-a42a-847a5d9330c4")
    @autotest.name("gns3_username_for: 500 distinct ids do not collide")
    def test_5bd75aa5_uuid_users_do_not_collide(self):
        """Bulk check, 500 different ids → 500 different names."""
        with autotest.step("Act: build names for 500 distinct student ids"):
            names = {gns3_username_for(f"student-{i}-0d1903e5") for i in range(500)}

        with autotest.step("Assert: all 500 names are distinct"):
            assert len(names) == 500
