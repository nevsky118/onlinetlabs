"""Extracting expected values from the lab task's YAML spec.

Loading lives in validation.runner, which caches by mtime; this module used to
re-parse the YAML on the event loop for every chat request.
"""


def expected_vpcs_config(spec: dict | None) -> dict[str, dict]:
    """Extracts expected IP/gateway per VPCS node from the spec: node_name -> {ip, gateway}."""
    result: dict[str, dict] = {}
    if not spec:
        return result
    for step in spec.get("steps", []):
        for check in step.get("checks", []):
            if check.get("kind") == "vpcs.show_ip":
                node = check.get("node")
                if node:
                    expect = check.get("expect", {})
                    result[node] = {"ip": expect.get("ip"), "gateway": expect.get("gateway")}
    return result
