import pytest


def build_gns3_node(**overrides) -> dict:
    defaults = {
        "node_id": "node-1",
        "name": "R1",
        "node_type": "dynamips",
        "status": "started",
        "console": 5000,
        "console_type": "telnet",
        "console_host": "127.0.0.1",
        "compute_id": "local",
        "ports": [{"name": "f0/0", "port_number": 0, "adapter_number": 0}],
    }
    return defaults | overrides


def build_gns3_link(**overrides) -> dict:
    defaults = {
        "link_id": "link-1",
        "nodes": [
            {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
            {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
        ],
        "link_type": "ethernet",
        "capturing": False,
        "filters": {},
    }
    return defaults | overrides


def build_gns3_version(**overrides) -> dict:
    defaults = {"version": "3.0.0", "local": True}
    return defaults | overrides
