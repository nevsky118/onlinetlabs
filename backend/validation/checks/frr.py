"""FRR check handlers: `frr.ospf_neighbor`, `frr.route_in_table`.

Handlers go through `ctx.frr_client.exec_vtysh(project_id, node_id, command)`
(a thin wrapper over gns3-service `POST /v1/exec/vtysh`).
Parsing lives in the pure functions `_parse_neighbor_state` / `_parse_route`,
so they can be covered by unit tests without network calls.
"""

from __future__ import annotations

import re

from validation.checks.registry import CheckContext, CheckResult

# `Neighbor ID   Pri  State                       Up Time      ...`
# a real line: `2.2.2.2  1 Full/DR             00:01:23     ...`
_NEIGHBOR_LINE_RE = re.compile(r"^\s*(\S+)\s+\d+\s+(\S+)")

# Example route lines:
#   `O>* 192.168.110.0/24 [110/20] via 10.0.0.2, eth1, ...`
#   `O   192.168.110.0/24 [110/20] is directly connected, eth1, ...`
# The code part can be `O`, `O>*`, `O>`, etc.
_ROUTE_LINE_RE = re.compile(r"^\s*([A-Z][A-Z>*]*)\s+(\d+\.\d+\.\d+\.\d+/\d+)\b")


def _parse_neighbor_state(stdout: str, neighbor_id: str) -> str | None:
    """Return the State (e.g. "Full/DR") of the neighbor line with the given Neighbor ID.

    Returns None if the neighbor doesn't exist.
    """
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("Neighbor ID"):
            continue
        m = _NEIGHBOR_LINE_RE.match(line)
        if not m:
            continue
        if m.group(1) == neighbor_id:
            return m.group(2)
    return None


def _parse_route(stdout: str, prefix: str) -> tuple[str, str] | None:
    """Return `(code, full_line)` for the route with the given prefix.

    `code` is the first column (route type), e.g. `O>*`. Returns None
    if no route with that prefix is found.
    """
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        m = _ROUTE_LINE_RE.match(line)
        if not m:
            continue
        if m.group(2) == prefix:
            return m.group(1), line.strip()
    return None


def _missing_param(name: str, expect: dict) -> CheckResult:
    """Build a failed result for a missing parameter."""
    return CheckResult(
        ok=False,
        expected=expect,
        actual={"error": f"param {name!r} missing"},
        log="",
    )


async def _exec_or_error(
    ctx: CheckContext, node_name: str, command: str, expect: dict
) -> tuple[dict | None, CheckResult | None]:
    """Run a command via the node's vtysh.

    Returns (result, None) on success, or (None, failed_result) if the node
    isn't found, the client isn't configured, or the call fails.
    """
    node_id = ctx.node_id(node_name)
    if not node_id:
        return None, CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"node {node_name!r} not found"},
            log="",
        )
    if not ctx.gns3_project_id or ctx.frr_client is None:
        return None, CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "frr_client/project_id not configured in CheckContext"},
            log="",
        )
    try:
        result = await ctx.frr_client.exec_vtysh(ctx.gns3_project_id, node_id, command)
    except Exception as exc:
        return None, CheckResult(
            ok=False,
            expected=expect,
            actual={"error": f"exec_vtysh failed: {exc}"},
            log="",
        )
    return result, None


async def frr_ospf_neighbor(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """`show ip ospf neighbor` -> check the state of a specific neighbor.

    params:  `{node: "R1"}`
    expect:  `{neighbor_id: "2.2.2.2", state: "Full"}`
             State matching is done via `startswith`, so `Full`
             covers `Full/DR`, `Full/BDR`, `Full/DROther`.
    """
    node_name = params.get("node")
    if not node_name:
        return _missing_param("node", expect)
    neighbor_id = expect.get("neighbor_id")
    expected_state = expect.get("state")
    if not neighbor_id or not expected_state:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "expect must contain 'neighbor_id' and 'state'"},
            log="",
        )

    exec_result, err = await _exec_or_error(ctx, node_name, "show ip ospf neighbor", expect)
    if err is not None:
        return err
    stdout = exec_result.get("stdout", "")

    state = _parse_neighbor_state(stdout, neighbor_id)
    actual = {"neighbor_id": neighbor_id, "state": state}
    ok = state is not None and state.startswith(expected_state)
    return CheckResult(ok=ok, expected=expect, actual=actual, log=stdout)


async def frr_route_in_table(ctx: CheckContext, params: dict, expect: dict) -> CheckResult:
    """`show ip route ospf` -> check that a route with the given protocol code exists.

    params:  `{node: "R1"}`
    expect:  `{prefix: "192.168.110.0/24", protocol: "O"}`
             Protocol matching via `startswith` -> `O` covers `O>*`, `O>`.
    """
    node_name = params.get("node")
    if not node_name:
        return _missing_param("node", expect)
    prefix = expect.get("prefix")
    protocol = expect.get("protocol")
    if not prefix or not protocol:
        return CheckResult(
            ok=False,
            expected=expect,
            actual={"error": "expect must contain 'prefix' and 'protocol'"},
            log="",
        )

    exec_result, err = await _exec_or_error(ctx, node_name, "show ip route ospf", expect)
    if err is not None:
        return err
    stdout = exec_result.get("stdout", "")

    parsed = _parse_route(stdout, prefix)
    actual = {
        "prefix": prefix,
        "protocol": parsed[0] if parsed else None,
        "route": parsed[1] if parsed else None,
    }
    ok = parsed is not None and parsed[0].startswith(protocol)
    return CheckResult(ok=ok, expected=expect, actual=actual, log=stdout)
