"""Test data generators for the GNS3 REST payloads the MCP server maps."""


class Gns3NodeData:
    """Generates the JSON structure of a GNS3 API node."""

    def __init__(self, **overrides):
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
        self.data = defaults | overrides


class Gns3LinkData:
    """Generates the JSON structure of a GNS3 API link."""

    def __init__(self, **overrides):
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
        self.data = defaults | overrides


class Gns3VersionData:
    """Generates the JSON structure of the GNS3 version endpoint."""

    def __init__(self, **overrides):
        self.data = {"version": "3.0.0", "local": True} | overrides
