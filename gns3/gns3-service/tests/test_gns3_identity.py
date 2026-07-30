"""Unit tests for gns3_username_for, GNS3 user names must not collide.

Regression. The name was built as `student-{user_id[:8]}`. Two students sharing
an 8-character id prefix got ONE name, and orphan cleanup during the second
student's provisioning deleted the first student's GNS3 user in the middle of
their session → ACL failed with `FOREIGN KEY constraint failed` and the session
failed with a 500. Students were breaking each other's labs.
"""

from src.gns3_identity import gns3_username_for


class TestGns3UsernameFor:
    def test_distinct_users_with_shared_prefix_get_distinct_names(self):
        """A shared 8-character id prefix no longer yields identical names."""
        a = gns3_username_for("sim-12000-1")
        b = gns3_username_for("sim-12000-2")
        c = gns3_username_for("sim-12000-49")

        assert a != b != c
        assert len({a, b, c}) == 3, "имена должны различаться при общем префиксе"

    def test_is_deterministic(self):
        """Same student → same name (otherwise cleanup of their stray accounts breaks)."""
        assert gns3_username_for("user-abc") == gns3_username_for("user-abc")

    def test_name_is_prefixed_and_bounded(self):
        """The name is recognizable and stays within the GNS3 length limits."""
        name = gns3_username_for("0d1903e5-d38a-41ff-bcfb-03554cddba20")

        assert name.startswith("student-")
        assert len(name) == len("student-") + 16
        assert name[len("student-") :].isalnum()

    def test_uuid_users_do_not_collide(self):
        """Bulk check, 500 different ids → 500 different names."""
        names = {gns3_username_for(f"student-{i}-0d1903e5") for i in range(500)}

        assert len(names) == 500
