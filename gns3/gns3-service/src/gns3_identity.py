# GNS3 username that maps unambiguously to a platform student.

import hashlib

_PREFIX = "student-"
_DIGEST_LEN = 16  # 64 bits, collisions are practically excluded


def gns3_username_for(user_id: str) -> str:
    """Unique GNS3 username, hashed from the full user_id.

    Must hash the whole id: the old `student-{user_id[:8]}` collided, and orphan
    cleanup then deleted a live student's GNS3 user mid-session, failing their ACL
    with FOREIGN KEY constraint failed. Deterministic, so self-cleanup still works.
    """
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:_DIGEST_LEN]
    return f"{_PREFIX}{digest}"
