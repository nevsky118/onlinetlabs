# GNS3 username that maps unambiguously to a platform student.

import hashlib

_PREFIX = "student-"
_DIGEST_LEN = 16  # 64 bits, collisions are practically excluded


def gns3_username_for(user_id: str) -> str:
    """Unique GNS3 username derived from the student's FULL user_id.

    It used to be `f"student-{user_id[:8]}"`, but an 8-character prefix is NOT unique.
    Two students with a shared prefix got the same name, and "orphan cleanup" during
    the second one's provisioning DELETED the first one's GNS3 user right in the
    middle of their session; their ACL then failed with `FOREIGN KEY constraint failed`,
    and the session with 500. In other words, students broke each other's labs.

    Hash of the full id: the name is deterministic (same student → same name, so
    cleanup of a student's own stray accounts keeps working), but collisions
    between two different students are practically impossible.
    """
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:_DIGEST_LEN]
    return f"{_PREFIX}{digest}"
