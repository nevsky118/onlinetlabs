"""Persist volatile node configuration before nodes are stopped."""

import asyncio
import logging

from validation.checks.vpcs import save_startup_config

logger = logging.getLogger(__name__)

# VPCS keeps addressing in RAM; a stop discards it.
_VOLATILE_NODE_TYPE = "vpcs"
_SAVE_CONCURRENCY = 4


async def persist_volatile_configs(gns3_client, gns3_sid: str, settings) -> int:
    """Saves every started VPCS node's config. Returns how many were saved."""
    from validation.service import build_check_context

    try:
        ctx = await build_check_context(gns3_client, gns3_sid, settings)
    except Exception:
        logger.warning("persist_volatile_configs: no state for %s", gns3_sid, exc_info=True)
        return 0

    targets = [
        (name, node)
        for name, node in ctx.nodes_by_name.items()
        if node.get("nodeType") == _VOLATILE_NODE_TYPE and node.get("status") == "started"
    ]
    if not targets:
        return 0

    semaphore = asyncio.Semaphore(_SAVE_CONCURRENCY)

    async def _save(name: str, node: dict) -> bool:
        port = node.get("console")
        if not port:
            return False
        async with semaphore:
            ok, log = await save_startup_config(ctx.node_console_host(name), int(port))
        if not ok:
            logger.warning("persist_volatile_configs: %s not saved: %s", name, log[-200:])
        return ok

    results = await asyncio.gather(
        *(_save(name, node) for name, node in targets), return_exceptions=True
    )
    return sum(1 for r in results if r is True)
