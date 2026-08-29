"""Builds a CheckContext from a live GNS3 session. Knows nothing about validation runs."""

from urllib.parse import urlparse

from validation.checks.registry import CheckContext


def _gns3_host_from_settings(settings) -> str:
    """Determine the GNS3 host for outbound connections from settings."""
    gns3 = getattr(settings, "gns3", None)
    if gns3 is not None:
        node_host = getattr(gns3, "node_host", "") or ""
        if node_host:
            return node_host
        for attr in ("internal_url", "public_url"):
            url = getattr(gns3, attr, "") or ""
            if url:
                host = urlparse(url).hostname or ""
                if host and host not in ("gns3-server",):
                    return host
    raise ValueError("cannot derive GNS3 node host from settings")


async def build_check_context(gns3_client, gns3_sid: str, settings) -> CheckContext:
    """GNS3 session state -> CheckContext for running checks."""
    state = await gns3_client.get_state(gns3_sid)
    nodes = state.get("nodes") or []
    nodes_by_name = {n.get("name"): n for n in nodes if n.get("name")}
    return CheckContext(
        gns3_host=_gns3_host_from_settings(settings),
        nodes_by_name=nodes_by_name,
        gns3_project_id=state.get("project_id", ""),
        frr_client=gns3_client,
    )
