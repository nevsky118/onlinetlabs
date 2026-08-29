# GNS3 username that maps unambiguously to one platform session.

import hashlib

_PREFIX = "student-"
_DIGEST_LEN = 16  # 64 bits, collisions are practically excluded


def gns3_username_for(session_id: str) -> str:
    """Unique GNS3 username, hashed from the session id.

    Per session, not per student: two concurrent sessions are allowed, and a
    per-student name meant the second launch's orphan cleanup deleted the GNS3
    user the first session was still using. Deterministic, so a failed launch
    can still clean up after itself.
    """
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:_DIGEST_LEN]
    return f"{_PREFIX}{digest}"
