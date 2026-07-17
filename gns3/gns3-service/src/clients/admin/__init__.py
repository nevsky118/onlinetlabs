# Httpx client for the GNS3 v3 admin API, assembled from per-resource mixins.

from ._http import HttpMixin
from .acl import AclMixin
from .projects import ProjectsMixin
from .roles import RolesMixin
from .topology import TopologyMixin
from .users import UsersMixin


class GNS3AdminClient(
    UsersMixin,
    ProjectsMixin,
    TopologyMixin,
    AclMixin,
    RolesMixin,
    HttpMixin,
):
    """GNS3 v3 client. Users, projects, ACL, nodes, and links."""

    def __init__(self, base_url: str, admin_user: str, admin_password: str) -> None:
        self._init_http(base_url, admin_user, admin_password)
        self._builtin_role_cache: dict[str, dict] = {}


__all__ = ["GNS3AdminClient"]
