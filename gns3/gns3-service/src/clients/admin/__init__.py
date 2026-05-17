# Httpx-клиент для GNS3 v3 admin API, собранный из миксинов по ресурсам.

from ._http import HttpMixin
from .acl import AclMixin
from .projects import ProjectsMixin
from .roles import RolesMixin
from .topology import TopologyMixin
from .users import UsersMixin


class GNS3AdminClient(
    UsersMixin, ProjectsMixin, TopologyMixin, AclMixin, RolesMixin, HttpMixin,
):
    """Клиент GNS3 v3. Пользователи, проекты, ACL, узлы и линки."""

    def __init__(self, base_url: str, admin_user: str, admin_password: str) -> None:
        self._init_http(base_url, admin_user, admin_password)
        self._builtin_role_cache: dict[str, dict] = {}


__all__ = ["GNS3AdminClient"]
